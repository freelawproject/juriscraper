import datetime
import math
import re
from urllib.parse import urljoin

from dateutil import parser
from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.ClusterSite import ClusterSite
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import (
    BackscrapeOptions,
    OpinionType,
    RawOpinion,
)


class Site(ClusterSite[int]):
    """
    About decision types

    MD:
    An abbreviated decision on the merits of a case. Memorandum decisions do
    not contain a syllabus and are not published in the West Virginia Reports.
    Memorandum decisions may be cited in any court or administrative tribunal.
    See Rule 21, Revised Rules of Appellate Procedure.

    SD:
    An opinion that is delivered by one of the Justices on behalf of the Court.
    Signed opinions contain at least one new syllabus point. See Syllabus point
    2, WALKER v. DOE, 210 W.Va. 490, 558 S.E.2d 290 (2001)("This Court will use
    signed opinions when new points of law are announced and those points will
    be articulated through syllabus points as required by our state
    constitution.") Signed opinions are published in the West Virginia Reports.

    PC:
    An opinion that is delivered by the Court as a whole. Per curiam opinions
    do not contain new syllabus points, but instead quote syllabus points from
    prior cases. See Syllabus point 3 and 4, WALKER v. DOE, 210 W.Va. 490, 558
    S.E.2d 290 (2001)("[3] Per curiam opinions have precedential value as an
    application of settled principles of law to facts necessarily differing
    from those at issue in signed opinions. The value of a per curiam opinion
    arises in part from the guidance such decisions can provide to the lower
    courts regarding the proper application of the syllabus points of law
    relied upon to reach decisions in those cases. [4] A per curiam opinion
    may be cited as support for a legal argument.")
    Per curiam opinions are published in the West Virginia Reports.
    """

    codes = {
        "CR-F": "Felony (non-Death Penalty)",
        "CR-M": "Misdemeanor",
        "CR-O": "Criminal-Other",
        "TCR": "Tort, Contract, and Real Property",
        "PR": "Probate",
        "FAM": "Family",
        "JUV": "Juvenile",
        "CIV-O": "Civil-Other",
        "WC": "Workers Compensation",
        "TAX": "Revenue (Tax)",
        "ADM": "Administrative Agency-Other",
        "MISC": "Appeal by Right-Other",
        "OJ-H": "Habeas Corpus",
        "OJ-M": "Writ Application-Other",
        "OJ-P": "Writ Application-Other",
        "L-ADM": "Bar Admis   sion",
        "L-DISC": "Bar Discipline/Eligibility",
        "L-DISC-O": "Bar/Judiciary Proceeding-Other",
        "J-DISC": "Bar/Judiciary Proceeding-Other",
        "CERQ": "Certified Question",
        "OJ-O": "Original Proceeding/Appellate Matter-Other",
        "POST": "Post-Conviction Appeal",
    }

    author_and_type_regex = re.compile(r"\((?P<author_and_type>.+)\)\s*$")

    # 10 results per page, server ignores items_per_page
    results_per_page = 10
    first_opinion_date = datetime.date(1991, 1, 1)
    prior_terms_path = (
        "/appellate-courts/supreme-court-of-appeals/opinions/prior-terms"
    )
    year_param = "field_sca_opinion_year_value"

    base_url = "https://www.courtswv.gov"
    opinions_path = "/appellate-courts/supreme-court-of-appeals/opinions"

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.url = urljoin(self.base_url, self.opinions_path)
        self.court_id = self.__module__
        self.cluster_by_date_max_days = 15
        self.seen_urls = set()
        self.make_backscrape_iterable(kwargs)

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath("//tr[td[@headers]]")
        for row in rows:
            name_cell = row.findall("td[3]")[0]
            # Replace <br> with space to avoid merged words
            for br in name_cell.iter("br"):
                br.tail = " " + (br.tail if br.tail is not None else "")
            name = name_cell.text_content().strip()
            # Strip "et al." early so names match for clustering
            name = re.sub(r",?\s+et\.?\s*al\.?", "", name)

            # Strip "(Separate Included)" from case name
            name = name.replace("(Separate Included)", "").strip()

            decision_type: str = row.xpath("td[5]/text()")[0]
            case_dict = self.get_metadata(name, decision_type)

            url: str = row.xpath("td[3]/a/@href")[0]
            # Skip duplicates from pagination overlap
            if url in self.seen_urls:
                continue
            self.seen_urls.add(url)

            case_type: str = row.xpath("td[4]/text()")[0].strip()
            case_dict.update(
                {
                    "date": row.xpath("td[1]/text()")[0].strip(),
                    "docket": row.xpath("td[2]/text()")[0].strip(),
                    "url": url,
                    "nature_of_suit": self.codes.get(case_type, ""),
                }
            )
            if bool(cluster := self.cluster_opinions(case_dict, self.cases)):
                # accumulate judges
                if bool(judge := case_dict.get("judge")):
                    cluster["judge"] = (
                        f"{(judge_value if (judge_value := cluster.get('judge')) is not None else '')}; {judge}"
                    )

                # Date corrections. See 'Todd Jarell' case on example files
                case_date_value = case_dict.get("date")
                cluster_date_value = cluster.get("date")
                if case_date_value == cluster_date_value:
                    continue

                if not isinstance(cluster_date_value, str) or not isinstance(
                    case_date_value, str
                ):
                    raise TypeError(
                        "Expected date strings from the opinion table."
                    )
                cluster_date = parser.parse(cluster_date_value)
                case_date = parser.parse(case_date_value)

                if cluster_date > case_date:
                    cluster["other_date"] = (
                        f"Some opinions were filed on {cluster_date_value};"
                    )
                    cluster["date"] = case_date_value
                else:
                    cluster["other_date"] = (
                        f"Some opinions were filed on {case_date_value};"
                    )
            else:
                self.cases.append(case_dict)

    def get_metadata(self, name: str, decision_type: str) -> RawOpinion:
        """Parses Opinion and Cluster values out of the raw data

        Gets opinion type, status, per curiam, author, judges, joined by, and may modify the name

        :param name: raw name
        :param decision_type: the source decision type
        :return a parsed case dict
        """
        # defaults
        status = "Published"
        per_curiam = False
        op_type = OpinionType.MAJORITY
        author = ""
        joined_by = ""
        judge = ""

        name = re.sub(r"[\s\n]+", " ", name)

        if "MD" in decision_type:
            status = "Unpublished"
            if "SEP" in decision_type:
                op_type = OpinionType.COMBINED
        elif "PC" in decision_type:
            per_curiam = True
            op_type = OpinionType.UNANIMOUS
        elif "SEP" in decision_type:
            # try to get the op type
            if (match := self.author_and_type_regex.search(name)) is not None:
                name = name[: match.start()].strip(", .")
                value = match.group("author_and_type")
                dissent = "dissent" in value.lower()
                concurrence = "concur" in value.lower()

                if dissent and concurrence:
                    op_type = (
                        OpinionType.CONCURRING_IN_PART_AND_DISSENTING_IN_PART
                    )
                elif dissent:
                    op_type = OpinionType.DISSENT
                elif concurrence:
                    op_type = OpinionType.CONCURRENCE

                if bool(
                    matches := re.finditer(
                        r"(Justice|Judge) (?P<judge>[A-Z][a-z]+)", value
                    )
                ):
                    judges = [i.group("judge") for i in matches]
                    author = judges[0]

                    if len(judges) > 1:
                        joined_by = "; ".join(judges[1:])
                        judge = "; ".join(judges)
                    else:
                        judge = author
            else:
                # see wvactapp
                op_type = OpinionType.CONCURRING_IN_PART_AND_DISSENTING_IN_PART
                logger.warning(
                    "%s: could not find Opinion.type", self.court_id
                )

        return {
            "status": status,
            "type": op_type.value,
            "per_curiam": per_curiam,
            "author": author,
            "joined_by": joined_by,
            "judge": judge,
            "name": name,
        }

    @override
    def make_backscrape_iterable(self, kwargs: BackscrapeOptions) -> None:
        """The prior-terms page only filters by year. We iterate
        by year and paginate through all pages for each year.

        Accepts backscrape_start/end in "%Y/%m/%d" format.
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        if bool(start):
            start = datetime.datetime.strptime(start, "%Y/%m/%d").date()
        else:
            start = self.first_opinion_date

        if bool(end):
            end = datetime.datetime.strptime(end, "%Y/%m/%d").date()
        else:
            end = datetime.date.today()

        self.back_scrape_iterable = list(range(start.year, end.year + 1))

    @override
    async def _download_backwards(self, year: int) -> None:
        logger.info("Backscraping %s for year %s", self.court_id, year)
        self.url = urljoin(self.base_url, self.prior_terms_path)
        self.request["parameters"]["params"] = {
            self.year_param: year,
        }

        self.html = await self._download()

        # Get total opinion count to compute page count
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        totals: list[HtmlElement] = self.html.xpath(
            "//div[contains(@class, 'view-header')]//h5"
        )
        total_text = totals[0].text_content() if bool(totals) else ""
        if (
            match := re.search(r"Total Opinions:\s*(\d+)", total_text)
        ) is not None:
            total = int(match.group(1))
        else:
            logger.warning(
                "%s: could not find total opinions for year %s",
                self.court_id,
                year,
            )
            total = 0

        self._process_html()

        # Paginate through remaining pages
        total_pages = math.ceil(total / self.results_per_page)
        for page in range(1, total_pages):
            self.request["parameters"]["params"]["page"] = page
            self.html = await self._download()
            self._process_html()
