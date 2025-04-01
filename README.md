# PMo Meta Ads Fetcher

This script automatically fetches ad performance data from the Meta Ads API and exports it to a CSV file.

## Setup

1. Copy `.env.example` to `.env` and fill in your `ACCESS_TOKEN` and `AD_ACCOUNT_ID`.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the script:
   ```
   python meta_ads_to_csv.py
   ```

## Railway Deployment

- This project is pre-configured with `railway.json` to enable scheduled jobs.
- Set the environment variables in Railway dashboard under Variables tab.
