from glQiwiApi.core.web_hooks.filter import Filter
from glQiwiApi.types import Transaction, WebHook, Notification

# Default filter for transaction handler
transaction_webhook_filter: Filter = Filter(
    lambda update: isinstance(update, (WebHook, Transaction))
)

# Default filter for bill handler
bill_webhook_filter: Filter = Filter(lambda update: isinstance(update, Notification))
