from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

# クライアント名を取得
CLIENT = os.environ.get('CLIENT')
if not CLIENT:
    raise KeyError("❌ CLIENT環境変数が設定されていません")

# 動的なCSVパスとDriveフォルダIDを構築
CSV_FILE_PATH = f"meta_csv/{CLIENT.lower()}_meta_report.csv"
FOLDER_ID = os.environ.get(f"{CLIENT}_META_FOLDER_ID")
if not FOLDER_ID:
    raise KeyError(f"❌ 環境変数が不足しています: '{CLIENT}_META_FOLDER_ID'")

def upload_to_drive():
    creds = service_account.Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build("drive", "v3", credentials=creds)

    # アップロードするCSVファイル
    media = MediaFileUpload(CSV_FILE_PATH, mimetype="text/csv")

    # 同名ファイルがすでに存在していれば上書き
    query = f"name = '{os.path.basename(CSV_FILE_PATH)}' and '{FOLDER_ID}' in parents and trashed = false"
    results = service.files().list(q=query, spaces='drive', fields="files(id)").execute()
    items = results.get('files', [])

    if items:
        file_id = items[0]['id']
        updated_file = service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
        print(f"✅ Updated existing file: {file_id}")
    else:
        file_metadata = {
            "name": os.path.basename(CSV_FILE_PATH),
            "parents": [FOLDER_ID]
        }
        created_file = service.files().create(
            body=file
