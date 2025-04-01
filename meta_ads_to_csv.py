import requests
import csv
from datetime import datetime, timedelta
import os

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
AD_ACCOUNT_ID = os.getenv("AD_ACCOUNT_ID")
API_VERSION = "v18.0"
FIELDS = [
    "date_start",
    "campaign_name",
    "impressions",
    "clicks",
    "spend",
    "actions"
]

end_date = datetime.today().date()
start_date = end_date - timedelta(days=7)

url = f"https://graph.facebook.com/{API_VERSION}/act_{AD_ACCOUNT_ID}/insights"
params = {
    "access_token": ACCESS_TOKEN,
    "level": "campaign",
    "fields": ",".join(FIELDS),
    "time_range": {
        "since": str(start_date),
        "until": str(end_date)
    },
    "limit": 100
}

response = requests.get(url, params=params)
data = response.json()

filename = f"meta_ads_report_{start_date}_to_{end_date}.csv"
with open(filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["Date", "Campaign Name", "Impressions", "Clicks", "Spend", "Purchases"])

    for row in data.get("data", []):
        purchases = 0
        if "actions" in row:
            for action in row["actions"]:
                if action["action_type"] == "purchase":
                    purchases = action["value"]

        writer.writerow([
            start_date,
            row.get("campaign_name", "-"),
            row.get("impressions", 0),
            row.get("clicks", 0),
            row.get("spend", 0),
            purchases
        ])

print(f"✅ Meta広告レポートを {filename} に保存しました")
