# Author: Michael Lissner
# History:
# - 2013-06-11: Birth.
# - 2013-08-06: Revised by Brian Carver
# - 2014-08-05: Updated URL by mlr
# - 2021-12-28: Updated by flooie

import re

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
            self.cases.append(
                {
                    "date": get_row_column_text(row, 1),
                    "name": titlecase(
                        get_row_column_text(row, 2).rsplit(",", 1)[0]
                    ),
                    "citation": cite[0],
                    "url": row.xpath(".//td[2]/a/@href")[0],
                    "docket": row.xpath(".//td[2]/a/@href")[0].split("/")[-1][
                        :5
                    ],
                }
            )
