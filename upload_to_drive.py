from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

CSV_FILE_PATH = "meta_report.csv"
FOLDER_ID = "12WQ6lLMOrk7dTbEb-gZx8ksK9Bv3HzHN"  # あなたのフォルダID（固定）

def upload_to_drive():
    creds = service_account.Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build("drive", "v3", credentials=creds)

    # アップロードするCSVファイルの内容を準備
    media = MediaFileUpload(CSV_FILE_PATH, mimetype="text/csv")

    # フォルダ内の同名ファイル（meta_report.csv）を検索
    query = f"name = '{CSV_FILE_PATH}' and '{FOLDER_ID}' in parents and trashed = false"
    results = service.files().list(q=query, spaces='drive', fields="files(id)").execute()
    items = results.get('files', [])

    if items:
        # ファイルが存在 → 上書き更新
        file_id = items[0]['id']
        updated_file = service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
        print(f"✅ Updated existing file: {file_id}")
    else:
        # ファイルが存在しない → 新規作成
        file_metadata = {
            "name": CSV_FILE_PATH,
            "parents": [FOLDER_ID]
        }
        created_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()
        print(f"✅ Uploaded new file: {created_file.get('id')}")

if __name__ == "__main__":
    upload_to_drive()
