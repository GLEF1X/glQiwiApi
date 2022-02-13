import os

QIWI_WALLET_CREDENTIALS = {
    "phone_number": os.getenv("QIWI_PHONE_NUMBER"),
    "api_access_token": os.getenv("QIWI_API_ACCESS_TOKEN"),
}

QIWI_P2P_CREDENTIALS = {"secret_p2p": os.getenv("QIWI_SECRET_P2P")}

YOO_MONEY_CREDENTIALS = {"api_access_token": os.getenv("YOOMONEY_API_TOKEN")}

YOO_MONEY_TEST_CLIENT_ID = os.getenv("YOOMONEY_TEST_CLIENT_ID")
