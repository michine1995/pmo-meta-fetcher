from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import datetime

# Google Drive認証
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=credentials)

# 日付付きファイル名の生成
today = datetime.datetime.now().strftime('%Y-%m-%d')
backup_filename = f"ad_data_{today}.csv"
source_filename = "ad_data.csv"  # ← get_meta_ads_data.py で出力されるファイル名と一致させる

# Driveにアップロード
file_metadata = {
    'name': backup_filename,
    'parents': [os.environ['RIAHOUSE_META_FOLDER_ID']]
}
media = MediaFileUpload(source_filename, mimetype='text/csv')

file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
print(f"✅ Uploaded daily backup as {backup_filename}, File ID: {file.get('id')}")
