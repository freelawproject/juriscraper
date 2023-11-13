from requests.exceptions import ChunkedEncodingError

from juriscraper.lib.html_utils import (
    get_row_column_links,
    get_row_column_text,
)
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://appellate-records.courts.alaska.gov/CMSPublic/Home/Opinions?isCOA=False"
        self.status = "Published"
        self.request["headers"][
            "user-agent"
        ] = "Free Law Project"  # juriscraper in the user agent crashes it - it appears to be just straight up blocked.

    def _download(self, request_dict={}):
        # Unfortunately, about 2/3 of calls are rejected by alaska but
        # if we just ignore those encoding errors we can live with it
        try:
            return super()._download(request_dict)
        except ChunkedEncodingError:
            return None

    def _process_html(self):
        if not self.html:
            return
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
                            "citation": get_row_column_text(row, 2),
                            "url": url,
                        }
                    )
