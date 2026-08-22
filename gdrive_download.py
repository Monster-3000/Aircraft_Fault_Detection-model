import requests
import re
import sys
import urllib3

urllib3.disable_warnings()

def download_file_from_google_drive(id, destination):
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()

    response = session.get(URL, params={'id': id}, stream=True, verify=False)
    token = get_confirm_token(response)

    if token:
        params = {'id': id, 'confirm': token}
        response = session.get(URL, params=params, stream=True, verify=False)

    save_response_content(response, destination)    

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

def save_response_content(response, destination):
    CHUNK_SIZE = 32768
    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python gdrive_download.py <file_id> <destination>")
    else:
        file_id = sys.argv[1]
        destination = sys.argv[2]
        download_file_from_google_drive(file_id, destination)
        print(f"Downloaded {file_id} to {destination}")
