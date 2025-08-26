# History:
# - Long ago: Created by mlr
# - 2014-11-07: Updated by mlr to use new website.
# - 2025-08-26: Updated by lmanzur to use OpinionSiteLinear and extract lower court

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://www.ca5.uscourts.gov/rss.aspx?Feed=Opinions&Which=All&Style=Detail"
        self.court_id = self.__module__

    def _process_html(self):
        case_names = list(self.html.xpath("//item/description/text()[2]"))
        download_urls = [e.tail for e in self.html.xpath("//item/link")]
        case_dates = list(self.html.xpath("//item/description/text()[5]"))
        docket_numbers = list(self.html.xpath("//item/description/text()[1]"))
        statuses_raw = list(self.html.xpath("//item/description/text()[3]"))
        nature_of_suit = list(self.html.xpath("//item/description/text()[4]"))

        statuses = []
        for status in statuses_raw:
            if status == "pub":
                statuses.append("Published")
            elif status == "unpub":
                statuses.append("Unpublished")
            else:
                statuses.append("Unknown")

        # Ensure date is a string, and clean up if needed
        case_dates_cleaned = []
        for date_string in case_dates:
            if isinstance(date_string, str) and date_string.strip():
                case_dates_cleaned.append(date_string.strip())
            else:
                case_dates_cleaned.append("")

        self.cases = []
        for name, url, date, docket, status, nature in zip(
            case_names,
            download_urls,
            case_dates_cleaned,
            docket_numbers,
            statuses,
            nature_of_suit,
        ):
            self.cases.append(
                {
                    "name": name,
                    "url": url,
                    "date": date,  # Now always a string
                    "docket": docket,
                    "status": status,
                    "nature_of_suit": nature,
                }
            )

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        import re

        pattern = re.compile(
            r"""
            (?:
               Appeal(?:s)?\s+from\s+the\s+
             | Petition\s+for\s+Review\s+from\s+an\s+Order\s+of\s+the\s+
             | Petition\s+for\s+Review\s+of\s+the\s+
            )
            (?P<lower_court>[^.]+?)
            (?=\s*(?:\.|Nos?\.|USDC))
            """,
            re.X,
        )
        match = pattern.search(scraped_text)
        lower_court = (
            re.sub(r"\s+", " ", match.group("lower_court")).strip()
            if match
            else ""
        )
        return {
            "Docket": {
                "appeal_from_str": lower_court,
            }
        }
