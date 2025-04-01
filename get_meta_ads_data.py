import requests
import csv
import datetime
import os

# 環境変数からアクセストークンとアカウントIDを取得
ACCESS_TOKEN = os.environ['META_ACCESS_TOKEN']
AD_ACCOUNT_ID = os.environ['META_AD_ACCOUNT_ID']  # 例: act_388170056461500
API_VERSION = 'v19.0'

# 今日の日付を取得（例: 2025-04-02）
today = datetime.datetime.utcnow().strftime("%Y-%m-%d")

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

# CSV出力ファイル名
filename = "meta_report.csv"

# CSVに書き出し
with open(filename, "w", newline='') as csvfile:
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

print(f"✅ CSV生成完了：{filename}")
