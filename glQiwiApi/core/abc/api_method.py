import abc
from typing import (
    Dict,
    Optional,
    Any,
    TypeVar,
    Generic,
    ClassVar,
    Callable,
    List,
    Set,
    cast,
    Union,
    Type,
    Tuple,
)

from pydantic import BaseModel, BaseConfig, Extra, parse_obj_as
from pydantic.fields import ModelField
from pydantic.generics import GenericModel

from glQiwiApi.core.session.holder import HTTPResponse
from glQiwiApi.utils.compat import json

ReturningType = TypeVar("ReturningType")
_T = TypeVar("_T")
_sentinel = object()


class RuntimeValueIsMissing(Exception):
    pass


def _filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v}


DEFAULT_EXCLUDE = {"request_schema", "endpoint", "http_method"}


class APIMethod(abc.ABC, GenericModel, Generic[ReturningType]):
    """
    Reflect the real API method that could be emitted using appropriate clients.
    """

    class Config(BaseConfig):
        extra = Extra.allow
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        orm_mode = True
        underscore_attrs_are_private = True
        json_loads = json.loads
        json_dumps = json.dumps  # type: ignore

    __returning_type__: ClassVar[Any] = _sentinel

    json_payload_schema: ClassVar[Dict[str, Any]] = {}

    def __class_getitem__(cls, params: Union[Type[Any], Tuple[Type[Any], ...]]) -> Type[Any]:
        """
        Allows us to get generic class in runtime instead of do it explicitly
        in every class that inherits from APIMethod.

        @param params:
        @return:
        """
        if isinstance(params, tuple):
            return super().__class_getitem__(params)

        if not params and cls is not Tuple:
            raise TypeError(f"Parameter list to {cls.__qualname__}[...] cannot be empty")

        key = params  # just alias

        if cls.__returning_type__ is _sentinel or cls.__returning_type__ is ReturningType:  # type: ignore
            cls.__returning_type__ = key
        else:
            try:
                cls.__returning_type__ = cls.__returning_type__[key]
            except TypeError:
                cls.__returning_type__ = key

        return super().__class_getitem__(params)

    def __init_subclass__(cls) -> None:
        if cls.__returning_type__ is not _sentinel:
            cls.__returning_type__ = cls.__returning_type__

    @classmethod
    def parse_http_response(cls, response: HTTPResponse) -> ReturningType:
        if cls.__returning_type__ is _sentinel or cls.__returning_type__ is ReturningType:  # type: ignore
            raise RuntimeError(f"{cls.__qualname__}: __returning_type__ is missing")

        json_response = response.json()

        manually_parsed_json = cls.on_json_parse(response)
        if manually_parsed_json is not _sentinel:
            return manually_parsed_json

        try:
            if issubclass(cls.__returning_type__, BaseModel):
                return cast(ReturningType, cls.__returning_type__.parse_obj(json_response))
        except TypeError:  # issubclass() arg 1 must be a class
            pass

        return cast(ReturningType, parse_obj_as(cls.__returning_type__, json_response))

    @classmethod
    def on_json_parse(cls, response: HTTPResponse) -> Union[Any, ReturningType]:
        return _sentinel

    def build_request(self, **url_format_kw: Any) -> "Request":
        request_kw: Dict[str, Any] = {
            "endpoint": self.url.format(**url_format_kw, **self._get_runtime_path_values()),
            "http_method": self.http_method,
        }

        if self.http_method == "GET" and self.json_payload_schema:
            raise TypeError(
                "Request schema is not compatible with GET http method "
                "since GET method cannot transfer_money json payload"
            )

        if self.http_method == "GET":
            request_kw["params"] = self.dict(
                exclude_none=True, by_alias=True, exclude=self._get_exclude_set()
            )

        if self.json_payload_schema:
            request_kw["json_payload"] = self._get_filled_json_payload_schema()
        else:
            request_kw["data"] = self.dict(
                exclude_none=True, by_alias=True, exclude=self._get_exclude_set()
            )

        return Request(**_filter_none_values(request_kw))

    def _get_exclude_set(self) -> Set[str]:
        to_exclude: Set[str] = DEFAULT_EXCLUDE.copy()
        for key, field in self.__fields__.items():
            if field.field_info.extra.get("path_runtime_value", False):
                to_exclude.add(key)

        return to_exclude

    def _get_filled_json_payload_schema(self) -> Dict[str, Any]:
        """
        Algorithm of this function firstly takes care of default values,
        if field has no default value for schema it checks values, that were transmitted to method

        @return:
        """
        request_schema = self._get_schema_with_filled_runtime_values()
        schema_values = self.dict(
            exclude_none=True, by_alias=True, exclude=self._get_exclude_set()
        )

        for key, field in self.__fields__.items():
            scheme_path: str = field.field_info.extra.get("scheme_path", field.name)
            keychain = scheme_path.split(".")
            try:
                field_value = schema_values[key]
            except KeyError:
                continue
            _insert_value_into_dictionary(request_schema, keychain, field_value)

        return request_schema

    def _get_schema_with_filled_runtime_values(self) -> Dict[str, Any]:
        scheme_paths: List[str] = [
            field.field_info.extra.get("scheme_path", field.name)
            for field in self.__fields__.values()
            if field.name in self.dict(exclude_none=True)
        ]
        schema = self.json_payload_schema.copy()

        def apply_runtime_values_to_schema(d: Dict[str, Any]) -> None:
            for k, v in list(d.items()):
                if isinstance(v, dict):
                    apply_runtime_values_to_schema(v)
                elif isinstance(v, RuntimeValue):
                    if v.has_default() and k not in scheme_paths:
                        d[k] = v.get_default()
                        continue
                    elif v.is_mandatory is False:
                        d.pop(k)

        apply_runtime_values_to_schema(schema)

        return schema

    def _get_runtime_path_values(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        for field_name, value in self.dict().items():
            field: ModelField = self.__fields__[field_name]
            is_path_runtime_value = field.field_info.extra.get("path_runtime_value", False)
            if not is_path_runtime_value:
                continue

            result[field_name] = value

        return result

    @property
    @abc.abstractmethod
    def url(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def http_method(self) -> str:
        pass


class Request(BaseModel):
    endpoint: str

    data: Optional[Dict[str, Optional[Any]]] = None
    params: Optional[Dict[str, Optional[Any]]] = None
    json_payload: Optional[Dict[str, Any]] = None
    headers: Dict[str, Any] = {}

    http_method: str = "GET"

    class Config(BaseConfig):
        arbitrary_types_allowed = True


class RuntimeValue:
    __slots__ = ("_default", "_default_factory", "is_mandatory")

    def __init__(
        self,
        default: Optional[Any] = None,
        default_factory: Optional[Callable[..., Any]] = None,
        mandatory: bool = True,
    ):
        self._default = default
        self._default_factory = default_factory
        self.is_mandatory = mandatory

    def has_default(self) -> bool:
        return self._default is not None or self._default_factory is not None

    def get_default(self) -> Any:
        if self._default is not None:
            return self._default
        if self._default_factory is not None:
            return self._default_factory()


def _insert_value_into_dictionary(
    d: Dict[str, _T], keychain: List[str], value: Any
) -> None:  # pragma: no cover
    if not keychain:
        return None

    if len(keychain) == 1:
        d[keychain[0]] = value

    for k, v in d.items():
        if not isinstance(v, dict):
            continue
        next_key_from_keychain = keychain[0]

        if k != next_key_from_keychain:
            continue

        _insert_value_into_dictionary(v, keychain[1:], value)
