from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://nvcourts.gov/Supreme/Decisions/Unpublished_Orders/"
        self.status = "Published"

        # HTTPS certificate is bad, but hopefully they'll fix it and we can remove the line below
        self.disable_certificate_verification()

    def _process_html(self):
        table_row_path = '//table[@id="ctl00_ContentPlaceHolderContent_UnpublishedOrders_GridView1"]//tr[position()>1]'
        for row in self.html.xpath(table_row_path):
            url = row.xpath(".//td[3]//a/@href")

            # skip rows with malformed html
            if not url:
                continue

            date_string = row.xpath(".//td[3]")

            self.cases.append(
                {
                    "date": date_string[0].text_content(),
                    "docket": row.xpath(".//td[1]")[0].text_content(),
                    "name": row.xpath(".//td[2]")[0].text_content().title(),
                    "url": url[0],
                }
            )
