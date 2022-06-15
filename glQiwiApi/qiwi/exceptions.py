from json import JSONDecodeError
from typing import Any, ClassVar, Dict, List, NoReturn, Optional, Union, cast

try:
    from orjson import JSONDecodeError as OrjsonJSONDecodeError
except ImportError:
    OrjsonJSONDecodeError = JSONDecodeError  # noqa  # type: ignore

from glQiwiApi.core.session.holder import HTTPResponse
from glQiwiApi.utils.compat import json

HTTP_STATUS_MATCH_TO_ERROR = {
    400: 'Query syntax error (invalid data format). Can be related to wrong arguments,'
    ' that you have passed to method',
    401: 'Wrong API token or token expired',
    403: 'No permission for this request(API token has insufficient permissions)',
    404: 'Object was not found or there are no objects with the specified characteristics',
    423: 'Too many requests, the service is temporarily unavailable',
    422: 'The domain / subnet / host is incorrectly specified'
    'webhook (in the new_url parameter for the webhook URL),'
    'the hook type or transaction type is incorrectly specified,'
    'an attempt to create a hook if there is one already created',
    405: 'Error related to the type of API request, contact the developer or open an issue',
    500: 'Internal service error',
}


class QiwiAPIError(Exception):
    __slots__ = 'http_response', '_custom_message', '_deserialize_cache', 'error_code', 'message'

    description_en: ClassVar[Optional[str]] = None
    description_ru: ClassVar[Optional[str]] = None

    _error_code_match: ClassVar[Optional[Union[str, int, List[Union[str, int]]]]] = None
    _error_code_contains: ClassVar[Union[str, List[str], None]] = None

    def __init__(self, http_response: HTTPResponse, custom_message: Optional[str] = None):
        self._deserialize_cache: Dict[int, Any] = {}
        self._custom_message = custom_message
        self.http_response = http_response
        self.error_code = self._scaffold_error_code()
        self.message = self._scaffold_error_message()
        self.service_name = self._scaffold_service_name()

    def json(self) -> Dict[str, Any]:
        return self._deserialize_response()

    def raise_exception_matching_error_code(self) -> NoReturn:
        if self.error_code is None:
            raise self

        for ex in self.__class__.__subclasses__():
            err_code_matches: List[Union[int, str]] = ex._error_code_match or []
            if not isinstance(ex._error_code_match, list):
                err_code_matches = [ex._error_code_match]

            err_codes_contains: List[Union[str, int]] = ex._error_code_contains or []
            if not isinstance(err_codes_contains, list):
                err_codes_contains = [err_codes_contains]

            err_code_matches = [str(c) for c in err_code_matches]

            if self.error_code in err_code_matches:
                raise ex(self.http_response, self._custom_message)
            elif any(c in self.error_code.lower() for c in err_codes_contains):
                raise ex(self.http_response, self._custom_message)

        raise self

    def __str__(self) -> str:
        representation = (
            '{message}\n'
            '    * {status_code} HTTP status code\n'
            '    * raw response {raw_response}'
        )
        deserialized_response = self._deserialize_response()

        try:
            raw_response: str = json.dumps(deserialized_response, indent=4, ensure_ascii=False)  # type: ignore
        except Exception:
            raw_response = self.http_response.body.decode('utf-8')

        formatted_representation = representation.format(
            status_code=self.http_response.status_code,
            message=self._compose_error_message(),
            raw_response=raw_response,
        )
        if deserialized_response.get('errorCode') is not None:
            formatted_representation += (
                f"\n    * error code = {deserialized_response['errorCode']}"
            )

        return formatted_representation

    def _compose_error_message(self) -> str:
        """
        Composing error message(-s) executes in two steps

        1) Search error message in dictionary with predefined error messages
        2) Deserialize response and try to know whether there is errorCode,
         that can be interpreted as error message

        If there are two messages founded, then it will be concatenated
        """
        if self._custom_message or self.description_ru or self.description_en:
            return self._custom_message or self.description_ru or self.description_en  # type: ignore
        return HTTP_STATUS_MATCH_TO_ERROR.get(self.http_response.status_code, '')

    def _scaffold_error_code(self) -> Optional[str]:
        r = self._deserialize_response()
        err_code = r.get('errorCode')
        if isinstance(err_code, str):
            return err_code

        err_code = r.get('code')
        if isinstance(err_code, str):
            return err_code.replace('QWPRC-', '')  # type: ignore

        return None

    def _scaffold_error_message(self) -> Optional[str]:
        r = self._deserialize_response()
        return r.get('message') or r.get('description')

    def _scaffold_service_name(self) -> Optional[str]:
        r = self._deserialize_response()
        return r.get('serviceName')

    def _deserialize_response(self) -> Dict[str, Any]:
        """
        Deserializing of response many times is practically zero-cost call,
        because response is being cached after the first deserializing
        """
        if self._deserialize_cache.get(id(self.http_response)) is not None:
            return cast(Dict[str, Any], self._deserialize_cache[id(self.http_response)])

        try:
            content: Dict[str, Any] = json.loads(self.http_response.body)
        except (JSONDecodeError, TypeError, OrjsonJSONDecodeError):
            content = {}

        self._deserialize_cache[id(self.http_response)] = content
        return content


