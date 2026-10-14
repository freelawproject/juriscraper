from __future__ import annotations

from collections.abc import (
    AsyncIterable,
    Awaitable,
    Callable,
    Iterable,
    Mapping,
    Sequence,
)
from datetime import date
from enum import Enum
from http.cookiejar import CookieJar
from ssl import SSLContext
from typing import IO, TYPE_CHECKING, TypeAlias

import httpx
from pydantic import ConfigDict, with_config
from typing_extensions import TypedDict

if TYPE_CHECKING:
    # HTTPX exports the sentinel value, but not its signature type.
    from httpx._client import UseClientDefault

CookieTypes: TypeAlias = (
    httpx.Cookies | CookieJar | dict[str, str] | list[tuple[str, str]]
)
QueryParamValue: TypeAlias = str | int | float | bool | None
QueryParamTypes: TypeAlias = (
    httpx.QueryParams
    | Mapping[str, QueryParamValue | Sequence[QueryParamValue]]
    | list[tuple[str, QueryParamValue]]
    | tuple[tuple[str, QueryParamValue], ...]
    | str
    | bytes
)

AuthTypes: TypeAlias = (
    httpx.Auth
    | tuple[str | bytes, str | bytes]
    | Callable[[httpx.Request], httpx.Request]
)
HeaderTypes: TypeAlias = (
    httpx.Headers
    | Mapping[str, str]
    | Mapping[bytes, bytes]
    | Sequence[tuple[str, str]]
    | Sequence[tuple[bytes, bytes]]
)
TimeoutTypes: TypeAlias = (
    httpx.Timeout
    | float
    | tuple[float | None, float | None, float | None, float | None]
    | None
)
RequestContent: TypeAlias = (
    str | bytes | Iterable[bytes] | AsyncIterable[bytes]
)
FileContent: TypeAlias = IO[bytes] | bytes | str
FileTypes: TypeAlias = (
    FileContent
    | tuple[str | None, FileContent]
    | tuple[str | None, FileContent, str | None]
    | tuple[str | None, FileContent, str | None, Mapping[str, str]]
)
RequestFiles: TypeAlias = (
    Mapping[str, FileTypes] | Sequence[tuple[str, FileTypes]]
)


class _ClientOptions(TypedDict, total=False):
    """Public HTTPX client options, excluding separately handled cookies."""

    auth: AuthTypes | None
    params: QueryParamTypes | None
    headers: HeaderTypes | None
    verify: SSLContext | str | bool
    cert: str | tuple[str, str] | tuple[str, str, str] | None
    http1: bool
    http2: bool
    proxy: httpx.Proxy | httpx.URL | str | None
    mounts: Mapping[str, httpx.AsyncBaseTransport | None] | None
    timeout: TimeoutTypes
    follow_redirects: bool
    limits: httpx.Limits
    max_redirects: int
    event_hooks: Mapping[str, list[Callable[..., Awaitable[None]]]] | None
    base_url: httpx.URL | str
    transport: httpx.AsyncBaseTransport | None
    trust_env: bool
    default_encoding: str | Callable[[bytes], str]


class ClientOptions(_ClientOptions, closed=True):
    pass


class AsyncClientOptions(_ClientOptions, total=False, closed=True):
    cookies: CookieTypes | None


class RequestOptions(TypedDict, total=False):
    params: QueryParamTypes | None
    headers: HeaderTypes | None
    cookies: CookieTypes | None
    auth: AuthTypes | UseClientDefault | None
    follow_redirects: bool | UseClientDefault
    timeout: TimeoutTypes | UseClientDefault
    extensions: Mapping[str, object] | None


class GetRequestOptions(RequestOptions, closed=True):
    pass


class PostRequestOptions(RequestOptions, total=False, closed=True):
    content: RequestContent | None
    files: RequestFiles | None
    data: Mapping[str, object] | None
    json: object


class BackscrapeOptions(TypedDict, total=False):
    backscrape_start: str | None
    backscrape_end: str | None
    days_interval: int | None


@with_config(ConfigDict(extra="allow"))
class DynamoDBAttribute(TypedDict, total=False):
    # Only string values are read; preserve other types for pagination keys.
    S: str


