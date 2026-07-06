import base64
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
import uuid

def get_access_token():
    consumer_key = "EG2cnGnCW3eYuufUwy5cfp0Wn9WX7kc2JWZbgVhEyYaNL10z"
    consumer_secret = "FaTIhKmvRWClYQLAYp40yxMaijHcipttriE6E4Wdm6KuIn1omy4JV9Ts3MX9x61R"

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
        "CallBackURL": "https://intermastoid-verna-issueless.ngrok-free.dev/api/leases/payments/callback/",
        "AccountReference": account_reference,
        "TransactionDesc": "Rent Payment"
    }

    response = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    return response.json()

def initiate_b2c_payment(phone_number, amount, remarks, occasion=""):
    originator_conversation_id = uuid.uuid4().hex

    access_token = get_access_token()

    payload = {
        "OriginatorConversationID": originator_conversation_id,
        "InitiatorName": "testapi",
        "SecurityCredential": "gdJ2ZddtVRkCtIrjQevuJklB7VKBoA8jYla/WzbqkCmfl8359nlj3DBq1gKF+D5H27zUFIOEWyzUdGcTyoXWP9KeJJaqoi36WrC/i+XGUoNs3smbAxR8uDoVIeTFLK+MClj0/C9ymBjrNK9pI9nnteSUShBEI7V7i88xUDB5jxKZJPD9J1sCLC5en4XTJw/4+ACzjrXKEFf+LXNHPQanQ+Synte8ikmcIkT9F+G6wm5hx0cCNSqyeyqBBVp51ddI0Pd3blIjLc69Q5qJHc1Fjs4eYDh80KhOIyWB/+uhuOxKoXxxiWXnqEpj1lXQ6zjFaHLoIeNst0+oSdVdQ2c29g==",
        "CommandID": "BusinessPayment",
        "Amount": int(amount),
        "PartyA": "600990",
        "PartyB": phone_number,
        "Remarks": remarks,
        "Occasion": occasion,
        "QueueTimeOutURL": "https://intermastoid-verna-issueless.ngrok-free.dev/api/leases/settlements/b2c/timeout/",
        "ResultURL": "https://intermastoid-verna-issueless.ngrok-free.dev/api/leases/settlements/b2c/result/",
    }
    response = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/b2c/v3/paymentrequest",
        json=payload,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
    )

    return response.json()