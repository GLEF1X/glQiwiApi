from typing import Union, Optional

from glQiwiApi.qiwi.clients.wallet.types import History, TransactionType


def is_transaction_exists_in_history(
        history: History,
        amount: Union[int, float],
        transaction_type: TransactionType = TransactionType.IN,
        sender: Optional[str] = None,
        comment: Optional[str] = None,
) -> bool:
    for txn in history:
        if txn.sum.amount < amount or txn.type != transaction_type.value:
            continue
        if txn.comment == comment and txn.to_account == sender:
            return True
        elif comment and sender:
            continue
        elif txn.to_account == sender:
            return True
        elif sender:
            continue
        elif txn.comment == comment:
            return True
        elif comment:
            continue
        return True
    return False
