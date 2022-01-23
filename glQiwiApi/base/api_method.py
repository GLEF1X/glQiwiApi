import abc
import copy
from typing import Dict, Optional, Any, TypeVar, Generic, Type, Union, Tuple, ClassVar, no_type_check, \
    Callable, List

from pydantic import BaseModel, BaseConfig, Extra, parse_obj_as
from pydantic.fields import ModelField
from pydantic.generics import GenericModel

from glQiwiApi.utils.compat import json

ReturningType = TypeVar("ReturningType")
_T = TypeVar("_T")
_sentinel = object()


class RuntimeValueIsMissing(Exception):
    pass


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
        json_dumps = json.dumps

    __returning_type__: ClassVar[Any] = _sentinel

    request_schema: ClassVar[Dict[str, Any]] = {}

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

        if cls.__returning_type__ is _sentinel or cls.__returning_type__ is ReturningType:
            cls.__returning_type__ = key
        else:
            try:
                cls.__returning_type__ = cls.__returning_type__[key]
            except TypeError:
                cls.__returning_type__ = key

        return super().__class_getitem__(params)

    def __init_subclass__(cls) -> None:
        if APIMethod.__returning_type__ is not _sentinel:
            cls.__returning_type__, APIMethod.__returning_type__ = APIMethod.__returning_type__, _sentinel

    def build_request(self, **url_format_kw: Any) -> "Request":
        request_kw: Dict[str, Any] = {}

        if self.http_method == 'GET' and self.request_schema:
            raise TypeError(
                "Request schema is not compatible with GET http method "
                "since GET method cannot send json payload"
            )

        if self.http_method == "GET":
            request_kw["params"] = self.dict(exclude_none=True, by_alias=True)

        if self.request_schema:
            request_kw["json_payload"] = self.Config.json_dumps(self._fill_runtime_values_in_request_schema(
                request_schema=self.request_schema,
                values=self.dict(by_alias=True)
            ))
        else:
            request_kw["data"] = self.dict(exclude_none=True, by_alias=True)

        return Request(
            endpoint=self.url.format(**url_format_kw, **self._get_runtime_path_values()),
            http_method=self.http_method,
            **request_kw
        )

    def _fill_runtime_values_in_request_schema(
            self,
            request_schema: Dict[str, Any],
            values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Algorithm of this function firstly takes care of default values,
        if field has no default value for schema it checks values, that were transmitted to method

        @param request_schema:
        @param values:
        @return:
        """
        self._apply_default_values(request_schema, values)

        for key, field in self.__fields__.items():
            scheme_path: str = field.field_info.extra.get("scheme_path", field.name)
            path_list = scheme_path.split(".")
            field_value = values.get(key)
            _substitute_runtime_value_by_path(request_schema, *path_list, value=field_value)

        return request_schema

    def _apply_default_values(self, schema: Dict[str, Any], values: Dict[str, Any]) -> None:
        scheme = copy.copy(schema)
        scheme_paths: List[str] = [
            field.field_info.extra.get("scheme_path", field.name)
            for field in self.__fields__.values()
        ]

        for k, v in list(scheme.items()):
            if isinstance(v, dict):
                self._apply_default_values(v, values)
            elif isinstance(v, RuntimeValue):
                if v.has_default() and k not in scheme_paths:
                    scheme[k] = v.get_default()
                    continue

    def _get_runtime_path_values(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        for field_name, value in self.dict(exclude_none=True).items():
            field: ModelField = self.__fields__[field_name]
            is_path_runtime_value = field.field_info.extra.get("path_runtime_value", False)
            if not is_path_runtime_value:
                continue

            result[field_name] = value

        return result

    @classmethod
    @no_type_check
    def parse_response(cls, obj: Any) -> ReturningType:
        if cls.__returning_type__ is _sentinel or cls.__returning_type__ is ReturningType:
            raise RuntimeError(f"{cls.__qualname__}: __returning_type__ is missing")

        try:
            if issubclass(cls.__returning_type__, BaseModel):
                return cls.__returning_type__.parse_obj(obj)
        except TypeError:  # issubclass() arg 1 must be a class
            pass

        return parse_obj_as(cls.__returning_type__, obj)

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
    json_payload: Optional[Any] = None
    headers: Optional[Dict[str, Any]] = None

    http_method: str = "GET"

    class Config(BaseConfig):
        arbitrary_types_allowed = True


class RuntimeValue:
    __slots__ = ('_default', '_default_factory')

    def __init__(self, default: Optional[Any] = None, default_factory: Optional[Callable[..., Any]] = None):
        self._default = default
        self._default_factory = default_factory

    def has_default(self) -> bool:
        return self._default is not None or self._default_factory is not None

    def get_default(self) -> Any:
        if self._default is not None:
            return self._default
        if self._default_factory is not None:
            return self._default_factory()


def _substitute_runtime_value_by_path(d: Dict[str, _T], *keys: str, value: Any) -> None:
    if not keys:
        return

    if len(keys) == 1:
        d[keys[0]] = value

    for k, v in d.items():
        if isinstance(v, dict):
            _substitute_runtime_value_by_path(v, *keys[1:], value=value)