class InternalQIWIError(QiwiAPIError):
    _error_code_match = [3, 749, 750]
    description_en = 'Technical error. Repeat the request later'
    description_ru = 'Техническая ошибка. Повторите платеж позже.'


class IncorrectDataFormat(QiwiAPIError):
    _error_code_match = 4
    description_en = 'Incorrect format of phone or account number. Check the data'
    description_ru = 'Некорректный формат телефона или счета. Проверьте данные.'


class NoSuchNumber(QiwiAPIError):
    _error_code_match = 5
    description_en = 'No such number. Check the data and try again'
    description_ru = 'Данного номера не существует. Проверьте данные и попробуйте еще раз.'


class BankSideReceiptError(QiwiAPIError):
    _error_code_match = 8
    description_en = "Technical problem on the recipient's bank side. Try again later"
    description_ru = 'Техническая проблема на стороне банка-получателя. Попробуйте позже.'


class PaymentUnavailableInYourCountry(QiwiAPIError):
    _error_code_match = 131
    description_en = 'Payment type unavailable for your country'
    description_ru = 'Платеж недоступен для вашей страны'


class NotEnoughFundsError(QiwiAPIError):
    _error_code_match = [220, 407]
    description_en = 'Not enough funds. Replenish your wallet'
    description_ru = 'Недостаточно средств. Пополните кошелек'


class PaymentRejected(QiwiAPIError):
    _error_code_match = [7000, 7600]
    description_en = "Payment rejected. Check card's details and repeat the payment or try to contact the bank that issued the card"
    description_ru = 'Платеж отклонен. Проверьте реквизиты карты и повторите платеж или обратитесь в банк, выпустивший карту'


class ValidationError(QiwiAPIError):
    _error_code_match = [303, 254, 241, 'validation.error', 558, 'internal.invoicing.error']


class ObjectNotFoundError(QiwiAPIError):
    _error_code_contains = 'not.found'


class ReceiptNotAvailable(QiwiAPIError):
    _error_code_contains = 'cheque.not.available'
    description_en = (
        'It is impossible to receive a check due to the fact that '
        'the transaction for this ID has not been completed,'
        'that is, an error occurred during the transaction'
    )


class OperationLimitExceededError(QiwiAPIError):
    _error_code_match = [705, 704, 700, 716, 717]


class ObjectAlreadyExistsError(QiwiAPIError):
    _error_code_contains = ['already.exists']
    description_ru = 'Объект, который вы хотите создать уже был создан ранее'
    description_en = 'Object that you want to create was have already been created earlier'


class MobileOperatorCannotBeDeterminedError(QiwiAPIError):
    pass


class InsufficientTokenRightsError(QiwiAPIError):
    _error_code_match = [309]
    description_ru = 'Недостаточно прав для выполнения данного действия. Чтобы решить эту проблему вам нужно перевыпустить токен с достаточными правами для выполнения нужного вам API метода на сайте QIWI.'
    description_en = 'There are insufficient rights to execute this API method. In order to solve this problem you should regenerate API token with sufficient rights.'
