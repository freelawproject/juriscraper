from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Generic, Optional, TypeVar, Union, final, overload

import lxml.html
import pydantic_core
from pydantic import BaseModel, JsonValue

from juriscraper.lib.html_utils import clean_html

_V = TypeVar("_V")


_TCaseInsensitiveDict = TypeVar(
    "_TCaseInsensitiveDict", bound="CaseInsensitiveDict"
)


class CaseInsensitiveDict(Generic[_V], dict[str, _V]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for k in self.keys():
            if k != k.lower():
                v = super().pop(k)
                self[k.lower()] = v

    def __getitem__(self, key: str):
        return super().__getitem__(key.lower())

    def __setitem__(self, key: str, value):
        super().__setitem__(key.lower(), value)

    def __delitem__(self, key: str):
        return super().__delitem__(key.lower())

    def union(
        self, other: "CaseInsensitiveDict[_V]"
    ) -> "CaseInsensitiveDict[_V]":
        updated = CaseInsensitiveDict(self)
        updated.update(other)
        return updated


class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


_PydanticModel = TypeVar("_PydanticModel", bound=BaseModel)


class _NetworkDriverResponse(ABC):
    encoding: str
    headers: CaseInsensitiveDict[str]
    status: int
    url: str

    @overload
    def json(self, model: None) -> JsonValue: ...

    @overload
    def json(self, model: type[_PydanticModel]) -> _PydanticModel: ...

    def json(self, model: Optional[type[_PydanticModel]]) -> _PydanticModel:
        if model is not None:
            return model.model_validate_json(self.bytes())
        return pydantic_core.from_json(self.bytes())

    def text(self) -> str:
        return self.bytes().decode(self.encoding)

    def html(self) -> lxml.html.HtmlElement:
        return lxml.html.fromstring(clean_html(self.text()), base_url=self.url)

    @abstractmethod
    def bytes(self) -> bytes:
        raise NotImplementedError


NetworkDriverResponse = TypeVar(
    "NetworkDriverResponse", bound=_NetworkDriverResponse
)


@dataclass
class NetworkDriverRequest:
    url: str
    method: HTTPMethod
    params: dict[str, Union[str, int, list[Union[str, int]]]]
    data: dict[str, Union[str, int]]
    headers: CaseInsensitiveDict[str]
    json: Union[BaseModel, JsonValue]


class NetworkDriver(ABC):
    params: dict[str, Union[str, int, list[Union[str, int]]]] = {}
    data: dict[str, Union[str, int]] = {}
    headers: CaseInsensitiveDict[str] = CaseInsensitiveDict(
        {"User-Agent": "Free Law Project"}
    )
    timeout: float = 10.0

    @final
    def request(
        self,
        url: str,
        method: HTTPMethod = HTTPMethod.GET,
        params: Optional[
            dict[str, Union[str, int, list[Union[str, int]]]]
        ] = None,
        data: Optional[dict[str, Union[str, int]]] = None,
        headers: Optional[CaseInsensitiveDict[str]] = None,
        json: Optional[Union[_PydanticModel, JsonValue]] = None,
        timeout: Optional[float] = None,
    ) -> NetworkDriverResponse:
        if params is None:
            params = {}
        if data is None:
            data = {}
        if headers is None:
            headers = CaseInsensitiveDict()
        if timeout is None:
            timeout = self.timeout
        request = NetworkDriverRequest(
            url=url,
            method=method,
            params=self.params | params,
            data=self.data | data,
            headers=self.headers.union(headers),
            json=json,
        )
        return self.send(request, timeout)

    @abstractmethod
    def send(
        self, request: NetworkDriverRequest, timeout: float
    ) -> NetworkDriverResponse:
        raise NotImplementedError
