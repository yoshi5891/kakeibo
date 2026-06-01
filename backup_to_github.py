import os
import base64
import requests
from datetime import datetime

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = "yoshi5891/kakeibo"
FILE_PATH = "/tmp/backup.json"

def upload_to_github():
    if not GITHUB_TOKEN:
        print("GITHUB_TOKEN が設定されていません")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    github_file_path = f"backups/backup-{today}.json"  # ← ここが重要！

    with open(FILE_PATH, "rb") as f:
        content = f.read()

    encoded = base64.b64encode(content).decode()

    url = f"https://api.github.com/repos/{REPO}/contents/{github_file_path}"

    data = {
        "message": f"Backup on {today}",
        "content": encoded,
    }

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    response = requests.put(url, json=data, headers=headers)

    print("GitHub Response:", response.status_code, response.text)

if __name__ == "__main__":
    upload_to_github()
