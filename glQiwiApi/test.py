import asyncio
from datetime import datetime, timedelta

from glQiwiApi import QiwiWrapper
from glQiwiApi.utils import measure_time

wallet = QiwiWrapper(
    api_access_token='7f8e514786b0cd326cf604223ec91861',
    phone_number='+380968317459',
    public_p2p='48e7qUxn9T7RyYE1MVZswX1FRSbE6iyCj2gCRwwF3Dnh5XrasNTx3BGPiMsyXQFNKQhvukniQG8RTVhYm3iPpzd6T6fUwiBX4WcjnHgoqxERdngWnH6EYfc7uBsGKPq4MF23dW4nUoixGqkoHj1YhjM7JyGfvh1o6fUdCHfX2uY8cfMxUFDwj8qRQgwPF',
    secret_p2p='eyJ2ZXJzaW9uIjoiUDJQIiwiZGF0YSI6eyJwYXlpbl9tZXJjaGFudF9zaXRlX3VpZCI6ImJuMXZmNy0wMCIsInVzZXJfaWQiOiIzODA5NjgzMTc0NTkiLCJzZWNyZXQiOiI1MWY2MDc1MzkzYzgwZWZiY2FiM2Q5ZTVhNThjNjQ1NmE3ZWY4NjkxNDJkZjI0NjczNWYzNzZmZjkwODQwM2U4In19'
)


@measure_time
async def main():
    # bill = await wallet.create_p2p_bill(
    #     amount=1
    # )
    # transactions = await wallet.fetch_statistics(
    #     start_date=datetime.now() - timedelta(days=80),
    #     end_date=datetime.now() - timedelta(days=10)
    # )multiply_objects_parse
    print(await wallet.transactions(
        start_date=datetime.now() + timedelta(days=5),
        end_date=datetime.now()
    ))
    # bill = await wallet.create_p2p_bill(
    #     amount=1,
    #     comment='my_comment'
    # )
    # Мой вариантarbitrary_types_allowed = True


asyncio.run(main())
