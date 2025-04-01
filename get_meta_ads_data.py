import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

# 環境変数からCLIENTとFOLDER_IDを取得
CLIENT = os.environ.get('CLIENT')
FOLDER_ID = os.environ.get(f'{CLIENT}_META_FOLDER_ID')

if not CLIENT:
    raise Exception("❌ CLIENT 環境変数が未設定です")
if not FOLDER_ID:
    raise Exception(f"❌ 環境変数が未設定です: {CLIENT}_META_FOLDER_ID")

# ファイルパスを動的に構築
CSV_FILE_PATH = os.path.join("meta_csv", f"{CLIENT.lower()}_meta_report.csv")

# Google API認証
creds = service_account.Credentials.from_service_account_file(
    'credentials.json',
    scopes=['https://www.googleapis.com/auth/drive.file']
)

service = build('drive', 'v3', credentials=creds)

file_metadata = {
    'name': f"{CLIENT.lower()}_meta_report.csv",
    'parents': [FOLDER_ID]
}
media = MediaFileUpload(CSV_FILE_PATH, mimetype='text/csv')

file = service.files().create(
    body=file_metadata,
    media_body=media,
    fields='id'
).execute()

print(f"✅ アップロード完了: {file.get('id')}")
