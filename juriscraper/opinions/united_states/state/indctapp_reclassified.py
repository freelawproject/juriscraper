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

            name_parts = link[0].xpath(".//p")
            if name_parts:
                name = titlecase(" ".join(p.text.strip() for p in name_parts))
            else:
                name = titlecase(link[0].text.strip())
            url = link[0].get("href")

            lower_court_parts = cells[3].xpath(".//p")
            if lower_court_parts:
                lower_court = ", ".join(
                    p.text.strip() for p in lower_court_parts
                )
            else:
                lower_court = ", ".join(
                    part.replace(",", ", ").strip()
                    for part in cells[3].xpath(".//text()[normalize-space()]")
                    if part.strip()
                ).strip(", ")

            docket_parts = cells[4].xpath(".//p")
            docket = (
                docket_parts[0].text.strip()
                if docket_parts
                else cells[4].text.strip()
            )

            self.cases.append(
                {
                    "date": cells[1].text.strip(),
                    "other_date": f"Date opinion was reclassified as published: {cells[0].text.strip()}",
                    "name": name,
                    "url": url,
                    "lower_court_number": lower_court,
                    "docket": docket,
                }
            )
