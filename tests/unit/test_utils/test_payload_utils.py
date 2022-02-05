from __future__ import annotations

from typing import Optional

import pytest

from glQiwiApi.qiwi.clients.wallet.types import Transaction, History, TransactionType
from glQiwiApi.qiwi.utils import is_transaction_exists_in_history


@pytest.mark.parametrize(
    "sender,comment",
    [
        (None, None),
        (None, "my_comment"),
        ("+38908234234", None),
    ],
)
def test_check_transaction(
    transaction: Transaction, sender: Optional[str], comment: Optional[str]
):
    assert (
        is_transaction_exists_in_history(
            History.parse_obj({"data": [transaction]}),
            amount=transaction.sum.amount,
            transaction_type=TransactionType.OUT,
            sender=sender,
            comment=comment,
        )
        is True
    )
