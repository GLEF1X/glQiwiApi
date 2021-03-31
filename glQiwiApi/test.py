import asyncio
from datetime import datetime, timedelta

from glQiwiApi import QiwiWrapper
from glQiwiApi.utils import measure_time

w = QiwiWrapper(
    api_access_token='6e29acc3b8414174b67aeee65f685f68',
    phone_number='+380985272064',
    public_p2p='48e7qUxn9T7RyYE1MVZswX1FRSbE6iyCj2gCRwwF3Dnh5XrasNTx3BGPiMsyXQFNKQhvukniQG8RTVhYm3iPpzd6T6fUwiBX4WcjnHgoqxERdngWnH6EYfc7uBsGKPq4MF23dW4nUoixGqkoHj1YhjM7JyGfvh1o6fUdCHfX2uY8cfMxUFDwj8qRQgwPF',
    secret_p2p='eyJ2ZXJzaW9uIjoiUDJQIiwiZGF0YSI6eyJwYXlpbl9tZXJjaGFudF9zaXRlX3VpZCI6ImJuMXZmNy0wMCIsInVzZXJfaWQiOiIzODA5NjgzMTc0NTkiLCJzZWNyZXQiOiI1MWY2MDc1MzkzYzgwZWZiY2FiM2Q5ZTVhNThjNjQ1NmE3ZWY4NjkxNDJkZjI0NjczNWYzNzZmZjkwODQwM2U4In19'
)


@measure_time
async def main():
    tr = await w.create_p2p_bill(
        life_time=datetime.now() + timedelta(seconds=20),
        amount=1
    )
    print(tr.pay_url)

asyncio.run(main())