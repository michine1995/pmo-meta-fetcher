from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

CSV_FILE_PATH = "meta_report.csv"
FOLDER_ID = "12WQ6lLMOrk7dTbEb"  # ← ここをあなたのフォルダIDに固定済み

def upload_to_drive():
    creds = service_account.Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/drive.file"]
    )
    service = build("drive", "v3", credentials=creds)

    file_metadata = {
        "name": CSV_FILE_PATH,
        "parents": [FOLDER_ID]
    }
    media = MediaFileUpload(CSV_FILE_PATH, mimetype="text/csv")
    file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    print(f"✅ Uploaded: {file.get('id')}")

if __name__ == "__main__":
    upload_to_drive()
