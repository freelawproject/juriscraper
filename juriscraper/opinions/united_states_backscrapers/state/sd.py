# Author: Michael Lissner
# Date created: 2013-06-11

from lxml.html import fromstring

from juriscraper.lib.html_utils import get_row_column_text
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://ujs.sd.gov/Supreme_Court/opinions.aspx"

    def _set_parameters(self):
        self.method = "POST"
        self.parameters = {
            "ctl00$ctl00$ScriptManager1": "ctl00$ctl00$ContentPlaceHolder1$ChildContent1$UpdatePanel_Opinions|ctl00$ctl00$ContentPlaceHolder1$ChildContent1$LinkButton_Next",
            "__EVENTTARGET": "ctl00$ctl00$ContentPlaceHolder1$ChildContent1$LinkButton_Next",
        }
        self.parameters["__VIEWSTATE"] = (
            self.html.xpath("//*[@id='__VIEWSTATE']/@value")[0],
        )
        self.parameters["__EVENTVALIDATION"] = (
            self.html.xpath("//*[@id='__EVENTVALIDATION']/@value")[0],
        )

    def _download(self):
        response = self.request["session"].post(self.url, data=self.parameters)
        return fromstring(response.text)

    def _process_html(self):
        self._set_parameters()
        rows = self.html.xpath(
            "//div[@id='ContentPlaceHolder1_ChildContent1_UpdatePanel_Opinions']//tbody/tr"
        )
        for row in rows:
            self.cases.append(
                {
                    "date": get_row_column_text(row, 1),
                    "name": get_row_column_text(row, 2).rsplit(",", 1)[0],
                    "citation": get_row_column_text(row, 2).rsplit(
                        ",", 1
                    )[1],
                    "url": row.xpath(".//td[2]/a/@href")[0],
                    "docket": row.xpath(".//td[2]/a/@href")[0].split("/")[-1][
                        :5
                    ],
                }
            )

        # Continue the loop
        if get_row_column_text(rows[-1], 3) != "1":
            try:
                self.html = super()._download()
                self._process_html()
            except Exception as e:
                pass
