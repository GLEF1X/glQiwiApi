import uuid

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_is_response_correct_when_access_p2p_proxy(client: AsyncClient,
                                                         initialized_app: FastAPI) -> None:
    invoice_uid = str(uuid.uuid4())
    response = await client.get(initialized_app.url_path_for("p2p_proxy", invoice_uid=invoice_uid))
    assert response.status_code == 200
    assert response.text == f"""
        <html>
            <meta name="referrer" content="origin">
            </meta>
        </html>
        <script>
            location.href = "https://oplata.qiwi.com/form?invoiceUid={invoice_uid}"
        </script>
        """
