import requests
import csv
import datetime
import os
import shutil
import sys

# ✅ クライアント名の取得とエラーハンドリング
CLIENT = os.environ.get("CLIENT")
if not CLIENT:
    print("❌ 環境変数 'CLIENT' が設定されていません", file=sys.stderr)
    exit(1)

# ✅ クライアントごとの環境変数を取得
ACCESS_TOKEN = os.environ.get(f"{CLIENT}_META_ACCESS_TOKEN")
AD_ACCOUNT_ID = os.environ.get(f"{CLIENT}_META_AD_ACCOUNT_ID")

if not ACCESS_TOKEN:
    print(f"❌ 環境変数 '{CLIENT}_META_ACCESS_TOKEN' が見つかりません", file=sys.stderr)
    exit(1)
if not AD_ACCOUNT_ID:
    print(f"❌ 環境変数 '{CLIENT}_META_AD_ACCOUNT_ID' が見つかりません", file=sys.stderr)
    exit(1)

# ✅ 基本設定
API_VERSION = "v19.0"
today = datetime.datetime.utcnow().strftime("%Y-%m-%d")

# ✅ 出力パス
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "meta_csv")
os.makedirs(OUTPUT_DIR, exist_ok=True)

filename_with_date = os.path.join(OUTPUT_DIR, f"{CLIENT.lower()}_meta_report_{today}.csv")
filename_fixed = os.path.join(OUTPUT_DIR, f"{CLIENT.lower()}_meta_report.csv")  # Driveアップロード用

# ✅ Meta広告API呼び出し
url = f"https://graph.facebook.com/{API_VERSION}/{AD_ACCOUNT_ID}/insights"
params = {
    "access_token": ACCESS_TOKEN,
    "level": "campaign",
    "fields": "campaign_name,spend,impressions,clicks,cpm,actions",
    "time_range": f'{{"since":"{today}","until":"{today}"}}'
}

response = requests.get(url, params=params)
data = response.json()

# ✅ APIエラーチェック
if "error" in data:
    print("❌ Meta API error:", data["error"], file=sys.stderr)
    exit(1)

# ✅ CSV出力
with open(filename_with_date, "w", newline="", encoding="utf-8") as csvfile:
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
            today,
            entry.get("campaign_name", "N/A"),
            spend,
            entry.get("cpm", "0"),
            ctr_link,
            cpc_link,
            impressions,
            link_clicks,
            conversions
        ])

# ✅ 固定ファイル名へコピー（Drive用）
shutil.copyfile(filename_with_date, filename_fixed)

print(f"✅ CSV生成完了：{filename_with_date}")
print(f"☁️ Driveアップロード用にコピー：{filename_fixed}")
