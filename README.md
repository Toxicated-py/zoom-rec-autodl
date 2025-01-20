# Zoom Recording Downloader

This Python script allows you to download all Zoom recordings within a specified date range or for the past weeks. It uses the Zoom API to fetch and download recordings in MP4 format.

---

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Logging](#logging)
- [License](#license)
- [Contributing](#contributing)
- [Support](#support)
- [Acknowledgments](#acknowledgments)

---

## Features
- Fetch recordings for a specified date range.
- Download recordings in parallel.
- Automatically refresh JWT token when expired.

---

## Prerequisites

Before using this script, ensure you have the following:

1. **Python 3.x** installed on your system.
2. **Zoom API Credentials**:
   - `CLIENT_ID`
   - `CLIENT_SECRET`
   - `ZOOM_ACCOUNT_ID`
   
   You can obtain these credentials by creating a Zoom OAuth app in the [Zoom App Marketplace](https://marketplace.zoom.us/).

    When creating your Zoom OAuth app, ensure the following scopes are enabled:
   - `cloud_recording:read:list_user_recordings:admin`
   - `cloud_recording:read:list_recording_files:admin`
   - `cloud_recording:read:list_account_recordings:master`
   - `user:read:list_users:admin`

   These scopes are necessary for the script to access and download recordings.

3. **Required Python Libraries**:
   - `requests`
   - `python-dotenv`

   These can be installed using the `requirements.txt` file.

---

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/Toxicated-py/zoom-rec-adl.git
    cd zoom-recording-downloader
    ```

2. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. Create a `.env` file with your Zoom API credentials:
    ```sh
    touch .env
    ```

    Add the following content to the `.env` file:
    ```env
    ZOOM_JWT_TOKEN="your_zoom_jwt_token"
    ZOOM_ACCOUNT_ID="your_zoom_account_id"
    CLIENT_ID="your_client_id"
    CLIENT_SECRET="your_client_secret"
    ```
    Replace `your_client_id`, `your_client_secret`, `your_zoom_account_id` with your actual Zoom API credentials.
    Optionally you can replace `your_jwt_token` too, although it is automatically updated.

---

## Usage

1. Run the script to fetch and download recordings:
    ```sh
    python rec-dl.py
    ```

2. Follow the prompts to specify the date range or the number of past weeks for which you want to download recordings.

---

## Configuration

You can customize the script's behavior by modifying the `config.json` file:

- `page_size`: Number of recordings to fetch per API request (default: `30`).
- `max_pages`: Maximum number of pages to fetch (default: `10`).
- `download_folder`: Folder where recordings will be saved (default: `recordings`).

---

## Logging

The script logs its activities to a file named `zoom_recording_downloader.log`. You can find details about fetched recordings, download progress, and any errors in this file.

---

## License
This project is licensed under the MIT License.

---

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

---

## Support

If you encounter any problems or have questions, feel free to open an issue on GitHub.

---

## Acknowledgments

- Thanks to Zoom for providing the API.
- Thanks to the developers of the requests and python-dotenv libraries.

---