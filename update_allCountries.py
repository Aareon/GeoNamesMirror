import asyncio
import csv
import hashlib
import zipfile
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx
from loguru import logger

GEONAMES_URL = "https://download.geonames.org/export/zip/allCountries.zip"
LOCAL_FILE = Path("allCountries.zip")
EXTRACTED_FILE = Path("allCountries.txt")
GITHUB_API_URL = "https://api.github.com/repos/Aareon/GeoNamesMirror/releases/latest"

async def check_for_updates() -> bool:
    if LOCAL_FILE.exists():
        local_time = datetime.fromtimestamp(LOCAL_FILE.stat().st_mtime, tz=timezone.utc)

        async with httpx.AsyncClient() as client:
            response = await client.head(GEONAMES_URL)
        response.raise_for_status()

        remote_time = datetime.strptime(
            response.headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S GMT"
        ).replace(tzinfo=timezone.utc)

        return remote_time > local_time
    return True

async def download_file():
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", GEONAMES_URL) as response:
            response.raise_for_status()
            total_size = int(response.headers.get("Content-Length", 0))

            with LOCAL_FILE.open("wb") as f:
                downloaded = 0
                async for chunk in response.aiter_bytes():
                    f.write(chunk)
                    downloaded += len(chunk)
                    logger.info(f"Downloaded {downloaded}/{total_size} bytes")

def calculate_md5(filename: Path) -> str:
    hash_md5 = hashlib.md5()
    with filename.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def extract_zip():
    with zipfile.ZipFile(LOCAL_FILE, "r") as zip_ref:
        zip_ref.extractall()

def get_statistics():
    total_entries = 0
    countries = set()

    with EXTRACTED_FILE.open("r", encoding="utf-8") as f:
        csv_reader = csv.reader(f, delimiter="\t")
        for row in csv_reader:
            total_entries += 1
            countries.add(row[0])  # The country code is the first column

    file_size = LOCAL_FILE.stat().st_size
    md5_checksum = calculate_md5(LOCAL_FILE)

    return {
        "total_entries": total_entries,
        "country_count": len(countries),
        "file_size": file_size,
        "md5_checksum": md5_checksum,
    }

def format_file_size(size_bytes):
    size_mb = size_bytes / (1024 * 1024)
    return f"{size_mb:.2f} MB"

def create_release_notes(stats, is_update):
    update_status = "Update" if is_update else "No changes"
    current_date = datetime.now().strftime("%Y-%m-%d")
    return f"""GeoNames Database {update_status} - {current_date}

- Total Entries: {stats['total_entries']:,}
- Countries Covered: {stats['country_count']}
- File Size: {format_file_size(stats['file_size'])}
- MD5 Checksum: {stats['md5_checksum']}

This release contains the latest GeoNames database {update_status.lower()}.
"""

async def get_previous_checksum():
    async with httpx.AsyncClient() as client:
        response = await client.get(GITHUB_API_URL)
        response.raise_for_status()
        release_data = response.json()
        body = release_data.get('body', '')
        
        # Extract MD5 checksum from the release notes
        match = re.search(r'MD5 Checksum: ([a-fA-F0-9]{32})', body)
        if match:
            return match.group(1)
    return None

async def main():
    try:
        if await check_for_updates():
            logger.info("Updating Geonames data...")
            await download_file()
            extract_zip()
            stats = get_statistics()
            
            previous_checksum = await get_previous_checksum()
            current_checksum = stats['md5_checksum']
            
            is_update = previous_checksum != current_checksum
            release_notes = create_release_notes(stats, is_update)

            if is_update:
                logger.info("New data detected. Creating release.")
            else:
                logger.info("No changes in data. Skipping release creation.")

            # Write release notes and update status to files for GitHub Actions to use
            with open("release_notes.txt", "w") as f:
                f.write(release_notes)
            
            with open("update_status.txt", "w") as f:
                f.write("update" if is_update else "no_update")
            
            # Write release title to a separate file
            with open("release_title.txt", "w") as f:
                f.write(release_notes.split('\n')[0])

            logger.info(f"Process complete. Release notes:\n{release_notes}")
        else:
            logger.info("Geonames data is up to date.")
    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
    except IOError as e:
        logger.error(f"I/O error occurred: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())