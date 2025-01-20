import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
ACCOUNT_ID = os.getenv('ZOOM_ACCOUNT_ID')

def generate_access_token(client_id, client_secret, account_id):
    command = [
        'curl', '-X', 'POST', 'https://zoom.us/oauth/token',
        '-u', f'{client_id}:{client_secret}',
        '-d', f'grant_type=account_credentials&account_id={account_id}'
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout, stderr=result.stderr)
    return result.stdout

if __name__ == "__main__":
    try:
        access_token_response = generate_access_token(CLIENT_ID, CLIENT_SECRET, ACCOUNT_ID)
        print(f"Access Token Response: {access_token_response}")
    except Exception as e:
        print(f"Failed to generate access token: {e}")