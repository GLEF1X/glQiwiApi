from json import JSONDecodeError
from typing import Dict, Any, Optional

try:
    from orjson import JSONDecodeError as OrjsonJSONDecodeError
except ImportError:
    OrjsonJSONDecodeError = JSONDecodeError  # noqa  # type: ignore

from glQiwiApi.core.session.holder import Response
from glQiwiApi.utils.compat import json

HTTP_STATUS_MATCH_TO_ERROR = {
    400: "Query syntax error (invalid data format). Can be related to wrong arguments,"
         " that you have passed to method",
    401: "Wrong API token or token expired",
    403: "No permission for this request(API token has insufficient permissions)",
    404: "Object was not found or there are no objects with the specified characteristics",
    423: "Too many requests, the service is temporarily unavailable",
    422: "The domain / subnet / host is incorrectly specified"
         "webhook (in the new_url parameter for the webhook URL),"
         "the hook type or transaction type is incorrectly specified,"
         "an attempt to create a hook if there is one already created",
    405: "Error related to the type of API request, contact the developer or open an issue",
    500: "Internal service error",
}


class QiwiAPIError(Exception):
    __slots__ = "_http_response", "_custom_message"

    def __init__(self, http_response: Response, custom_message: Optional[str] = None):
        self._http_response = http_response
        self._custom_message = custom_message

    def __str__(self) -> str:
        resp = (
            "HTTP status code={sc} description=`{msg}`, additional_info={info}" ""
        )
        return resp.format(
            sc=self._http_response.status_code,
            msg=self._custom_message or self._match_message(),
            info={"raw_response": self._try_deserialize_response()}
        )

    def json(self) -> Dict[str, Any]:
        return self._try_deserialize_response()

    def _match_message(self) -> str:
        """
        Matching exception message(-s) executes in two steps

        1) Search error message in dictionary with predefined error messages
        2) Deserialize response and try to know whether there is errorCode,
         that can be interpreted as error message

        If there are two messages founded, then it will be concatenated
        """
        error_message = HTTP_STATUS_MATCH_TO_ERROR.get(self._http_response.status_code, "")
        json_response = self._try_deserialize_response()
        err_code = json_response.get("errorCode", "")

        if err_code != "":
            error_message += f", error code = {err_code}"

        return error_message

    def _try_deserialize_response(self) -> Dict[str, Any]:
        try:
            return json.loads(self._http_response.body)
        except (JSONDecodeError, TypeError, OrjsonJSONDecodeError):
            return {}
