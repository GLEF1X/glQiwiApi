from __future__ import annotations

from typing import Optional

import pytest

from glQiwiApi.types import Transaction
from glQiwiApi.types.qiwi.transaction import TransactionType
from glQiwiApi.utils.payload import check_transaction


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
        check_transaction(
            [transaction],
            amount=transaction.sum.amount,
            transaction_type=TransactionType.OUT,
            sender=sender,
            comment=comment,
        )
        is True
    )
