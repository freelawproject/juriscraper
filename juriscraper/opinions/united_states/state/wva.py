import datetime
import math
import re
from urllib.parse import urljoin

from dateutil import parser

from juriscraper.AbstractSite import logger
from juriscraper.ClusterSite import ClusterSite
from juriscraper.lib.type_utils import OpinionType


class Site(ClusterSite):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = urljoin(self.base_url, self.opinions_path)
        self.court_id = self.__module__
        self.cluster_by_date_max_days = 15
        self.seen_urls = set()
        self.make_backscrape_iterable(kwargs)

    def _process_html(self):
        for row in self.html.xpath("//tr[td[@headers]]"):
            name_cell = row.xpath("td[3]")[0]
            # Replace <br> with space to avoid merged words
            for br in name_cell.iter("br"):
                br.tail = " " + (br.tail or "")
            name = name_cell.text_content().strip()
            # Strip "et al." early so names match for clustering
            name = re.sub(r",?\s+et\.?\s*al\.?", "", name)

            # Strip "(Separate Included)" from case name
            name = name.replace("(Separate Included)", "").strip()

            decision_type = row.xpath("td[5]/text()")[0]
            case_dict = self.get_metadata(name, decision_type)

            url = row.xpath("td[3]/a/@href")[0]
            # Skip duplicates from pagination overlap
            if url in self.seen_urls:
                continue
            self.seen_urls.add(url)

            case_type = row.xpath("td[4]/text()")[0].strip()
            case_dict.update(
                {
                    "date": row.xpath("td[1]/text()")[0].strip(),
                    "docket": row.xpath("td[2]/text()")[0].strip(),
                    "url": url,
                    "nature_of_suit": self.codes.get(case_type, ""),
                }
            )
            if cluster := self.cluster_opinions(case_dict, self.cases):
                # accumulate judges
                if case_dict.get("judge"):
                    cluster["judge"] += f"; {case_dict['judge']}"

                # Date corrections. See 'Todd Jarell' case on example files
                if case_dict["date"] == cluster["date"]:
                    continue

                cluster_date = parser.parse(cluster["date"])
                case_date = parser.parse(case_dict["date"])

                if cluster_date > case_date:
                    cluster["other_date"] = (
                        f"Some opinions were filed on {cluster['date']};"
                    )
                    cluster["date"] = case_dict["date"]
                else:
                    cluster["other_date"] = (
                        f"Some opinions were filed on {case_dict['date']};"
                    )
            else:
                self.cases.append(case_dict)

    def get_metadata(self, name: str, decision_type: str) -> dict[str, str]:
        """Parses Opinion and Cluster values out of the raw data

        Gets opinion type, status, per curiam, author, judges, joined by, and may modify the name

        :param name: raw name
        :param decision type: the source decision type
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
            if match := self.author_and_type_regex.search(name):
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

                if matches := re.finditer(
                    r"(Justice|Judge) (?P<judge>[A-Z][a-z]+)", value
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

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """The prior-terms page only filters by year. We iterate
        by year and paginate through all pages for each year.

        Accepts backscrape_start/end in "%Y/%m/%d" format.
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        if start:
            start = datetime.datetime.strptime(start, "%Y/%m/%d").date()
        else:
            start = self.first_opinion_date

        if end:
            end = datetime.datetime.strptime(end, "%Y/%m/%d").date()
        else:
            end = datetime.date.today()

        self.back_scrape_iterable = list(range(start.year, end.year + 1))

    async def _download_backwards(self, year: int) -> None:
        logger.info("Backscraping %s for year %s", self.court_id, year)
        self.url = urljoin(self.base_url, self.prior_terms_path)
        self.request["parameters"]["params"] = {
            self.year_param: year,
        }

        self.html = await self._download()

        # Get total opinion count to compute page count
        total_text = self.html.xpath(
            "string(//div[contains(@class, 'view-header')]//h5)"
        )
        if match := re.search(r"Total Opinions:\s*(\d+)", total_text):
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
