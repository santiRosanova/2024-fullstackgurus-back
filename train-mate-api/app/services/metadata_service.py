from firebase_setup import db
from datetime import datetime
import pytz

def set_last_modified_timestamp(uid, collection):
    try:
        user_ref = db.collection('metadata').document(uid)
        user_doc = user_ref.get()

        # Si el documento no existe, lo creamos
        if not user_doc.exists:
            user_ref.set({})

        collection_name = collection + '_last_modified'

        local_tz = pytz.timezone('America/Argentina/Buenos_Aires')
        local_time = datetime.now(local_tz)

        user_ref.set({
            collection_name: local_time
        }, merge=True)
    
        return local_time
    
    except Exception as e:
        print(f"Error setting last modified timestamp: {e}")
        return False
    
def get_last_modified_timestamp(uid, collection):
    try:
        user_ref = db.collection('metadata').document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return None

        collection_name = collection + '_last_modified'
        last_modified = user_doc.get(collection_name)
        return last_modified

    except Exception as e:
        print(f"Error getting last modified timestamp: {e}")
        return None