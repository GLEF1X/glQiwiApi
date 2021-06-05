import glQiwiApi.types.qiwi_types as types
from glQiwiApi.core.web_hooks.filter import Filter

# Default filter for transaction handler
transaction_webhook_filter: Filter = Filter(
    lambda update: isinstance(update, (types.WebHook, types.Transaction))
)

# Default filter for bill handler
bill_webhook_filter: Filter = Filter(
    lambda update: isinstance(update, types.Notification)
)
