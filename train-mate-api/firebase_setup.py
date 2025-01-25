import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

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

cred = credentials.Certificate(firebase_creds_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()