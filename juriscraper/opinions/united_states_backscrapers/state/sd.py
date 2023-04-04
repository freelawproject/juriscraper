# Author: Michael Lissner
# History:
# - 2013-06-11: Birth.
# - 2013-08-06: Revised by Brian Carver
# - 2014-08-05: Updated URL by mlr
# - 2022-01-01: Updated by flooie

import datetime
import re
from typing import Any, Dict

from juriscraper.lib.html_utils import get_row_column_text
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://ujs.sd.gov/Supreme_Court/opinions.aspx"
        self.years = range(2010, datetime.date.today().year)

    def _set_page_year(
        self,
        year: int,
        view_state: str,
        event_validation: str,
    ) -> None:
        a = self.html.xpath(
            f".//a[contains(@id,'ContentPlaceHolder1_ChildContent1_Repeater_OpinionsYear_LinkButton1')][contains(text(), '{year}')]"
        )
        link = a[0].get("href").split("'")[1]
        data = {
            "__VIEWSTATE": view_state,
            "__EVENTVALIDATION": event_validation,
            "__EVENTTARGET": link,
        }
        self.parameters = data
        self.method = "POST"

    def _set_page_next(
        self,
        view_state: str,
        event_validation: str,
    ) -> None:
        data = {
            "ctl00$ctl00$ScriptManager1": "ctl00$ctl00$ContentPlaceHolder1$ChildContent1$UpdatePanel_Opinions|ctl00$ctl00$ContentPlaceHolder1$ChildContent1$LinkButton_Next",
            "__EVENTTARGET": "ctl00$ctl00$ContentPlaceHolder1$ChildContent1$LinkButton_Next",
            "__VIEWSTATE": view_state,
            "__EVENTVALIDATION": event_validation,
        }
        self.parameters = data
        self.method = "POST"

    def _process_html(self):
        for year in self.years:
            view_state = self.html.xpath("//input[@id='__VIEWSTATE']")[0].get(
                "value"
            )
            event_validation = self.html.xpath(
                "//input[@id='__EVENTVALIDATION']"
            )[0].get("value")

            self._set_page_year(year, view_state, event_validation)
            self.html = super()._download()
            while True:
                rows = self.html.xpath(
                    "//div[@id='ContentPlaceHolder1_ChildContent1_UpdatePanel_Opinions']//tbody/tr"
                )
                for row in rows:
                    cite = re.findall(
                        r"\d{4} S\.D\. \d+", get_row_column_text(row, 2)
                    )
                    if not cite:
                        continue

                    # https://ujs.sd.gov/uploads/sc/opinions/2928369ef9a6.pdf
                    # We abstract out the first part of the docket number here
                    # And process the full docket number in the `extract_from_text` method
                    # Called after the file has been downloaded.
                    docket = row.xpath(".//td[2]/a/@href")[0].split("/")[-1][
                        :5
                    ]
                    self.cases.append(
                        {
                            "date": get_row_column_text(row, 1),
                            "name": titlecase(
                                get_row_column_text(row, 2).rsplit(",", 1)[0]
                            ),
                            "neutral_citation": cite[0],
                            "url": row.xpath(".//td[2]/a/@href")[0],
                            "docket": docket,
                        }
                    )
                page_count = self.html.xpath(
                    "//span[@id='ContentPlaceHolder1_ChildContent1_Label_Page']"
                )[0].text_content()
                page_of = re.findall(r"Page (\d+) of (\d+)", page_count)
                if len(set(page_of[0])) == 1:
                    break

                vs = self.html.xpath("//input[@id='__VIEWSTATE']")[0].get(
                    "value"
                )
                ev = self.html.xpath("//input[@id='__EVENTVALIDATION']")[
                    0
                ].get("value")

                self._set_page_next(view_state=vs, event_validation=ev)
                self.html = super()._download()

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Can we extract the date filed from the text?

        :param scraped_text: The content of the document downloaded
        :return: Metadata to be added to the case
        """
        # The docket number appears to be the first text on the page.
        # So I crop the text to avoid any confusion that might occur in the
        # body of an opinion.
        docket = re.findall(r"#\d+.*-.-\w{3}", scraped_text)[0][:20]
        metadata = {
            "Docket": {
                "docket_number": docket,
            },
        }
        return metadata
