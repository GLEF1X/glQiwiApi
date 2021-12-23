import uuid

from fastapi import FastAPI, Response
from starlette.responses import HTMLResponse, JSONResponse

app = FastAPI()


@app.get(
    "/proxy/p2p/{invoice_uid}",
    response_class=HTMLResponse,
    tags=["proxy"],
    summary="Helps you to add Referrer attribute when use qiwi p2p to avoid blocking",
)
async def process_proxy_p2p_request(invoice_uid: uuid.UUID) -> HTMLResponse:
    return HTMLResponse(
        f"""
        <html>
            <meta name="referrer" content="origin">
            </meta>
        </html>
        <script>
            location.href = "https://oplata.qiwi.com/form?invoiceUid={invoice_uid}"
        </script>
        """
    )


@app.get("/", include_in_schema=False)
async def index() -> Response:
    return JSONResponse({"message": "Hello, World!"})
