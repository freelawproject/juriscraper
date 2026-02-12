# Author: Michael Lissner
# Date created: 2013-05-23

import re
from datetime import date, datetime

from juriscraper.ClusterSite import ClusterSite
from juriscraper.lib.date_utils import unique_year_month
from juriscraper.lib.log_tools import make_default_logger
from juriscraper.lib.type_utils import OpinionType

logger = make_default_logger()


class Site(ClusterSite):
    first_opinion_date = datetime(2010, 1, 1)
    days_interval = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = (
            "https://www.courts.state.hi.us/opinions_and_orders/opinions"
        )
        self.court_id = self.__module__
        self.court_code = "S.Ct"
        self.status = "Published"
        self.should_have_results = True
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """Parse HTML into case objects

        :return: None
        """
        for row in self.html.xpath("//tr[@class='row-']"):
            (
                date,
                court,
                docket_container,
                name_container,
                lower_court,
                citation,
            ) = row.xpath(".//td")
            if court.text_content() != self.court_code:
                logger.debug("Skipping row not matching %s", self.court_code)
                continue

            if not docket_container.xpath(".//a"):
                continue

            lower_court = lower_court.text_content()
            if lower_court == "Original Proceeding":
                lower_court = ""

            name_text = name_container.text_content().strip()
            last_period_regex = (
                r", Dated|(?<!v)(?<!Jr)(?<!U\.S)(?<! [A-Z])\.(?! Inc\.)"
            )

            if "(" in name_text:
                case_name = name_text.split("(", 1)[0].strip()
            else:
                if v_match := re.search(r" v\. ", name_text):
                    post_v = name_text[v_match.end() :]
                    case_name = (
                        name_text[: v_match.end()]
                        + re.split(last_period_regex, post_v, maxsplit=1)[
                            0
                        ].strip()
                    )
                else:
                    case_name = re.split(
                        last_period_regex, name_text, maxsplit=1
                    )[0].strip()

            docket = (
                docket_container.text_content()
                .strip()
                .split("\t")[0]
                .split()[0]
            )
            case_dict = {
                "date": date.text_content(),
                "name": case_name,
                "docket": docket,
                "lower_court": lower_court,
                "citation": citation.text_content(),
            }

            main_url = docket_container.xpath(".//a")[0].get("href")
            sub_opinions = []
            judges = ""

            # the text describing the opinion type will be inside the links
            links = name_container.xpath(".//a")
            for link_index, link in enumerate(links):
                link_text = link.text_content()
                lower_link_text = link_text.strip().lower()
                dissent = "dissent" in lower_link_text
                concurrence = "concur" in lower_link_text

                op_type = None
                if dissent and concurrence:
                    op_type = (
                        OpinionType.CONCURRING_IN_PART_AND_DISSENTING_IN_PART
                    )
                elif concurrence:
                    op_type = OpinionType.CONCURRENCE
                elif dissent:
                    op_type = OpinionType.DISSENT

                if not op_type:
                    continue

                author = ""
                # start at this link's text; end at the next link's text
                # Author and joined by should be in this interval
                start_text_index = name_text.find(link_text)

                if link_index + 1 == len(links):
                    end_text_index = len(name_text)
                else:
                    end_text_index = name_text.find(
                        links[link_index + 1].text_content(), start_text_index
                    )

                judges_text = name_text[start_text_index:end_text_index]

                if author_match := re.search(
                    r"by ([CJ.]+ )?(?P<author>\w+)", judges_text
                ):
                    author = author_match.group("author")
                    judges += f"; {author}"

                joined_by = ""
                if joined_by_match := re.search(
                    r"in which (?P<joined_by>.+)[jJ]oins", judges_text
                ):
                    joined_by = joined_by_match.group("joined_by").strip()
                    judges += f"; {joined_by}"

                sub_opinions.append(
                    {
                        "url": link.attrib["href"],
                        "type": op_type.value,
                        "author": author,
                        "joined_by": joined_by,
                    }
                )

            if sub_opinions:
                sub_opinions.append(
                    {"url": main_url, "type": OpinionType.MAJORITY.value}
                )
                case_dict["sub_opinions"] = sub_opinions

                if judges:
                    case_dict["judge"] = judges.strip("; ")
            else:
                case_dict["url"] = main_url

            self.cases.append(case_dict)

    def _download_backwards(self, search_date: date) -> None:
        """Download and process HTML for a given target date.

        :param search_date (date): The date for which to download and process opinions.
        :return None; sets the target date, downloads the corresponding HTML
        and processes the HTML to extract case details.
        """

        self.request["parameters"]["params"] = {
            "yr": search_date.year,
            "mo": f"{search_date.month:02d}",
        }
        logger.info(
            "Now downloading case page at: %s (params: %s)"
            % (self.url, self.request["parameters"]["params"])
        )
        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs) -> None:
        """Make back scrape iterable

        :param kwargs: the back scraping params
        :return: None
        """
        super().make_backscrape_iterable(kwargs)
        self.back_scrape_iterable = unique_year_month(
            self.back_scrape_iterable
        )
