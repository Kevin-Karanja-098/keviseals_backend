import os
import firebase_admin

from django.conf import settings
from firebase_admin import credentials

firebase_app = None
service_account = settings.BASE_DIR / "firebase" / "serviceAccountKey.json"


def initialize_firebase():

    global firebase_app

    if firebase_app:
        return firebase_app

    service_account = os.path.join(
        settings.BASE_DIR,
        "firebase",
        "serviceAccountKey.json"
    )

    cred = credentials.Certificate(service_account)

    firebase_app = firebase_admin.initialize_app(cred)

    return firebase_app