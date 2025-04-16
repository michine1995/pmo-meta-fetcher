import requests
import csv
import datetime
import os
import shutil
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 前日の日付を取得（UTC基準）
yesterday = datetime.datetime.utcnow() - datetime.timedelta(days=1)
date_str = yesterday.strftime("%Y-%m-%d")

CLIENT = "RIAHOUSE"
ACCESS_TOKEN = os.environ.get(f"{CLIENT}_META_ACCESS_TOKEN")
AD_ACCOUNT_ID = os.environ.get(f"{CLIENT}_META_AD_ACCOUNT_ID")
FOLDER_ID = os.environ.get(f"{CLIENT}_META_FOLDER_ID")

if not ACCESS_TOKEN or not AD_ACCOUNT_ID or not FOLDER_ID:
    raise KeyError("❌ 環境変数が不足しています")

# 出力フォルダ
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "meta_csv")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ファイル名
filename_with_date = os.path.join(OUTPUT_DIR, f"{CLIENT.lower()}_meta_report_{date_str}.csv")
filename_fixed = os.path.join(OUTPUT_DIR, f"{CLIENT.lower()}_meta_report.csv")

# Meta API取得
url = f"https://graph.facebook.com/v19.0/{AD_ACCOUNT_ID}/insights"
params = {
    "access_token": ACCESS_TOKEN,
    "level": "campaign",
    "fields": "campaign_name,spend,impressions,clicks,cpm,actions",
    "time_range": f'{{"since":"{date_str}","until":"{date_str}"}}'
}
res = requests.get(url, params=params)
data = res.json()

if "error" in data:
    print("❌ Meta API error:", data["error"])
    exit(1)

# CSV書き出し
with open(filename_with_date, "w", newline="") as csvfile:
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

# 最新ファイル（固定名）としてコピー
shutil.copyfile(filename_with_date, filename_fixed)

# Google Drive アップロード
def upload_to_drive(filepath):
    creds = service_account.Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build("drive", "v3", credentials=creds)

    media = MediaFileUpload(filepath, mimetype="text/csv")
    file_metadata = {
        "name": os.path.basename(filepath),
        "parents": [FOLDER_ID]
    }
    service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    print(f"✅ アップロード成功：{filepath}")

upload_to_drive(filename_with_date)
