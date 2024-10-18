import re
from datetime import date, datetime

from juriscraper.AbstractSite import logger
from juriscraper.lib.date_utils import unique_year_month
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    id_to_case_mapper = {
        "lblCaseTitle": "name",
        "lblCaseNum": "docket",
        "lblRulingJudge": "judge",
        "lblDistrictCourtNo": "lower_court_number",
        "lblLowerCourt": "lower_court",
        "lblAttorney": "attorney",
    }
    first_opinion_date = datetime(1992, 1, 1)
    days_interval = 28  # ensure a tick for each month
    date_regex = re.compile(r"\d{2}/\d{2}/\d{4}")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.fifthcircuit.org/searchopinions.aspx"
        self.search_is_configured = False
        self.parameters = {
            "ctl00$cntBody$ctlOpinionSearch_Toggle$ddlSearchOptions": "2",
        }
        self.target_date = datetime.today()
        self.make_backscrape_iterable(kwargs)
        self.status = "Unknown"

    def _process_html(self):
        # We need to do a plain GET to get hidden inputs
        # Then we can do our filtered request
        if not self.test_mode_enabled():
            self.method = "POST"

            # We need to set the proper search filter the first time
            if not self.search_is_configured:
                self.update_hidden_inputs()
                self.parameters["__EVENTTARGET"] = (
                    "ctl00$cntBody$ctlOpinionSearch_Toggle$ddlSearchOptions"
                )
                self.html = self._download()
                self.search_is_configured = True

            # Set the proper filters to get the actual data we want
            self.update_date_filters()
            self.update_hidden_inputs()
            self.html = self._download()

        count_xpath = "//*[@id='cntBody_ctlOpinionSearch_Toggle_lblRecordCnt']"
        logger.info(self.html.xpath(count_xpath)[0].text_content().strip())

        for row in self.html.xpath("//tr[.//a[contains(@id, 'HyperLink_')]]"):
            fixed_values = {}
            for id_part, key in self.id_to_case_mapper.items():
                element = row.xpath(f".//*[contains(@id, '{id_part}')]")
                if element:
                    fixed_values[key] = element[0].text_content().strip()

            fixed_values["name"] = titlecase(fixed_values["name"])
            if fixed_values.get("judge"):
                fixed_values["judge"] = re.sub(
                    r"Hon\.[\s\n]+", "", fixed_values["judge"]
                )

            # Some cases have more than 1 opinion document (check example 2)
            # Some cases have no links, they will be ignored by this loop
            for anchor in row.xpath(".//a"):
                # The opinion date is sometimes in the disposition text
                disposition = ""
                case_date = f"{self.target_date.year}/07/01"
                date_filed_is_approximate = True
                if disp_container := anchor.xpath("following-sibling::text()"):
                    disposition = disp_container[0].strip()

                    if date_match := self.date_regex.search(disposition):
                        case_date = date_match.group(0)
                        disposition = disposition.rsplit(" on ", 1)[0].strip(
                            " '"
                        )
                        date_filed_is_approximate = False

                case = {
                    "url": anchor.get("href"),
                    "disposition": disposition,
                    "date": case_date,
                    "date_filed_is_approximate": date_filed_is_approximate,
                    **fixed_values,
                }

                self.cases.append(case)

    def update_hidden_inputs(self) -> None:
        """Parse form values characteristic of aspx sites,
        and put then on self.parameters for POST use
        """
        for input in self.html.xpath('//input[@type="hidden"]'):
            self.parameters[input.get("name")] = input.get("value", "")

    def update_date_filters(self) -> None:
        """Set year and month values from `self.target_date`
        into self.parameters for POST use
        """
        logger.info(
            "Scraping for year: %s - month: %s",
            self.target_date.year,
            self.target_date.month,
        )
        self.parameters = {
            "ctl00$cntBody$ctlOpinionSearch_Toggle$ddlOpnMonth": str(
                self.target_date.month
            ),
            "ctl00$cntBody$ctlOpinionSearch_Toggle$ddlOpnYear": str(
                self.target_date.year
            ),
            "ctl00$cntBody$ctlOpinionSearch_Toggle$btnSearch": "Search",
        }

    def _download_backwards(self, target_date: date) -> None:
        self.target_date = target_date
        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs):
        super().make_backscrape_iterable(kwargs)
        self.back_scrape_iterable = unique_year_month(
            self.back_scrape_iterable
        )
