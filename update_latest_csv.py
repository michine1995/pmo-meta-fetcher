import requests
import csv
import datetime
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 当日日付
today = datetime.datetime.utcnow().date()
date_str = today.strftime("%Y-%m-%d")

CLIENT = "RIAHOUSE"
ACCESS_TOKEN = os.environ.get(f"{CLIENT}_META_ACCESS_TOKEN")
AD_ACCOUNT_ID = os.environ.get(f"{CLIENT}_META_AD_ACCOUNT_ID")
FOLDER_ID = os.environ.get(f"{CLIENT}_META_FOLDER_ID")

if not ACCESS_TOKEN or not AD_ACCOUNT_ID or not FOLDER_ID:
    raise KeyError("❌ 環境変数が不足しています")

# 出力フォルダとファイル名
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "meta_csv")
os.makedirs(OUTPUT_DIR, exist_ok=True)

filename_fixed = os.path.join(OUTPUT_DIR, f"{CLIENT.lower()}_meta_report.csv")

# Meta APIから今日のデータを取得
url = f"https://graph.facebook.com/v19.0/{AD_ACCOUNT_ID}/insights"
params = {
    "access_token": ACCESS_TOKEN,
    "level": "campaign",
    "fields": "campaign_name,spend,impressions,clicks,cpm,actions",
    "date_preset": "today"
}

res = requests.get(url, params=params)
data = res.json()

if "error" in data:
    print("❌ Meta API error:", data["error"])
    exit(1)

# CSV書き出し（今日の分）
with open(filename_fixed, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["date", "campaign", "cost", "CPM", "CTR", "CPC", "impressions", "link_clicks", "conversions"])

    for entry in data.get("data", []):
        actions = entry.get("actions", [])
        conversions = sum(int(a["value"]) for a in actions if "conversion" in a["action_type"])
        link_clicks = next((int(a["value"]) for a in actions if a["action_type"] == "link_click"), 0)
        spend = float(entry.get("spend", 0))
        impressions = int(entry.get("impressions", 0))
        ctr = round((link_clicks / impressions * 100), 2) if impressions else 0
        cpc = round((spend / link_clicks), 2) if link_clicks else 0

        writer.writerow([
            date_str,
            entry.get("campaign_name", "N/A"),
            spend,
            entry.get("cpm", "0"),
            ctr,
            cpc,
            impressions,
            link_clicks,
            conversions
        ])

# Google Driveへアップロード（固定名）
def upload_to_drive(filepath):
    creds = service_account.Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build("drive", "v3", credentials=creds)

    media = MediaFileUpload(filepath, mimetype="text/csv")

    # すでにファイルがある場合は更新
    query = f"name = '{os.path.basename(filepath)}' and '{FOLDER_ID}' in parents and trashed = false"
    results = service.files().list(q=query, spaces="drive", fields="files(id)").execute()
    items = results.get("files", [])

    if items:
        file_id = items[0]["id"]
        service.files().update(fileId=file_id, media_body=media).execute()
        print(f"✅ Updated existing file: {file_id}")
    else:
        file_metadata = {
            "name": os.path.basename(filepath),
            "parents": [FOLDER_ID]
        }
        created_file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        print(f"✅ Uploaded new file: {created_file.get('id')}")

upload_to_drive(filename_fixed)
