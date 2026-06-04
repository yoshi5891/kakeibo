import base64
import os
import requests
import sys

GITHUB_OWNER = "yoshi5891"
GITHUB_REPO = "kakeibo"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

def upload_to_github(zip_path):

    if not GITHUB_TOKEN:
        print("ERROR: GITHUB_TOKEN is not set")
        return False

    filename = os.path.basename(zip_path)

    with open(zip_path, "rb") as f:
        content = f.read()

    encoded = base64.b64encode(content).decode("utf-8")

    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/backups/{filename}"

    data = {
        "message": f"Backup {filename}",
        "content": encoded
    }

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.put(url, json=data, headers=headers)

    if response.status_code in (200, 201):
        print("Upload success")
        return True
    else:
        print("Upload failed")
        print(response.text)
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python backup_to_github.py <zip_path>")
        sys.exit(1)

    zip_path = sys.argv[1]
    upload_to_github(zip_path)
