from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import datetime
import shutil

# 📌 Google Drive API 認証設定
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=credentials)

# 📌 リアルタイムのファイル名と、日付付きバックアップファイル名を定義
original_file = "riahouse_meta_report.csv"
today = datetime.datetime.now().strftime("%Y-%m-%d")
backup_file = f"riahouse_meta_report_{today}.csv"

# 📌 バックアップ用にローカルで日付付きファイルを作成
shutil.copyfile(original_file, backup_file)

# 📌 Google Drive にアップロード（バックアップ保存）
file_metadata = {
    'name': backup_file,
    'parents': [os.environ['RIAHOUSE_META_FOLDER_ID']]  # ← 既に使ってるフォルダIDと同じでOK
}
media = MediaFileUpload(backup_file, mimetype='text/csv')
file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

print(f"✅ 日次バックアップファイルをアップロードしました: {backup_file}")
