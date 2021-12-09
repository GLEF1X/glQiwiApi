from typing import Optional

from pydantic import BaseModel


class WebhookAPIError(BaseModel):
    status: str
    detail: Optional[str] = None
