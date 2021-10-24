from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class QiwiErrorAnswer(BaseModel):
    service_name: str = Field(..., alias="serviceName")
    error_code: str = Field(..., alias="errorCode")
    description: str = Field(..., alias="description")
    user_msg: str = Field(..., alias="userMessage")
    dt: datetime = Field(..., alias="dateTime")
    trace_id: str = Field(..., alias="traceId")

    def construct_error_message(self) -> str:
        return f"Error code: {self.error_code}, description: {self.description}"
