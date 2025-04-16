import os
import requests
import csv
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# === 環境変数の読み込み ===
ACCESS_TOKEN = os.getenv('RIAHOUSE_META_ACCESS_TOKEN')
AD_ACCOUNT_ID = os.getenv('RIAHOUSE_META_AD_ACCOUNT_ID')
FOLDER_ID = os.getenv('RIAHOUSE_META_FOLDER_ID')
CSV_PATH = 'meta_csv/latest.csv'

# === Meta広告データ取得 ===
def fetch_meta_ads_data():
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    fields = "campaign_name,ad_name,impressions,clicks,spend"
    date_preset = "today"

    url = f"https://graph.facebook.com/v19.0/act_{AD_ACCOUNT_ID}/insights"
    params = {
        "fields": fields,
        "date_preset": date_preset,
        "level": "ad",
        "limit": 1000
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json().get("data", [])

# === CSV書き出し ===
def write_to_csv(data):
    os.makedirs("meta_csv", exist_ok=True)
    with open(CSV_PATH, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["campaign_name", "ad_name", "impressions", "clicks", "spend"])
        for row in data:
            writer.writerow([
                row.get("campaign_name", ""),
                row.get("ad_name", ""),
                row.get("impressions", ""),
                row.get("clicks", ""),
                row.get("spend", "")
            ])

# === Google Driveへアップロード ===
def upload_to_drive():
    SCOPES = ['https://www.googleapis.com/auth/drive']
    credentials = service_account.Credentials.from_service_account_file(
        'credentials.json', scopes=SCOPES)
    service = build('drive', 'v3', credentials=credentials)

    # 既存ファイルの検索
    results = service.files().list(
        q=f"'{FOLDER_ID}' in parents and name='latest.csv' and trashed=false",
        spaces='drive',
        fields='files(id, name)').execute()
    items = results.get('files', [])

    media = MediaFileUpload(CSV_PATH, mimetype='text/csv', resumable=True)

    if items:
        file_id = items[0]['id']
        service.files().update(fileId=file_id, media_body=media).execute()
        print(f"✔ 既存の latest.csv を更新しました (fileId: {file_id})")
    else:
        file_metadata = {
            'name': 'latest.csv',
            'parents': [FOLDER_ID]
        }
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print("✔ 新規に latest.csv をアップロードしました")

# === メイン処理 ===
def main():
    print("▶ Meta広告データを取得中...")
    data = fetch_meta_ads_data()
    print(f"✔ {len(data)} 件のデータを取得")

    print("▶ CSVとして保存中...")
    write_to_csv(data)
    print(f"✔ {CSV_PATH} に保存完了")

    print("▶ Google Driveにアップロード中...")
    upload_to_drive()
    print("✔ アップロード完了")

if __name__ == "__main__":
    main()
