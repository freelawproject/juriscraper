import re
import time
from datetime import date

from lxml import html
from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker, clean_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.url = "http://www.isc.idaho.gov/opinions/cacivil.htm"
        self.court_id = self.__module__

    @override
    def tweak_response_object(self) -> None:
        """
        This state uses an HTTP header to indicate an encoding of UTF-8,
        but the encoding is actually ISO-8859-1, as indicated in the HTML
        itself. When this page is rendered in Firefox, chardet fails, and
        many unknown characters are displayed to the user. Setting the
        character encoding manually fixes the issue.
        """
        response = self.request.get("response")
        if response is None:
            raise ValueError("Download a response before accessing it.")
        response.encoding = "ISO-8859-1"

    @override
    def _get_case_names(self) -> list[str]:
        case_names: list[str] = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        xelements: list[HtmlElement] = self.html.xpath(
            '//li[@class="MsoNormal"]/span/a[1]'
        )
        for xelement in xelements:
            # Our text nodes are randomly surrounded by HTML spans, so we start
            # at a high level node, and strip down to just what we want.
            data_html = html.tostring(xelement, encoding=str)
            data_string = re.sub(r"<[^>]*?>", "", data_html)
            data_string = " ".join(data_string.split())

            # Several regexes are needed since we have hyphen-separated values
            regexes = [
                "(.*?)[-–](.*?)–",
                "(.*?)[-–](.*)-",
                "(.*?)[-–](.*)$",
            ]
            for regex in regexes:
                if (match := re.search(regex, data_string)) is not None:
                    case_names.append(match.group(2))
                    break

        return case_names

    @override
    def _get_download_urls(self) -> list[str]:
        download_urls = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(
            '//li[@class="MsoNormal"]/span/a[1]/@href'
        )
        for e in texts:
            download_urls.append(e)
        return download_urls

    @override
    def _get_case_dates(self) -> list[date]:
        case_dates: list[date] = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        elements: list[HtmlElement] = self.html.xpath(
            '//li[@class="MsoNormal"]/span/a[1]'
        )
        for e in elements:
            s = html.tostring(e, method="text", encoding="unicode")
            # Cleanup...
            s = s.split("-")[0]
            s = s.split("–")[0]
            date_formats = ["%B %d, %Y", "%B %d %Y", "%B %d , %Y"]
            for format in date_formats:
                try:
                    case_date = date.fromtimestamp(
                        time.mktime(time.strptime(clean_string(s), format))
                    )
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Could not parse opinion date: {s!r}")
            case_dates.append(case_date)
        return case_dates

    @override
    def _get_precedential_statuses(self) -> list[str]:
        return ["Published"] * len(self)
