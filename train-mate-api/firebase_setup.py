import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from google.oauth2 import service_account
from google.cloud import storage

# For local dev, read from a file if it exists (ignored by git).
if os.path.exists("trainmate-pro-firebase-adminsdk-lqht8-9ca5f4a3a9.json"):
    with open("trainmate-pro-firebase-adminsdk-lqht8-9ca5f4a3a9.json") as f:
        firebase_creds_dict = json.load(f)
else:
    # Fallback: read from environment variable
    firebase_creds_json = os.getenv("FIREBASE_CREDENTIALS")
    if not firebase_creds_json:
        raise Exception("No local file and no FIREBASE_CREDENTIALS environment var set")
    firebase_creds_dict = json.loads(firebase_creds_json)

# Initialize Firebase Admin SDK
cred = credentials.Certificate(firebase_creds_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()
# Initialize for storage
credentials = service_account.Credentials.from_service_account_info(firebase_creds_dict)
storage_client = storage.Client(credentials=credentials, project=credentials.project_id)