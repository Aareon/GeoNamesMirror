# 🌍 GeoNamesMirror

[![Data Update](https://github.com/Aareon/GeoNamesMirror/actions/workflows/update_allCountries.yml/badge.svg)](https://github.com/Aareon/GeoNamesMirror/actions/workflows/update_allCountries.yml)
[![Data License: CC BY 4.0](https://img.shields.io/badge/Data%20License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

Automated mirror of GeoNames geographical database, updated weekly.

## 🎯 Purpose

This repository serves as an automated mirror for the GeoNames `allCountries.zip` dataset. It provides a reliable, versioned source for GeoNames postal code data, updated on a weekly basis.

## 🔄 Update Schedule

The GeoNames data is checked for updates every Sunday at 00:00 UTC. If new data is available, this repository will automatically create a new release with the updated `allCountries.zip` file.

## 📦 Accessing the Data

You can access the latest GeoNames data in two ways:

1. **Latest Release**: Always points to the most recent data.
   - URL: `https://github.com/Aareon/GeoNamesMirror/releases/latest/download/allCountries.zip`

2. **Specific Version**: Access a specific version of the data by its release tag.
   - URL: `https://github.com/Aareon/GeoNamesMirror/releases/download/release-{number}/allCountries.zip`
   - Replace `{number}` with the specific release number you want to access.

## 🛠️ Implementation Details

### update_allCountries.py

This Python script is responsible for:
- Checking if a new version of the GeoNames data is available
- Downloading the new data if an update is found
- Preparing the data for release

Key features:
- Uses `httpx` for asynchronous HTTP requests
- Implements robust error handling and logging
- Verifies data integrity after download

### update_allCountries.yml

This GitHub Actions workflow:
- Runs on a weekly schedule (every Sunday at 00:00 UTC)
- Can also be triggered manually
- Executes the `update_allCountries.py` script
- Creates a new release with the updated data if changes are detected

## 📊 Data Statistics

Each release includes basic statistics about the data:
- Total number of entries
- Number of countries covered
- File size
- MD5 checksum of the zip file

## 📜 License

This project is dual-licensed:

- The code in this repository (including scripts and workflows) is licensed under the [MIT License](https://opensource.org/licenses/MIT).
- The GeoNames data mirrored in this repository is licensed under the [Creative Commons Attribution 4.0 License](https://creativecommons.org/licenses/by/4.0/).

## 🙏 Acknowledgements

This project uses data from [GeoNames](https://www.geonames.org/), which is made available under the Creative Commons Attribution 4.0 License.

## 🚀 Using this Data

This mirrored data is ideal for:
- Applications requiring offline access to GeoNames data
- Projects that need a stable, versioned source of GeoNames data
- Automated pipelines that depend on GeoNames postal code information

To use this data in your project, you can download the latest release or a specific version as needed. Always ensure you comply with the Creative Commons Attribution 4.0 License when using this data.

## 🤝 Contributing

While this repository is primarily automated, we welcome contributions to improve the update script or GitHub Actions workflow. Please feel free to submit issues or pull requests. Note that any contributions to the code will be under the MIT License.

## 📬 Contact

If you have any questions, encounter any issues, or would like to request enhancements, please [create an issue](https://github.com/yourusername/GeoNamesMirror/issues) in this repository. We appreciate your feedback and contributions!

Project Link: [https://github.com/Aareon/GeoNamesMirror](https://github.com/Aareon/GeoNamesMirror)