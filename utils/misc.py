import os

import json
import requests

from google.oauth2 import service_account
from google.auth.transport import requests as google_requests
from firebase_admin import credentials

from utils.logging_utils import log_error

FIREBASE_NOTIFICATIONS_TOKEN = os.getenv("FIREBASE_NOTIFICATIONS_TOKEN")
SCOPES = ['https://www.googleapis.com/auth/firebase.messaging']

def generate_firebase_token():
    keyfile_dict = service_account.Credentials.from_service_account_file(
        'firebase-admin.json',
        scopes=SCOPES
    )

    request = google_requests.Request()
    keyfile_dict.refresh(request)
    return keyfile_dict.token

def send_notification(title, body, token):
    res = None
    try:
        url = os.environ.get('FCM_ENDPOINT')
        fcm_token = generate_firebase_token()


        payload = json.dumps({
            "message": {
                    "token": token,
                    "data": {"itemId": "123"},
                    "notification": {
                    "title": title,
                    "body": body,
                }
            }
        })
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {fcm_token}'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        res = response.json()
    except Exception as e:
        log_error(e)

    return res