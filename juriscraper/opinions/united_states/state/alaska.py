from juriscraper.lib.html_utils import get_row_column_links
from juriscraper.lib.html_utils import get_row_column_text
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://appellate-records.courts.alaska.gov/CMSPublic/Home/Opinions?isCOA=False"
        self.status = "Published"

    def _process_html(self):
        for table in self.html.xpath("//table"):
            date = table.xpath("./preceding-sibling::h5")[0].text_content()
            for row in table.xpath(".//tr"):
                if row.text_content().strip():

                    # skip rows without PDF links in first column
                    try:
                        url = get_row_column_links(row, 1)
                    except IndexError:
                        continue

                    self.cases.append(
                        {
                            "date": date,
                            "docket": get_row_column_text(row, 3),
                            "name": get_row_column_text(row, 4),
                            "neutral_citation": get_row_column_text(row, 2),
                            "url": url,
                        }
                    )
