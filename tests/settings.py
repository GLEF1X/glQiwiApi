import os

QIWI_WALLET_CREDENTIALS = {
    "phone_number": os.getenv("PHONE_NUMBER"),
    "api_access_token": os.getenv("API_ACCESS_TOKEN"),
}

QIWI_P2P_CREDENTIALS = {"secret_p2p": os.getenv("SECRET_P2P")}

YOO_MONEY_CREDENTIALS = {"api_access_token": os.getenv("YOO_API_TOKEN")}

YOO_MONEY_TEST_CLIENT_ID = os.getenv("YOO_TEST_CLIENT_ID")
