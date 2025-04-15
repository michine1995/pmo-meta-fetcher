import requests
import csv
import datetime
import os
import shutil
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 固定クライアント名
CLIENT = "RIAHOUSE"

# 環境変数から取得
ACCESS_TOKEN = os.environ.get(f"{CLIENT}_META_ACCESS_TOKEN")
AD_ACCOUNT_ID = os.environ.get(f"{CLIENT}_META_AD_ACCOUNT_ID")
FOLDER_ID = os.environ.get(f"{CLIENT}_META_FOLDER_ID")

if not ACCESS_TOKEN:
    raise KeyError(f"❌ 環境変数が不足しています: '{CLIENT}_META_ACCESS_TOKEN'")
if not AD_ACCOUNT_ID:
    raise KeyError(f"❌ 環境変数が不足しています: '{CLIENT}_META_AD_ACCOUNT_ID'")
if not FOLDER_ID:
    raise KeyError(f"❌ 環境変数が不足しています: '{CLIENT}_META_FOLDER_ID'")

API_VERSION = "v19.0"
# 取得対象は前日の日付
yesterday = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

# CSV出力先
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "meta_csv")
os.makedirs(OUTPUT_DIR, exist_ok=True)

filename_with_date = os.path.join(OUTPUT_DIR, f"{CLIENT.lower()}_meta_report_{yesterday}.csv")
filename_fixed = os.path.join(OUTPUT_DIR, f"{CLIENT.lower()}_meta_report.csv")

# Meta API呼び出し
url = f"https://graph.facebook.com/{API_VERSION}/{AD_ACCOUNT_ID}/insights"
params = {
    "access_token": ACCESS_TOKEN,
    "level": "campaign",
    "fields": "campaign_name,spend,impressions,clicks,cpm,actions",
    "time_range": f'{{"since":"{yesterday}","until":"{yesterday}"}}'
}

response = requests.get(url, params=params)
data = response.json()

if "error" in data:
    print("❌ Meta API error:", data["error"])
    exit(1)

# CSVに書き出し
with open(filename_with_date, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["date", "campaign", "cost", "CPM", "CTR", "CPC", "impressions", "link_clicks", "conversions"])

    for entry in data.get("data", []):
        actions = entry.get("actions", [])
        conversions = sum(int(a["value"]) for a in actions if "conversion" in a["action_type"])
        link_clicks = next((int(a["value"]) for a in actions if a["action_type"] == "link_click"), 0)

        spend = float(entry.get("spend", 0))
        impressions = int(entry.get("impressions", 0))

        ctr_link = round((link_clicks / impressions * 100), 2) if impressions else 0
        cpc_link = round((spend / link_clicks), 2) if link_clicks else 0

        writer.writerow([
            yesterday,
            entry.get("campaign_name", "N/A"),
            spend,
            entry.get("cpm", "0"),
            ctr_link,
            cpc_link,
            impressions,
            link_clicks,
            conversions
        ])

# 固定名CSVコピー（リアルタイム用）
shutil.copyfile(filename_with_date, filename_fixed)

print(f"✅ CSV生成完了：{filename_with_date}")
print(f"✅ Driveアップロード用コピー：{filename_fixed}")

# Google Driveにアップロード
creds = service_account.Credentials.from_service_account_file(
    "credentials.json",
    scopes=["https://www.googleapis.com/auth/drive"]
)
service = build("drive", "v3", credentials=creds)
media = MediaFileUpload(filename_with_date, mimetype="text/csv")

query = f"name = '{os.path.basename(filename_with_date)}' and '{FOLDER_ID}' in parents and trashed = false"
results = service.files().list(q=query, spaces="drive", fields="files(id)").execute()
items = results.get("files", [])

if items:
    file_id = items[0]["id"]
    service.files().update(fileId=file_id, media_body=media).execute()
    print(f"✅ Updated existing file on Drive: {file_id}")
else:
    file_metadata = {
        "name": os.path.basename(filename_with_date),
        "parents": [FOLDER_ID]
    }
    created_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()
    print(f"✅ Uploaded new file to Drive: {created_file.get('id')}")
