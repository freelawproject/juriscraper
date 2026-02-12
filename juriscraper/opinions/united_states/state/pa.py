"""
Scraper for Pennsylvania Supreme Court
CourtID: pa
Court Short Name: pa
"""

import re
from datetime import date, datetime, timedelta
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.ClusterSite import ClusterSite
from juriscraper.lib.type_utils import OpinionType


class Site(ClusterSite):
    court = "Supreme"
    base_url = "https://www.pacourts.us/api/opinion?"
    document_url = "https://www.pacourts.us/assets/opinions/{}/out/{}"
    days_interval = 1
    api_dt_format = "%Y-%m-%dT00:00:00-05:00"
    first_opinion_date = datetime(1998, 4, 27)
    judge_key = "AuthorCode"
    regional_cite_regex = re.compile(r"\d{1,3} A\.3d \d+")
    post_type_key = "PostingTypeId"

    def __init__(self, *args, **kwargs):
        """About postTypes values in self.params


        mo = majority opinion
        pco = per curiam order
        co = concurring opinion
        cs = concurring statement
        cds = concurring and dissenting statement
        do = dissenting opinion
        ds = dissenting statement
        oaj = opinion announcing judgement of the court
        rv = Evenly Divided Court, Reversal
        dedc = Dismissal, Evenly Divided Court
        """
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.regex = re.compile(r"(.*)(?:[,-]?\s+Nos?\.)(.*)")
        self.status = "Published"

        now = datetime.now()
        start = now - timedelta(days=1)
        self.params = {
            "startDate": start.strftime(self.api_dt_format),
            "endDate": now.strftime(self.api_dt_format),
            "courtType": self.court,
            "postTypes": "cd,cds,co,cs,dedc,do,ds,mo,oaj,pco,rv,sd",
            "sortDirection": "-1",
        }
        self.url = f"{self.base_url}{urlencode(self.params)}"
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """Parses data into case dictionaries

        Note that pages returned have no pagination

        :return: None
        """
        json_response = self.html

        for cluster in json_response["Items"]:
            title = cluster["Caption"]
            name, docket = self.parse_case_title(title)
            # A.3d cites seem to exist only for pasuperct
            cite = ""
            if cite_match := self.regional_cite_regex.search(title):
                cite = cite_match.group(0)

            parsed_cluster = {
                "date": cluster["DispositionDate"].split("T")[0],
                "name": name,
                "docket": docket,
                "citation": cite,
                "sub_opinions": [],
                "judge": "",
            }

            for op in cluster["Postings"]:
                post_type = op.get("PostType", {}).get(self.post_type_key, "")
                opinion_type = self.get_type(post_type, cluster)

                status = self.get_status(op)
                if not parsed_cluster.get("status"):
                    parsed_cluster["status"] = status

                per_curiam = False
                author_str = ""
                if op["Author"]:
                    author_str = self.clean_judge(op["Author"][self.judge_key])
                    if author_str.lower() == "per curiam":
                        author_str = ""
                        per_curiam = True
                    else:
                        if author_str not in parsed_cluster["judge"]:
                            parsed_cluster["judge"] += f"; {author_str}"
                elif "per curiam" in post_type.lower():
                    per_curiam = True

                url = self.document_url.format(self.court, op["FileName"])
                parsed_cluster["sub_opinions"].append(
                    {
                        "url": url,
                        "author": author_str,
                        "per_curiam": per_curiam,
                        "type": opinion_type.value,
                    }
                )

            self.cases.append(parsed_cluster)

        if not self.test_mode_enabled() and json_response.get("HasNext"):
            next_page = json_response["PageNumber"] + 1
            logger.info("Paginating to page %s", next_page)
            self.params["pageNumber"] = next_page
            self.url = f"{self.base_url}{urlencode(self.params)}"
            self.html = self._download()
            self._process_html()

    def parse_case_title(self, title: str) -> tuple[str, str]:
        """Separates case_name and docket_number from case string

        :param title: string from the source

        :return: A tuple with the case name and docket number
        """
        search = self.regex.search(title)
        if search:
            name = search.group(1)
            docket = search.group(2)
        else:
            name = title
            docket = ""
        return name, docket

    def get_status(self, op: dict) -> str:
        """Get status from opinion json.
        Inheriting classes have status data

        :param op: opinion json
        :return: parsed status
        """
        return self.status

    def clean_judge(self, author_str: str) -> str:
        """Cleans judge name. `pa` has a different format than
        `pasuperct` and `pacommwct`
        """
        return author_str

    def get_type(self, post_type: str, cluster: dict) -> str:
        """Parse the PostingType into one of our Opinion.type values

        :param post_type: type as returned by the source
        :param cluster: the cluster data returned by the source
        :return: the parsed type
        """
        is_single_opinion = len(cluster["Postings"]) == 1

        if (
            post_type in ["Opinion Per Curiam", "Per Curiam Order"]
            and is_single_opinion
        ):
            type = OpinionType.UNANIMOUS
        elif post_type in [
            "Concurring Opinion",
            "Concurrent Statement",
            "Concurring Statement",
            "Concurring Memorandum",
            "Concurring Memorandum Statement",
        ]:
            type = OpinionType.CONCURRENCE
        elif post_type in [
            "Dissenting Opinion",
            "Dissenting Statement",
            "Dissenting Memorandum",
            "Dissenting Memorandum Statement",
        ]:
            type = OpinionType.DISSENT
        elif post_type in [
            "Concurring and Dissenting Opinion",
            "Concurring and Dissenting Statement",
            "Concurring and Dissenting Memorandum",
            "Concurring and Dissenting Memorandum Statement",
        ]:
            type = OpinionType.CONCURRING_IN_PART_AND_DISSENTING_IN_PART
        elif (
            post_type
            in [
                "Majority Opinion",
                "Opinion Announcing the Judgment of the Court",
                "Opinion",
            ]
            or not is_single_opinion
        ):
            type = OpinionType.MAJORITY
        else:
            logger.error(
                "`pa`: unmapped opinion type %s",
                post_type,
                extra={"scraped_cluster": cluster},
            )
            # default value in CL
            type = OpinionType.COMBINED

        return type

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract citations from text

        Be careful with citations referring to other opinions that are
        mentioned before the actual citation

        See, for example:
        https://ojd.contentdm.oclc.org/digital/api/collection/p17027coll5/id/28946/download
        """
        # For each line, keep only the part after the last colon
        cleaned_text = "\n".join(
            line.rsplit(":", 1)[-1] if ":" in line else line
            for line in scraped_text.splitlines()
        )

        pattern = re.compile(
            r"""
                    (?:
                        review\s+from\s+the\s+
                        |Order\s+of(?:\s+the)?\s+
                        |Appeal\s+from\s+the(?:\s[Oo]rder\s+of\s+the)?\s+
                     )
                    (?P<lower_court>.*?)(?=\s*(?:\.|at|entered|Order|,))
                    """,
            re.X | re.DOTALL,
        )
        result = {}
        if match := pattern.search(cleaned_text):
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()

            if lower_court in ["Superior Court", "Commonwealth Court"]:
                lower_court = "Pennsylvania " + lower_court

            result["Docket"] = {"appeal_from_str": lower_court}

        return result

    def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Modify GET querystring for desired date range

        :param dates: (start_date, end_date) tuple
        :return None
        """
        start, end = dates
        self.params["startDate"] = start.strftime(self.api_dt_format)
        self.params["endDate"] = end.strftime(self.api_dt_format)
        self.url = f"{self.base_url}{urlencode(self.params)}"
        logger.info("Backscraping for range %s %s", *dates)
        self.html = self._download()
        self._process_html()
