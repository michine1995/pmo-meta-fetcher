# upload_daily_backup.py
import shutil
import datetime
import os

# 今日の日付
# 前日を取得（UTC基準で処理）
today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)
yesterday_str = yesterday.isoformat()

# ファイルパス
CLIENT = "RIAHOUSE"
base_name = f"{CLIENT.lower()}_meta_report.csv"

original_file = os.path.join("meta_csv", base_name)
backup_file = os.path.join("meta_csv", f"{CLIENT.lower()}_meta_report_{yesterday_str}.csv")

# コピー実行
shutil.copyfile(original_file, backup_file)
print(f"✅ バックアップコピー作成：{backup_file}")

# upload_to_drive.py
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import datetime

CLIENT = "riahouse"
yesterday = datetime.date.today() - datetime.timedelta(days=1)
CSV_FILE_PATH = f"meta_csv/{CLIENT}_meta_report_{yesterday.isoformat()}.csv"
FOLDER_ID = os.environ.get(f"{CLIENT.upper()}_META_FOLDER_ID")

if not FOLDER_ID:
    raise KeyError(f"❌ 環境変数が不足しています: '{CLIENT.upper()}_META_FOLDER_ID'")

def upload_to_drive():
    creds = service_account.Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build("drive", "v3", credentials=creds)

    media = MediaFileUpload(CSV_FILE_PATH, mimetype="text/csv")

    query = f"name = '{os.path.basename(CSV_FILE_PATH)}' and '{FOLDER_ID}' in parents and trashed = false"
    results = service.files().list(q=query, spaces="drive", fields="files(id)").execute()
    items = results.get("files", [])

    if items:
        file_id = items[0]["id"]
        service.files().update(fileId=file_id, media_body=media).execute()
        print(f"✅ Updated existing file: {file_id}")
    else:
        file_metadata = {
            "name": os.path.basename(CSV_FILE_PATH),
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

# .github/workflows/meta_ads_to_drive.yml
name: メタ広告を取得しGoogle Driveへ保存

on:
  schedule:
    - cron: '0 15 * * *'  # JST 00:00（前日分バックアップ）
  workflow_dispatch:

jobs:
  run-meta:
    runs-on: ubuntu-latest
    env:
      CLIENT: RIAHOUSE
    steps:
      - uses: actions/checkout@v3

      - name: 🐍 Pythonセットアップ
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'

      - name: 🔧 ライブラリインストール
        run: |
          pip install requests google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib

      - name: 🔐 Google認証情報のデコード
        run: echo "$GDRIVE_CREDENTIALS_JSON" | base64 --decode > credentials.json
        env:
          GDRIVE_CREDENTIALS_JSON: ${{ secrets.GDRIVE_CREDENTIALS_JSON }}

      - name: 📁 前日分バックアップファイルを作成
        run: python upload_daily_backup.py
        env:
          RIAHOUSE_META_ACCESS_TOKEN: ${{ secrets.RIAHOUSE_META_ACCESS_TOKEN }}
          RIAHOUSE_META_AD_ACCOUNT_ID: ${{ secrets.RIAHOUSE_META_AD_ACCOUNT_ID }}

      - name: ☁️ Google Driveにアップロード（前日分）
        run: python upload_to_drive.py
        env:
          RIAHOUSE_META_FOLDER_ID: ${{ secrets.RIAHOUSE_META_FOLDER_ID }}
