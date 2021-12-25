# Author: Michael Lissner
# History:
# - 2013-06-11: Birth.
# - 2013-08-06: Revised by Brian Carver
# - 2014-08-05: Updated URL by mlr

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
            self.cases.append(
                {
                    "date": self.get_row_column_text(row, 1),
                    "name": self.get_row_column_text(row, 2).rsplit(",", 1)[0],
                    "neutral_citation": self.get_row_column_text(
                        row, 2
                    ).rsplit(",", 1)[1],
                    "url": row.xpath(".//td[2]/a/@href")[0],
                    "docket": f'#{row.xpath(".//td[2]/a/@href")[0].split("/")[-1][:5]}',
                }
            )

    def get_row_column_text(self, row, cell_num):
        """Return string cell value for specified column.

        :param row: HtmlElement
        :param cell_num: int
        :return: string
        """
        return row.xpath(".//td[%d]" % cell_num)[0].text_content().strip()
