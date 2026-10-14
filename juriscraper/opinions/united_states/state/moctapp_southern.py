from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.state import mo


class Site(mo.Site):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.court = "Southern"
        self.url = self.build_url()

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath(
            "//div[@class='margin-bottom-15']"
        )
        for row in rows:
            date = row.findall(".//input")[0].attrib["value"]
            for opinion in row.findall(
                ".//div[@class='list-group-item-text']"
            ):
                url = opinion.findall("a")[0].attrib["href"]
                all_text: list[str] = opinion.xpath(".//text()")
                case_metadata = [
                    t.strip() for t in all_text if bool(t.strip())
                ]
                if len(case_metadata) != 6:
                    continue
                docket, name, _, author, _, vote = case_metadata
                self.cases.append(
                    {
                        "name": name,
                        "docket": docket[:-1],
                        "url": url,
                        "date": date,
                        "disposition": vote.split(".")[0].strip(),
                        "author": author,
                        "judge": vote.split(".", 1)[1].strip(),
                    }
                )
