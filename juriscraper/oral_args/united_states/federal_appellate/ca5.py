"""Scraper for Fifth Circuit of Appeals
CourtID: ca5
Court Short Name: ca5
Reviewer: mlr
History:
 - 2014-07-19: Created by Andrei Chelaru
 - 2014-11-08: Updated for new site by mlr.
 - 2026-08-05: Updated by grossir for the website redesign, see #2062
"""

from juriscraper.AbstractSite import logger
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.ca5.uscourts.gov/feeds/oral-arguments"
        # The feed keeps a rolling window of the latest recordings, so it
        # holds items even when the court is in recess
        self.should_have_results = True

    def _process_html(self):
        for item in self.html.xpath("//item"):
            # The feed escapes the `<br/>` separators, so the whole record
            # reaches us as a single text node. Ex:
            # "19-40930<br/>USA v. Senegal<br/>Argued August 4, 2026<br/>
            #  <br/>Appearing:<br/>Kathryn Shephard — Appellant<br/>"
            description = item.xpath("description/text()")
            if not description:
                logger.error("ca5: item with no description")
                continue

            fields = [f.strip() for f in description[0].split("<br/>")]
            if len(fields) < 3 or not fields[2].startswith("Argued"):
                logger.error(
                    "ca5: unexpected description '%s'", description[0]
                )
                continue

            docket, name, argued = fields[:3]
            # The lxml HTML parser treats `link` as a void element, so the
            # URL ends up as its tail rather than its text
            url = item.xpath("link")[0].tail

            # Each attorney is listed as "Name — Role", after an
            # "Appearing:" heading. Not every recording lists them
            attorneys = [f for f in fields[3:] if f and f != "Appearing:"]

            self.cases.append(
                {
                    "name": name,
                    "url": url.strip(),
                    "date": argued.removeprefix("Argued").strip(),
                    "docket": docket,
                    "attorney": "; ".join(attorneys),
                }
            )
