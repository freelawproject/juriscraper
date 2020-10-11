from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://nvcourts.gov/Supreme/Decisions/Advance_Opinions/"
        self.status = "Published"

        # HTTPS certificate is bad, but hopefully they'll fix it and we can remove the line below
        self.disable_certificate_verification()

    def _process_html(self):
        table_row_path = '//table[@style="border-spacing:0px"]//tr'
        for row in self.html.xpath(table_row_path):
            citation = row.xpath(".//td[1]")[0].text_content().strip()
            docket = row.xpath(".//td[2]")[0].text_content()
            name = row.xpath(".//td[3]")[0].text_content()
            url = row.xpath(".//td[4]//a/@href")
            date_string = row.xpath(".//td[4]")[0].text_content()
            year = convert_date_string(date_string).year

            self.cases.append(
                {
                    "date": date_string,
                    "docket": docket,
                    "name": name if name else "Unknown",
                    "neutral_citation": "%d NV %s" % (year, citation),
                    "url": url[0],
                }
            )
