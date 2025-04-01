import requests
import csv
import datetime
import os
import shutil

# クライアント名を環境変数から取得（例: CLIENTA）
CLIENT = os.environ['CLIENT']  # 必須！GitHub Actions 側で設定

# 環境変数からアクセストークンとアカウントIDを取得（直接変数名で読む）
ACCESS_TOKEN = os.environ['META_ACCESS_TOKEN']
AD_ACCOUNT_ID = os.environ['META_AD_ACCOUNT_ID']
API_VERSION = 'v19.0'

# 今日の日付を取得（例: 2025-04-02）
today = datetime.datetime.utcnow().strftime("%Y-%m-%d")

# 出力先ディレクトリを作成（存在しなければ）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "meta_csv")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ファイル名：クライアント名＋日付入り
filename_with_date = os.path.join(OUTPUT_DIR, f"{CLIENT.lower()}_meta_report_{today}.csv")
filename_fixed = os.path.join(OUTPUT_DIR, f"{CLIENT.lower()}_meta_report.csv")  # Driveアップロード対象

# Meta広告APIのエンドポイント
url = f"https://graph.facebook.com/{API_VERSION}/{AD_ACCOUNT_ID}/insights"

# APIパラメータ
params = {
    'access_token': ACCESS_TOKEN,
    'level': 'campaign',
    'fields': 'campaign_name,spend,impressions,clicks,cpm,actions',
    'time_range': f'{{"since":"{today}","until":"{today}"}}'
}

# API呼び出し
response = requests.get(url, params=params)
data = response.json()

# エラーチェック
if "error" in data:
    print("❌ Meta API error:", data["error"])
    exit(1)

# CSVに書き出し
with open(filename_with_date, "w", newline='') as csvfile:
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

# 固定ファイル名で保存（Driveアップロード用）
shutil.copyfile(filename_with_date, filename_fixed)

print(f"✅ CSV生成完了：{filename_with_date}")
print(f"✅ Driveアップロード用コピー：{filename_fixed}")
