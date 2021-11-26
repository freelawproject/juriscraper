from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import (
    get_row_column_links,
    get_row_column_text,
)
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://cafc.uscourts.gov/home/case-information/opinions-orders/?field_origin_value=All&field_report_type_value=All"
        self.back_scrape_iterable = list(range(1, 700))
        self.court_id = self.__module__

    def _process_html(self):
        """Process HTML
        Iterate over each table row.
        If a table row does not have a link, skip it

        Return: None
        """
        for row in self.html.xpath("//table/tbody/tr"):
            try:
                url = get_row_column_links(row, 4)
            except IndexError:
                continue

            date = get_row_column_text(row, 1)
            docket = get_row_column_text(row, 2)
            name = get_row_column_text(row, 4)
            name = titlecase(name.split("[")[0].strip())
            status_raw = get_row_column_text(row, 5)
            status_raw = status_raw.lower()
            if "nonprecedential" in status_raw:
                status = "Unpublished"
            elif "precedential" in status_raw:
                status = "Published"
            else:
                status = "Unknown"

            self.cases.append(
                {
                    "date": date,
                    "docket": docket,
                    "url": url,
                    "name": name,
                    "status": status,
                }
            )

    def _download_backwards(self, n):
        self.url = f"http://www.cafc.uscourts.gov/opinions-orders?page={n}"
        logger.info(f"Backscraping for page {n}: {self.url}")
        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
            self._process_html()
