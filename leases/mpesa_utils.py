import base64
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth

def get_access_token():
    consumer_key = "3OTSDozmHvaXrKRrSTF6Ck2o0ONnXgsGZDPFASojdlqMn2eG"
    consumer_secret = "dZONHK8e0sAc3uhKBo7UyQSCaFlwzR6w3G0qvPIFBw6ns0rOBiYX47YyoBMep1yK"

    response = requests.get(
        "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
        auth=HTTPBasicAuth(consumer_key, consumer_secret)
    )
    return response.json()["access_token"]

def initiate_stk_push(phone_number, amount, account_reference):
    shortcode = "174379"
    passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode()

    access_token = get_access_token()
    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone_number,
        "PartyB": shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": "https://kevinkaranja098.pythonanywhere.com/api/leases/payments/callback/",
        "AccountReference": account_reference,
        "TransactionDesc": "Rent Payment"
    }

    response = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    return response.json()