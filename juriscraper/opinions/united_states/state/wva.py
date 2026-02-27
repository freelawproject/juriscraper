import re

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

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("verify", False)
        super().__init__(*args, **kwargs)
        self.url = "https://www.courtswv.gov/appellate-courts/supreme-court-of-appeals/opinions/prior-terms"
        self.court_id = self.__module__
        self.cluster_by_date_max_days = 15

    def _process_html(self):
        for row in self.html.xpath("//tr[td[@headers]]"):
            name = row.xpath("string(td[3])").strip()
            decision_type = row.xpath("td[5]/text()")[0]
            case_dict = self.get_metadata(name, decision_type)

            case_type = row.xpath("td[4]/text()")[0].strip()
            case_dict.update(
                {
                    "date": row.xpath("td[1]/text()")[0].strip(),
                    "docket": row.xpath("td[2]/text()")[0].strip(),
                    "url": row.xpath("td[3]/a/@href")[0],
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
