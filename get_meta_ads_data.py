import requests
import csv
import datetime
import os

# クライアント一覧（環境変数とCSVファイル名のプレフィックスとして使用）
clients = ["CLIENTA", "CLIENTB"]  # ← 必要に応じて追加

# 日付の設定（今日の日付）
today = datetime.datetime.utcnow().strftime("%Y-%m-%d")

# APIバージョン
API_VERSION = 'v19.0'

for client in clients:
    # 各クライアントの環境変数からトークンとアカウントIDを取得
    access_token = os.environ.get(f"{client}_META_ACCESS_TOKEN")
    ad_account_id = os.environ.get(f"{client}_META_AD_ACCOUNT_ID")

    if not access_token or not ad_account_id:
        print(f"⚠️ {client} の環境変数が不足しています。スキップします。")
        continue

    # Meta広告APIのエンドポイント
    url = f"https://graph.facebook.com/{API_VERSION}/{ad_account_id}/insights"

    # APIパラメータ
    params = {
        'access_token': access_token,
        'level': 'campaign',
        'fields': 'campaign_name,spend,impressions,clicks,cpm,actions',
        'time_range': f'{{"since":"{today}","until":"{today}"}}'
    }

    # API呼び出し
    response = requests.get(url, params=params)
    data = response.json()

    # エラーチェック
    if "error" in data:
        print(f"❌ {client} - Meta API error:", data["error"])
        continue

    # 出力ファイル名をクライアント名ベースに
    filename = f"{client.lower()}_meta_report.csv"

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

    print(f"✅ {client} のCSV生成完了：{filename}")
