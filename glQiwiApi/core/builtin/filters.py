from glQiwiApi.core.web_hooks.filter import LambdaBasedFilter
from glQiwiApi.types import Transaction, WebHook, Notification

# Default filter for transaction handler
transaction_webhook_filter: LambdaBasedFilter = LambdaBasedFilter(
    lambda update: isinstance(update, (WebHook, Transaction))
)

# Default filter for bill handler
bill_webhook_filter: LambdaBasedFilter = LambdaBasedFilter(lambda update: isinstance(update, Notification))
