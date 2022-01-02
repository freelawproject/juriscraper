# Author: Michael Lissner
# History:
# - 2013-06-11: Birth.
# - 2013-08-06: Revised by Brian Carver
# - 2014-08-05: Updated URL by mlr
# - 2021-12-28: Updated by flooie

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

    def _process_html(self):
        rows = self.html.xpath(
            "//div[@id='ContentPlaceHolder1_ChildContent1_UpdatePanel_Opinions']//tbody/tr"
        )
        for row in rows:
            cite = re.findall(r"\d{4} S\.D\. \d+", get_row_column_text(row, 2))
            if not cite:
                continue

            # https://ujs.sd.gov/uploads/sc/opinions/2928369ef9a6.pdf
            # We abstract out the first part of the docket number here
            # And process the full docket number in the `extract_from_text` method
            # Called after the file has been downloaded.
            docket = row.xpath(".//td[2]/a/@href")[0].split("/")[-1][:5]
            self.cases.append(
                {
                    "date": get_row_column_text(row, 1),
                    "name": titlecase(
                        get_row_column_text(row, 2).rsplit(",", 1)[0]
                    ),
                    "citation": cite[0],
                    "url": row.xpath(".//td[2]/a/@href")[0],
                    "docket": docket,
                }
            )

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
