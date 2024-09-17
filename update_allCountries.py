import asyncio
import csv
import hashlib
import zipfile
import re
from datetime import datetime, timezone
from pathlib import Path
import time

from tqdm import tqdm
import httpx
from loguru import logger

GEONAMES_URL = "https://download.geonames.org/export/zip/allCountries.zip"
LOCAL_FILE = Path("allCountries.zip")
EXTRACTED_FILE = Path("allCountries.txt")
GITHUB_API_URL = "https://api.github.com/repos/Aareon/GeoNamesMirror/releases"


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
            
            chunk_size = 1024 * 1024  # 1 MB chunks
            downloaded = 0
            start_time = time.time()
            last_log_time = start_time
            log_interval = 5  # Log every 5 seconds
            
            with open(LOCAL_FILE, "wb") as f, tqdm(
                total=total_size, unit='iB', unit_scale=True, desc="Downloading"
            ) as progress_bar:
                async for chunk in response.aiter_bytes(chunk_size):
                    size = f.write(chunk)
                    downloaded += size
                    progress_bar.update(size)
                    
                    current_time = time.time()
                    if current_time - last_log_time >= log_interval:
                        elapsed_time = current_time - start_time
                        speed = downloaded / elapsed_time / 1024 / 1024  # MB/s
                        percent = (downloaded / total_size) * 100 if total_size > 0 else 0
                        logger.info(f"Downloaded: {downloaded/1024/1024:.2f} MB / {total_size/1024/1024:.2f} MB "
                                    f"({percent:.2f}%) - Speed: {speed:.2f} MB/s")
                        last_log_time = current_time

            logger.info(f"Download completed. Total size: {total_size/1024/1024:.2f} MB")

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
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(GITHUB_API_URL, headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            })
            response.raise_for_status()
            releases = response.json()
            
            if not releases:
                logger.info("No previous releases found. This will be the first release.")
                return None
            
            latest_release = releases[0]
            body = latest_release.get('body', '')
            
            # Extract MD5 checksum from the release notes
            match = re.search(r'MD5 Checksum: ([a-fA-F0-9]{32})', body)
            if match:
                return match.group(1)
            else:
                logger.warning("MD5 checksum not found in the latest release notes.")
                return None
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching previous releases: {e}")
    return None

async def main():
    current_checksum = None
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
            logger.info(f"Geonames data is up to date.{' Checksum: ' + current_checksum + '.' if current_checksum else ''} Last modified: {datetime.fromtimestamp(LOCAL_FILE.stat().st_mtime)}")
    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
    except IOError as e:
        logger.error(f"I/O error occurred: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())