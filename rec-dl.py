import os
import requests
import logging
import json
import base64
from datetime import datetime, timedelta
import re
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import signal
import sys

# Load environment variables
load_dotenv()

# Configuration
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")
JWT_TOKEN = os.getenv("ZOOM_JWT_TOKEN")
BASE_URL = "https://api.zoom.us/v2"
TOKEN_EXPIRY = None  # Token expiry time

# Load configuration from config.json
try:
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
    PAGE_SIZE = config.get("page_size", 30)
    MAX_PAGES = config.get("max_pages", 10)
    DOWNLOAD_FOLDER = config.get("download_folder", "recordings")
except FileNotFoundError:
    logging.warning("config.json not found. Using default settings.")
    PAGE_SIZE = 30
    MAX_PAGES = 10
    DOWNLOAD_FOLDER = "recordings"

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def is_token_valid():
    """Check if the token is still valid."""
    global TOKEN_EXPIRY
    if TOKEN_EXPIRY is None or datetime.now() >= TOKEN_EXPIRY:
        return False
    return True

def update_env_file(token):
    """Update the .env file with the new JWT token."""
    with open('.env', 'r') as file:
        lines = file.readlines()
    with open('.env', 'w') as file:
        for line in lines:
            if line.startswith('ZOOM_JWT_TOKEN='):
                file.write(f'ZOOM_JWT_TOKEN="{token}"\n')
            else:
                file.write(line)

def refresh_token():
    """Refresh the JWT token using client credentials."""
    global TOKEN_EXPIRY
    try:
        url = "https://zoom.us/oauth/token"
        auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_header}"
        }
        data = {
            "grant_type": "account_credentials",
            "account_id": ACCOUNT_ID
        }
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()
        TOKEN_EXPIRY = datetime.now() + timedelta(seconds=token_data.get("expires_in", 3600))  # Default to 1 hour
        new_token = token_data.get("access_token")
        update_env_file(new_token)
        return new_token
    except Exception as e:
        logging.error(f"Failed to refresh access token: {e}")
        return None

def fetch_recordings(start_date, end_date):
    """Fetch recordings from Zoom API."""
    global JWT_TOKEN
    all_meetings = []
    next_page_token = None
    page_count = 0

    while page_count < MAX_PAGES:
        if not is_token_valid():
            JWT_TOKEN = refresh_token()
            if not JWT_TOKEN:
                logging.error("Unable to refresh JWT token. Exiting.")
                return []

        url = f"{BASE_URL}/users/me/recordings"
        headers = {
            "Authorization": f"Bearer {JWT_TOKEN}"
        }
        params = {
            "page_size": PAGE_SIZE,
            "from": start_date,
            "to": end_date
        }
        if next_page_token:
            params["next_page_token"] = next_page_token

        try:
            logging.info(f"Fetching recordings with URL: {url} and params: {params}")
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            meetings = data.get("meetings", [])
            all_meetings.extend(meetings)
            next_page_token = data.get("next_page_token")
            page_count += 1

            logging.info(f"Fetched {len(meetings)} recordings on page {page_count}. Next page token: {next_page_token}")

            if not next_page_token:
                break

        except requests.RequestException as e:
            logging.error(f"Error fetching recordings: {e}")
            if response:
                logging.error(f"Response status code: {response.status_code}")
                logging.error(f"Response content: {response.content}")
            break

    logging.info(f"Total fetched recordings: {len(all_meetings)}")
    return all_meetings

def download_recording(download_url, file_name):
    """Download a recording file."""
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)
    path = os.path.join(DOWNLOAD_FOLDER, file_name)
    try:
        response = requests.get(download_url, headers={
            "Authorization": f"Bearer {JWT_TOKEN}"
        })
        response.raise_for_status()
        with open(path, "wb") as f:
            f.write(response.content)
        logging.info(f"Downloaded {file_name} to {DOWNLOAD_FOLDER}")
    except requests.RequestException as e:
        logging.error(f"Error downloading {file_name}: {e}")

def download_all_recordings(meetings):
    """Download all recordings in parallel."""
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for meeting in meetings:
            recording_files = meeting.get('recording_files', [])
            for rec_file in recording_files:
                if rec_file.get('file_type') == 'MP4':
                    file_name = generate_file_name(meeting)
                    download_url = rec_file.get('download_url')
                    if download_url:
                        download_url = f"{download_url}?access_token={JWT_TOKEN}"
                        futures.append(executor.submit(download_recording, download_url, file_name))
        for future in futures:
            future.result()

def generate_file_name(meeting):
    """Generate a file name for the recording."""
    topic = meeting.get('topic', 'meeting')
    start_time = meeting.get('start_time', 'unknown')
    try:
        dt = datetime.fromisoformat(start_time.rstrip("Z"))
        date_str = dt.strftime("%Y-%m-%d")
        safe_topic = re.sub(r'[^\w\-_\. ]', ' ', topic)
        first_word = safe_topic.split()[0].rstrip(":")
        file_name = f"{first_word}--{date_str}.mp4"
    except ValueError as e:
        logging.error(f"Error parsing date {start_time}: {e}")
        file_name = f"{meeting['id']}.mp4"
    return file_name

def get_date_input(prompt):
    """Get a valid date input from the user."""
    while True:
        date_input = input(prompt).strip()
        try:
            datetime.strptime(date_input, "%Y-%m-%d")
            return date_input
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")

def get_week_input():
    """Get the number of past weeks from the user."""
    while True:
        weeks_input = input("Enter the number of past weeks: ").strip()
        try:
            weeks = int(weeks_input)
            if weeks > 0:
                return weeks
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def signal_handler(sig, frame):
    """Handle interrupt signals gracefully."""
    logging.info("Shutting down gracefully...")
    sys.exit(0)

def main():
    """Main function to fetch and download recordings."""
    global JWT_TOKEN
    if not all([CLIENT_ID, CLIENT_SECRET, ACCOUNT_ID, JWT_TOKEN]):
        logging.error("Missing credentials. Please check your .env file.")
        return

    signal.signal(signal.SIGINT, signal_handler)  # Add signal handling
    signal.signal(signal.SIGTERM, signal_handler)  # Add signal handling

    print("Welcome to the Zoom Recording Downloader!")
    print("Please choose an option for downloading recordings:")
    print("1. Download recordings for the past weeks")
    print("2. Download recordings by specifying start and end dates")

    choice = input("Enter your choice (1 or 2): ").strip()

    if choice == "1":
        weeks = get_week_input()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=weeks*7)
        start_date = start_date.strftime("%Y-%m-%d")
        end_date = end_date.strftime("%Y-%m-%d")
    elif choice == "2":
        start_date = get_date_input("Enter the start date (YYYY-MM-DD): ")
        end_date = get_date_input("Enter the end date (YYYY-MM-DD): ")
    else:
        print("Invalid choice. Exiting.")
        return

    print(f"\nFetching recordings from {start_date} to {end_date}...")
    meetings = fetch_recordings(start_date, end_date)

    if meetings:
        print(f"\nFound {len(meetings)} recordings.")
        download_all_recordings(meetings)
        print("\nDownload complete! Recordings are saved in the 'recordings' folder.")
    else:
        print("\nNo recordings found for the specified date range.")

if __name__ == "__main__":
    main()