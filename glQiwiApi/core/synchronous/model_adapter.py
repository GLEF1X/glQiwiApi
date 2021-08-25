from __future__ import annotations

from typing import no_type_check

from glQiwiApi.types import Bill
from glQiwiApi.types.base import Base


class AdaptedBill(Bill):
    def check(self) -> bool:  # type: ignore
        if self.sync_client is None:
            raise RuntimeError("No synchronous client found in context")
        return self.sync_client.check_p2p_bill_status(bill_id=self.bill_id) == "PAID"


@no_type_check
def adapt_type(result):
    from .adapter import SyncAdaptedQiwi

    adapted_instance = SyncAdaptedQiwi.get_current()
    if not isinstance(result, Base):
        return result
    setattr(result, "sync_client", adapted_instance)
    if not isinstance(result, Bill):
        return result
    return AdaptedBill.parse_obj(result.dict(by_alias=True))