DynamoDBItem: TypeAlias = dict[str, DynamoDBAttribute]


class DynamoDBScan(TypedDict, total=False):
    Items: list[DynamoDBItem]
    LastEvaluatedKey: DynamoDBItem


class ExtractedDocket(TypedDict, total=False, closed=True):
    appeal_from_str: str
    case_name: str
    case_name_full: str
    court_id: str
    date_argued: str | date
    docket_number: str
    panel_str: str


class ExtractedOpinion(TypedDict, total=False, closed=True):
    author_str: str
    per_curiam: bool
    type: str


class ExtractedCluster(TypedDict, total=False, closed=True):
    case_name: str
    case_name_full: str
    date_filed: str | date
    date_filed_is_approximate: bool
    disposition: str
    docket_number: str
    headnotes: str
    judges: str
    precedential_status: str
    procedural_history: str
    summary: str
    syllabus: str


class ExtractedOriginatingCourt(TypedDict, total=False, closed=True):
    assigned_to_str: str
    docket_number: str


class ExtractedMetadata(TypedDict, total=False, closed=True):
    """Model updates extracted from the text of an opinion."""

    Citation: str
    Docket: ExtractedDocket
    Opinion: ExtractedOpinion
    OpinionCluster: ExtractedCluster
    OriginatingCourtInformation: ExtractedOriginatingCourt


@with_config(ConfigDict(strict=True, extra="forbid"))
class RawOpinion(TypedDict, total=False):
    """Case fields before and after ClusterSite normalizes their names.

    Fields remain optional while a scraper builds a case or sub-opinion;
    the scraper's sanity checks enforce the required completed fields.
    """

    name: str
    url: str
    date: str | date | None
    date_filed_is_approximate: bool
    status: str | None
    docket: str | None
    judge: str | None
    citation: str | None
    parallel_citation: str | None
    summary: str | None
    lower_court: str | None
    child_court: str | None
    adversary_number: str | None
    division: str | None
    disposition: str | None
    cause: str | None
    docket_attachment_number: int | str | None
    docket_document_number: int | str | None
    nature_of_suit: str | None
    lower_court_id: str | None
    lower_court_number: str | None
    lower_court_judge: str | None
    author: str | None
    per_curiam: bool | None
    type: str | None
    joined_by: str | None
    other_date: str | None
    attorney: str | None
    headnote: str | None
    content: str | bytes | None
    court_reporter: str | None
    sub_opinions: list[RawOpinion]

    # ClusterSite replaces shorthand keys in the same public cases list.
    authors: str | None
    types: str | None
    download_urls: str
    case_names: str
    case_dates: date
    case_name_shorts: str
    blocked_statuses: bool
    precedential_statuses: str
    docket_numbers: str | None
    judges: str | None
    citations: str | None
    parallel_citations: str | None
    summaries: str | None
    lower_courts: str | None
    child_courts: str | None
    adversary_numbers: str | None
    divisions: str | None
    dispositions: str | None
    causes: str | None
    docket_attachment_numbers: int | str | None
    docket_document_numbers: int | str | None
    lower_court_ids: str | None
    lower_court_numbers: str | None
    lower_court_judges: str | None
    other_dates: str | None
    attorneys: str | None
    headnotes: str | None


class RawOralArgument(TypedDict, total=False):
    name: str
    url: str
    date: str | date | None
    docket: str | None
    judge: str | None
    attorney: str | None


# OpinionType is used to represent the type of opinion in a case. These values are the ones used on CourtListener.
class OpinionType(Enum):
    COMBINED = "010combined"
    UNANIMOUS = "015unamimous"
    MAJORITY = "020lead"
    PLURALITY = "025plurality"
    CONCURRENCE = "030concurrence"
    CONCURRING_IN_PART_AND_DISSENTING_IN_PART = "035concurrenceinpart"
    DISSENT = "040dissent"
    ADDENDUM = "050addendum"
    REMITTITUR = "060remittitur"
    REHEARING = "070rehearing"
    ON_THE_MERITS = "080onthemerits"
    ON_MOTION_TO_STRIKE_COST_BILL = "090onmotiontostrike"
