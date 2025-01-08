"""
Contact: Sara Velasquez, svelasquez@idcourts.net, 208-947-7501
History:
 - 2014-08-05, mlr: Updated.
 - 2015-06-19, mlr: Updated to simply the XPath expressions and to fix an OB1
   problem that was causing an InsanityError. The cause was nasty HTML in their
   page.
 - 2015-10-20, mlr: Updated due to new page in use.
 - 2015-10-23, mlr: Updated to handle annoying situation.
 - 2016-02-25 arderyp: Updated to catch "ORDER" (in addition to "Order") in download url text
 - 2024-12-30, grossir: updated to OpinionSiteLinear
"""

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    # Skip rows that don't have  link in 4th cell with
    # either 'Opinion', 'Order', 'ORDER', or 'Amend' in
    # the link text
    path_conditional_anchor = (
        "a["
        'contains(.//text(), "Opinion") or '
        'contains(.//text(), "Order") or '
        'contains(.//text(), "ORDER") or '
        'contains(.//text(), "Amended")'
        "]"
    )

    # https://www.isc.idaho.gov/appeals-court/isc_civil
    base_url = "https://www.isc.idaho.gov/appeals-court/"
    url_part = "isc_civil"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = f"{self.base_url}{self.url_part}"
        self.court_id = self.__module__
        self.status = "Published"

    def _process_html(self):
        row_xpath = f"//table//tr[.//{self.path_conditional_anchor}]"
        for row in self.html.xpath(row_xpath):
            url = self.get_opinion_url(row).replace("http://", "https://")
            self.cases.append(
                {
                    "date": row.xpath("string(td[1])").strip(),
                    "docket": row.xpath("string(td[2])").strip(),
                    "name": row.xpath("string(td[3])").strip(),
                    "url": url,
                }
            )

    def get_opinion_url(self, row) -> str:
        """Get's the URL tagged as an Opinion, if possible

        We'll accept an order document if the opinion document
        is missing. Since each row can list multiple valid links,
        we will parse all acceptable links, take the opinion link
        if present, otherwise take the first acceptable link.

        :param row: the lxml object of the row
        :return: the document URL
        """

        for link in row.xpath("td[4]//a"):
            if "Opinion" in link.text_content().strip():
                return link.xpath("@href")[0]

        return row.xpath("td[4]//a/@href")[0]
