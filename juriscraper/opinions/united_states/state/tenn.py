"""
Scraper for the Supreme Court of Tennessee
CourtID: tenn
Court Short Name: Tenn.
"""

import re
from datetime import date, datetime
from urllib.parse import urljoin

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.ClusterSite import ClusterSite
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import (
    ExtractedMetadata,
    OpinionType,
    RawOpinion,
)


class Site(ClusterSite[tuple[date, date]]):
    first_opinion_date = datetime(1993, 1, 22)
    days_interval = 7

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.url = "https://www.tncourts.gov/courts/supreme-court/opinions"
        self.court_id = self.__module__
        self.status = "Unknown"
        self.should_have_results = True
        self.make_backscrape_iterable(kwargs)

        # we got this UA whitelisted #1689
        self.request["headers"] = {"User-Agent": "Juriscraper"}
        self.needs_special_headers = True

        self.section_selector = "views-field-field-opinions-case-number"
        # the docket will be the first no empty floating text in the "section"
        self.docket_xpath = ".//p/text()[normalize-space()]"

    @override
    def _process_html(self) -> None:
        """
        Parse the HTML table rows and extract case details.

        Iterates over each table row in the HTML, extracting the date, URL, case name,
        docket number, judge, lower court judge, summary, per curiam status, and opinion type.
        Appends a dictionary with these details to self.cases.
        """
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath("//tr")
        for row in rows:
            date: str = (
                row.xpath(
                    ".//td[contains(@class, 'views-field-field-opinions-date-filed')]"
                )[0]
                .text_content()
                .strip()
            )
            section: HtmlElement = row.xpath(
                f".//td[contains(@class, '{self.section_selector}')]"
            )[0]
            url = section.findall(".//a")[0].attrib["href"]

            summary = self.get_summary(section)
            # prevent picking up one of the judge containers
            if "Judge:" in summary:
                summary = ""

            name_text = section.findall(".//a")[0].text_content()
            name, opinion_type = self.extract_type(name_text, summary)

            # may be empty
            lower_court_judges: list[str] = section.xpath(
                ".//text()[contains(., 'Trial Court Judge:')]"
            )
            lower_court_judge = (
                lower_court_judges[0].split(":", 1)[1].strip()
                if bool(lower_court_judges)
                else ""
            )

            judge: str = (
                section.xpath(".//text()[contains(., 'Authoring Judge:')]")[0]
                .strip()
                .split(":", 1)[1]
                .strip()
            )
            per_curiam = False
            if "curiam" in judge.lower():
                judge = ""
                per_curiam = True

            case_dict: RawOpinion = {
                "date": date,
                "url": url,
                "name": name.strip(),
                "docket": section.xpath(self.docket_xpath)[0].strip(),
                "judge": judge,
                "author": judge,
                "lower_court_judge": lower_court_judge,
                "summary": summary,
                "per_curiam": per_curiam,
                "type": opinion_type,
            }

            # attempt to merge with previous cases
            if bool(cluster := self.cluster_opinions(case_dict, self.cases)):
                # add to the cluster
                cluster["judge"] = (
                    f"{(judge_value if (judge_value := cluster.get('judge')) is not None else '')}; {judge}"
                )
                logger.info("Clustered opinions into %s", self.cases[-1])
                continue

            self.cases.append(case_dict)

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Extract precedential_status and appeal_from_str from scraped text.

        :param scraped_text: Text of the scraped content
        :return: dictionary with precedential_status and appeal_from_str
        """
        lower_court = self.extract_lower_court_name(scraped_text)
        precedential_status = (
            "Published"
            if "MEMORANDUM OPINION" not in scraped_text
            else "Unpublished"
        )
        result: ExtractedMetadata = {
            "OpinionCluster": {"precedential_status": precedential_status}
        }
        if bool(lower_court):
            result["Docket"] = {"appeal_from_str": lower_court}
        return result

    def extract_lower_court_name(self, text: str) -> str:
        """Extract the lower court name from the provided opinion text.

        Sometimes there is no introductory cue for the lower court. In that
        case, it's usually between the case name that contains a "v." and the
        docket number "No."
        That's what the third pattern is for

        :param text: the opinion's extracted text
        :return: the lower court or an empty string
        """

        patterns = [
            r"Appeal by Permission from.+\n(.+)\n",
            r"Appeal from the (.+)",
            r".+\bv\..+\n(?P<lower_court>.*(\n.*)?)\n.+No\.",
        ]

        for pattern in patterns:
            match = re.search(pattern, text[:1000])
            if match is not None:
                return match.group(1).strip()

        return ""

    def extract_type(self, raw_name: str, summary: str) -> tuple[str, str]:
        """
        Find the opinion type if it exists and clean it out fo the name

        See edge cases:
            "In Re: Winston Bradshaw Sitton, BPR#018440 - Concurring in Section III, not joining in Sections I and II"
            "State of Tennessee v. Jerome Antonio McElrath - Concurring In the suppression of evidence; dissenting from the adoption of an exclusionary rule exception for constitutional violations caused by careless police recordkeeping"

        Be careful when cleaning out the name. See example:
            "State of Tennessee v. Tabitha Gentry (AKA ABKA RE BAY)"

        :param raw_name: full name including opinion type
        :param summary: summary of the opinion
        :return: (Standardized type string from types_mapping, name cleaned of the type)
        """
        # everything between a dash or parenthesis and the end of the string
        type_regex = re.compile(r"(- |\().+?\)?$")
        type_string = ""
        if (match := type_regex.search(raw_name)) is not None:
            type_string = match.group(0)
        lower_type = type_string.lower()

        # Use specific patterns to avoid false positives like "concurrent"
        # Match "concurring" or "concurrence" but not "concurrent"
        concur = "concur" in lower_type or re.search(
            r"\bconcur(?:ring|rence|s)?\b", summary, re.IGNORECASE
        )
        dissent = "dissent" in lower_type or re.search(
            r"\bdissent(?:ing|s)?\b", summary, re.IGNORECASE
        )
        not_join = "not join" in lower_type

        op_type = ""
        if (
            "in part" in lower_type
            or (bool(concur) and bool(dissent))
            or (bool(concur) and not_join)
        ):
            op_type = OpinionType.CONCURRING_IN_PART_AND_DISSENTING_IN_PART
        elif bool(concur):
            op_type = OpinionType.CONCURRENCE
        elif bool(dissent):
            op_type = OpinionType.DISSENT

        # if no type was found, set it to Majority but do not edit the name
        if not bool(op_type):
            return raw_name, OpinionType.MAJORITY.value

        # delete the type string
        if match is not None:
            logger.debug(
                "Deleting '%s' from case name '%s'", match.group(0), raw_name
            )
            raw_name = raw_name[: match.start()].strip()

        return raw_name, op_type.value

    @override
    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        r"""Download cases within a given date range.

        :param dates: Tuple containing the start and end dates \(`date`, `date`\) for the query.
        :return None:
        """
        start, end = dates
        self.url = urljoin(
            (self.url if self.url is not None else ""),
            f"?field_opinions_date_filed={start.strftime('%Y-%m-%d')}&field_opinions_date_filed_1={end.strftime('%Y-%m-%d')}",
        )
        self.html = await self._download()
        self._process_html()

    def get_summary(self, section: HtmlElement) -> str:
        """Get the summary

        :param section: the html element containing the case summary
        :return the parsed summary
        """
        # the summary will be the last non empty p or p/span
        summary_container = section.findall(".//p")

        summary = summary_container[-1].text_content().strip()
        if not bool(summary):
            summary = summary_container[-2].text_content()

        # text inside may be separated by <br> tags
        summary = re.sub(r"\s+", " ", summary)

        return summary
