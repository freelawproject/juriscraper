"""
Scraper for Indiana Court of Appeals Reclassified Opinions
CourtID: indctapp
Court Short Name: Ind. Ct. App.
Auth: Luis Manzur
History:
    2025-07-29: Created by Luis Manzur
"""

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://www.in.gov/courts/appeals/reclassified/"
        self.should_have_results = True
        self.expected_content_types = ["application/pdf"]

    def _process_html(self):
        """Process the HTML to extract case details.

        :return None
        """

        rows = self.html.xpath("//table/tbody/tr")
        for row in rows:
            cells = row.xpath(".//td")
            link = cells[2].xpath(".//a")
            if not link:
                continue

            # Cell text may be direct, or split across <p>, <span> or <br>
            # tags (e.g. rows pasted from Outlook). Avoid .text, which is
            # None or truncated when a child tag comes first. #2050
            name = titlecase(
                " ".join(t.strip() for t in link[0].itertext() if t.strip())
            )
            url = link[0].get("href")

            lower_court_parts = cells[3].xpath(".//p")
            if lower_court_parts:
                lower_court = ", ".join(
                    p.text_content().strip() for p in lower_court_parts
                )
            else:
                # Strip commas per part: a text node may already end in a
                # comma before a <br>, which would double up with the join
                lower_court = ", ".join(
                    part.replace(",", ", ").strip(" ,")
                    for part in cells[3].xpath(".//text()[normalize-space()]")
                    if part.strip(" ,")
                )

            docket_parts = cells[4].xpath(".//p")
            docket = (
                docket_parts[0].text_content().strip()
                if docket_parts
                else cells[4].text_content().strip()
            )

            self.cases.append(
                {
                    "date": cells[1].text_content().strip(),
                    "other_date": f"Date opinion was reclassified as published: {cells[0].text_content().strip()}",
                    "name": name,
                    "url": url,
                    "lower_court_number": lower_court,
                    "docket": docket,
                }
            )
