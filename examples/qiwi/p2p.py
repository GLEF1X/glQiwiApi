import asyncio

from glQiwiApi import QiwiWrapper, RequestError

SECRET_KEY = "P2P SECRET_KEY"


async def p2p_usage():
    async with QiwiWrapper(secret_p2p=SECRET_KEY) as w:
        # bill id will be generated as str (uuid.uuid4 ()) if not passed
        bill = await w.create_p2p_bill(amount=1, comment="Im using glQiwiApi")
        print(bill)
        # This is how you can check the status for paid
        status_1 = (await w.check_p2p_bill_status(bill_id=bill.bill_id)) == "PAID"
        # Or you can (it looks more concise in my opinion)
        status_2 = await bill.paid
        print(status_1 == status_2)
        # This will throw an error as api_access_token and phone_number are not passed
        # You can reassign a token or number at any time
        try:
            await w.retrieve_bills(rows=50)
        except RequestError as ex:
            print(ex)
        # Reassign tokens and no longer observe errors
        w.api_access_token = "TOKEN from https://qiwi.api"
        w.phone_number = "+NUMBER"
        print(await w.retrieve_bills(rows=20))


asyncio.run(p2p_usage())
