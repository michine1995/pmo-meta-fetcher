from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import datetime

CLIENT = "riahouse"
today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
CSV_FILE_PATH = f"meta_csv/{CLIENT}_meta_report_{today}.csv"
FOLDER_ID = os.environ.get(f"{CLIENT.upper()}_META_FOLDER_ID")

if not FOLDER_ID:
    raise KeyError(f"❌ 環境変数が不足しています: '{CLIENT.upper()}_META_FOLDER_ID'")

def upload_to_drive():
    creds = service_account.Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build("drive", "v3", credentials=creds)
    media = MediaFileUpload(CSV_FILE_PATH, mimetype="text/csv")

    file_metadata = {
        "name": os.path.basename(CSV_FILE_PATH),
        "parents": [FOLDER_ID]
    }
    created_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()
    print(f"✅ Uploaded new daily backup: {created_file.get('id')}")

if __name__ == "__main__":
    upload_to_drive()
