import asyncio
from typing import Union

import aiohttp
import time

# Перевод на QIWI Кошелек
from api import HttpXParser


# def send_p2p(api_access_token, to_qw, comment, sum_p2p):
#     s = object()
#     s.headers = {'content-type': 'application/json'}
#     s.headers['authorization'] = 'Bearer ' + api_access_token
#     s.headers['User-Agent'] = 'Android v3.2.0 MKT'
#     s.headers['Accept'] = 'application/json'
#     postjson = {"id": "", "sum": {"amount": "", "currency": ""},
#                 "paymentMethod": {"type": "Account", "accountId": "643"}, "comment": f"{comment}",
#                 "fields": {"account": ""}}
#     postjson['id'] = str(int(time.time() * 1000))
#     postjson['sum']['amount'] = sum_p2p
#     postjson['sum']['currency'] = '643'
#     postjson['fields']['account'] = to_qw
#     res = s.post('https://edge.qiwi.com/sinap/api/v2/terms/99/payments', json=postjson)
#     return res.json()
#
#
# print(send_p2p(
#     api_access_token='bfca39a457751dd03ef1dc3407cf1217',
#     to_qw='+380985272064',
#     sum_p2p=1,
#     comment='privet'
# ))


async def qiwi_main(
        api_access_token: str,
        tranz_sum: Union[float, int],
        to_card: str,
        prv_id: str = '22351'
):
    parser = HttpXParser()
    json_data = {
        "id": str(int(time.time() * 1000)),
        "sum":
            {
                "amount": "", "currency": "643"
            },

        "paymentMethod":
            {
                "type": "Account", "accountId": "643"
            },
        "fields": {
            "account": ""
        }
    }
    json_data['sum']['amount'] = tranz_sum
    json_data['fields']['account'] = to_card
    async for response in parser.fast().fetch(
            url='https://edge.qiwi.com/sinap/api/v2/terms/' + prv_id + '/payments',
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': 'Bearer {token}'.format(token=api_access_token),
                'Host': 'edge.qiwi.com',
            },
            json=json_data
    ):
        print(response.status_code)

if __name__ == '__main__':
    asyncio.run(qiwi_main(
        api_access_token='bfca39a457751dd03ef1dc3407cf1217',
        to_card='4890494716063292',
        tranz_sum=1
    ))