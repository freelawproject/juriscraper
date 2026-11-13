import re
from datetime import date, datetime
from urllib.parse import parse_qs, urlparse

from dateutil.relativedelta import relativedelta
from lxml import html as lxmlHTML
from typing_extensions import override

from juriscraper.opinions.united_states.state import texapp


class Site(texapp.Site):
    """Gets opinions from the court's "Released Orders/Opinions" pages,
    for courts whose opinions the Document Search does not return

    Each case is still parsed from its case page because some courts do
    not link the opinion PDF on the release page, and the release page
    does not tell the opinion types of a cluster apart. See
    https://search.txcourts.gov/Docket.aspx?coa=coa08&FullDate=02/18/2026
    """

    release_dates_xpath = (
        "//table[contains(@id, 'grdDocketDates')]//a[normalize-space()]"
    )
    decided_rows_xpath = (
        "//table[contains(@class, 'rgMasterTable')]"
        "[contains(@id, '_grdDocket_') or contains(@id, '_grdDocket2_')]"
        "/tbody/tr[not(@class='rgNoRecords')]"
    )

    @override
    async def _process_html(self) -> None:
        if self.html is None:
            return None

        authors = {}
        for op_date, url in await self.get_release_dates(self.html):
            html = await self._get_page(url)
            for row in html.xpath(self.decided_rows_xpath):
                authors.update(self.get_authors(row))
                case_link = row.xpath("td[1]/a")[0]
                await self.add_case(
                    case_link.get("href"),
                    op_date,
                    case_link.text_content().strip(),
                    self.get_panel(row),
                )

        # A case's opinions may be listed in later rows, so authors are
        # matched once all rows are read
        for case in self.cases:
            for opinion in case["sub_opinions"]:
                opinion.update(
                    authors.get(self.get_media_id(opinion["url"]), {})
                )

    @staticmethod
    def clean_judge_name(name: str) -> str:
        """Removes titles such as "Senior Chief Justice" from a judge name

        :param name: judge name as shown on the release page
        :return: judge name without titles
        """
        titles = r"(?:(?:Senior|Former|Visiting|Retired|Chief) )*(?:Justice|Judge)|Honorable|Hon\.|Retired"
        return re.sub(
            rf"^(?:{titles}) |, (?:{titles})$", "", " ".join(name.split())
        )

    def get_panel(self, row: lxmlHTML.HtmlElement) -> str:
        """Gets the panel of a release page row; some courts leave it empty

        :param row: release page row
        :return: judge names separated by "; "
        """
        return "; ".join(
            self.clean_judge_name(name)
            for name in row.xpath("td[4]//text()[normalize-space()]")
        )

    def get_authors(self, row: lxmlHTML.HtmlElement) -> dict[str, dict]:
        """Gets author and per curiam of each document of a release page row

        Documents are keyed by MediaID, which the case page links share

        :param row: release page row
        :return: {MediaID: {"author": ..., "per_curiam": True}}
        """
        authors = {}
        for document in row.xpath(
            "td[1]//tr[td/a[contains(@href, 'MediaID=')]]"
        ):
            label = " ".join(document.xpath("string(td[1])").split())
            values = {}
            if " by " in label:
                values["author"] = self.clean_judge_name(
                    label.split(" by ")[-1]
                )
            if "per curiam" in label.lower():
                values["per_curiam"] = True
            media_id = self.get_media_id(document.xpath("td/a/@href")[0])
            authors[media_id] = values
        return authors

    @staticmethod
    def get_media_id(url: str) -> str:
        """Gets the MediaID that identifies an opinion document

        :param url: SearchMedia.aspx url
        :return: MediaID, or "" if missing
        """
        return parse_qs(urlparse(url).query).get("MediaID", [""])[0]

    async def get_release_dates(
        self, index: lxmlHTML.HtmlElement
    ) -> list[tuple[str, str]]:
        """Gets the release dates in range from the index pages

        :param index: HTML object of the index page
        :return: list of (date, url of the release date page) tuples
        """
        shown_quarter = self.get_shown_quarter(index)
        if self.test_mode_enabled():
            quarters = [shown_quarter]
        else:
            quarters = self.get_quarters(self.start_date, self.end_date)

        release_dates = []
        for quarter in quarters:
            if quarter == shown_quarter:
                html = index
            else:
                html = await self.get_index_page(index, quarter)

            for link in html.xpath(self.release_dates_xpath):
                op_date = link.text_content().strip()
                day = datetime.strptime(op_date, "%m/%d/%Y").date()
                if self.test_mode_enabled() or (
                    self.start_date <= day <= self.end_date
                ):
                    release_dates.append((op_date, link.get("href")))

        return release_dates

    async def get_index_page(
        self, index: lxmlHTML.HtmlElement, quarter: date
    ) -> lxmlHTML.HtmlElement:
        """Submits the index page form to get the release dates of a quarter

        :param index: HTML object of the index page
        :param quarter: first day of the quarter
        :return: HTML object of the index page of the quarter
        """
        self.parameters = {
            hidden.get("name"): hidden.get("value", "")
            for hidden in index.xpath("//input[@type='hidden'][@name]")
        }
        self.parameters.update(
            {
                "ctl00$ContentPlaceHolder1$ddlYear": str(quarter.year),
                "ctl00$ContentPlaceHolder1$ddlQuarter": quarter.strftime(
                    "%m-%d-"
                ),
                "ctl00$ContentPlaceHolder1$btnSearch": "Refresh",
            }
        )
        self.method = "POST"
        return await self._download()

    @staticmethod
    def get_shown_quarter(html: lxmlHTML.HtmlElement) -> date:
        """Gets the quarter shown on the index page

        :param html: HTML object of the index page
        :return: first day of the quarter
        """
        year = html.xpath(
            "string(//select[contains(@name, 'ddlYear')]/option[@selected]/@value)"
        )
        quarter = html.xpath(
            "string(//select[contains(@name, 'ddlQuarter')]/option[@selected]/@value)"
        )
        return datetime.strptime(f"{quarter}{year}", "%m-%d-%Y").date()

    @staticmethod
    def get_quarters(start: date, end: date) -> list[date]:
        """Gets the quarters from `start` to `end`, newest first

        :param start: start date
        :param end: end date
        :return: first day of each quarter
        """
        first = date(start.year, 3 * ((start.month - 1) // 3) + 1, 1)
        quarter = date(end.year, 3 * ((end.month - 1) // 3) + 1, 1)
        quarters = []
        while quarter >= first:
            quarters.append(quarter)
            quarter -= relativedelta(months=3)

        return quarters
