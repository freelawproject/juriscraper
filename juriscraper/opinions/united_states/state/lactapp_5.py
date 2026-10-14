import re
from datetime import datetime
from typing import Literal

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.exceptions import BotChallengeError, ParsingException
from juriscraper.lib.string_utils import CaseNameTweaker, titlecase
from juriscraper.lib.type_utils import RawOpinion
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    id_to_case_mapper: dict[
        str,
        Literal[
            "name",
            "docket",
            "judge",
            "lower_court_number",
            "lower_court",
            "attorney",
        ],
    ] = {
        "lblCaseTitle": "name",
        "lblCaseNum": "docket",
        "lblRulingJudge": "judge",
        "lblDistrictCourtNo": "lower_court_number",
        "lblLowerCourt": "lower_court",
        "lblAttorney": "attorney",
    }
    date_regex = re.compile(r"\d{2}/\d{2}/\d{4}")
    panel_prefix = "cntBody_ctlOpinions"
    count_xpath = f"//span[@id='{panel_prefix}_lblRecordCnt']"
    row_xpath = (
        "//tr[.//span[starts-with(@id, "
        f"'{panel_prefix}_rptCaseSearch_lblCaseNum')]]"
    )

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.fifthcircuit.org/"
        self.status = "Unknown"

        # Kwargs from backscrape callers
        if bool(
            {"backscrape_start", "backscrape_end", "days_interval"}
            & set(kwargs)
        ):
            raise NotImplementedError(
                f"{self.court_id} has no backscraper. Only the reCaptcha "
                "protected search form can filter opinions by date"
            )

    @override
    async def _process_html(self) -> None:
        self.check_panel_is_present()

        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath(self.row_xpath)
        for row in rows:
            fixed_values: RawOpinion = {}
            for id_part, key in self.id_to_case_mapper.items():
                element: list[HtmlElement] = row.xpath(
                    f".//*[contains(@id, '{id_part}')]"
                )
                if bool(element):
                    fixed_values[key] = element[0].text_content().strip()

            name = fixed_values.get("name")
            if not bool(name):
                logger.warning(
                    "%s: no case title for docket %s; skipping row",
                    self.court_id,
                    fixed_values.get("docket"),
                )
                continue

            fixed_values["name"] = titlecase(name)
            if bool(judge := fixed_values.get("judge")):
                fixed_values["judge"] = re.sub(r"Hon\.[\s\n]+", "", judge)

            hearing = self.get_hearing_info(row)
            rehearing_application = self.get_rehearing_application(row)

            # Cases can have more than 1 opinion document
            anchors: list[HtmlElement] = row.xpath(
                ".//a[contains(@id, 'HyperLink_')]"
            )
            for anchor in anchors:
                disposition = ""
                case_date = ""
                disp_container: list[str] = anchor.xpath(
                    "following-sibling::text()"
                )
                if bool(disp_container):
                    disposition = disp_container[0].strip()

                    if (
                        date_match := self.date_regex.search(disposition)
                    ) is not None:
                        case_date = date_match.group(0)
                        disposition = disposition.rsplit(" on ", 1)[0].strip(
                            " '"
                        )

                if not bool(case_date):
                    logger.error(
                        "%s: no date in disposition %r for docket %s; "
                        "skipping document %s",
                        self.court_id,
                        disposition,
                        fixed_values.get("docket"),
                        anchor.attrib["href"],
                    )
                    continue

                other_dates = [hearing]
                label: list[str] = anchor.xpath(
                    "preceding-sibling::b[1]/text()"
                )
                if bool(label) and label[0].strip().startswith("Rehearing"):
                    other_dates.append(rehearing_application)

                case: RawOpinion = {
                    "url": anchor.attrib["href"],
                    "disposition": disposition,
                    "date": case_date,
                    "other_date": "; ".join(filter(None, other_dates)),
                    **fixed_values,
                }

                self.cases.append(case)

    def is_valid_date(self, text: str) -> bool:
        """Check that `text` holds a real MM/DD/YYYY date

        :param text: the text to search
        :return: True if the first date-like string parses
        """
        if (match := self.date_regex.search(text)) is None:
            return False
        try:
            datetime.strptime(match.group(0), "%m/%d/%Y")
        except ValueError:
            return False
        return True

    def get_hearing_info(self, row: HtmlElement) -> str:
        """Get the "Court Hearing Info" of a case row

        :param row: the case row element
        :return: the hearing info, or an empty string if it has no valid date
        """
        element: list[HtmlElement] = row.xpath(
            ".//span[contains(@id, '_Label2_')]"
        )
        if not bool(element):
            return ""
        text = re.sub(r"\s+", " ", element[0].text_content()).strip()
        if not self.is_valid_date(text):
            return ""
        # "Oral Argument: No" means the case was submitted on briefs, so the
        # flag is kept to avoid reading the date as an argument date
        text = re.sub(r"\s*Oral Argument:", ", Oral Argument:", text)
        return f"Court Hearing Info: {text}"

    def get_rehearing_application(self, row: HtmlElement) -> str:
        """Get the "Application for Rehearing" date of a case row

        :param row: the case row element
        :return: the application text, or an empty string if it has no
            valid date
        """
        label: list[HtmlElement] = row.xpath(
            ".//b[starts-with(normalize-space(), 'Application for Rehearing')]"
        )
        if not bool(label):
            return ""
        text = f"{label[0].text_content().strip()} {(tail_value if (tail_value := label[0].tail) is not None else '').strip()}"
        if not self.is_valid_date(text):
            return ""
        return text

    def check_panel_is_present(self) -> None:
        """Check that the "Latest Decisions" panel returned decisions.

        :raises BotChallengeError: when the page serves a captcha challenge
        :raises ParsingException: when the panel is missing or empty
        """
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        if bool(self.html.xpath("//*[contains(@class, 'h-captcha')]")) or bool(
            self.html.xpath("//title[contains(., 'Bot Manager Captcha')]")
        ):
            raise BotChallengeError(
                f"{self.court_id}: served a captcha challenge instead of the homepage",
                fingerprint=[f"{self.court_id}-bot-challenge"],
            )
        count: list[HtmlElement] = self.html.xpath(self.count_xpath)
        if not bool(count):
            raise ParsingException(
                f"{self.court_id}: no 'Latest Decisions' record count on "
                f"{self.url}; the page layout may have changed"
            )

        logger.info(count[0].text_content().strip())
        if not bool(self.html.xpath(self.row_xpath)):
            raise ParsingException(
                f"{self.court_id}: the 'Latest Decisions' panel on {self.url} "
                "has no rows"
            )
