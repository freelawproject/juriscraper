# Scraper for the United States Court of Appeals for the Seventh Circuit
# CourtID: ca7
# Court Short Name: 7th Cir.

import re

import feedparser

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    # The opinion's own URL carries the filing date, as `Y2026/D07-31`
    filing_date_in_url = re.compile(r"Path=Y(\d{4})/D(\d{2})-(\d{2})")
    # The description repeats the day the court posted the PDF, which is
    # the filing date for all but a handful of late postings
    upload_date_in_summary = re.compile(
        r"\[uploaded:\s*(\d{2})/(\d{2})/(\d{4})\]"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://media.ca7.uscourts.gov/cgi-bin/OpinionsWeb/processWebInputExternal.pl?Time=month&startDate=&endDate=&Author=any&AuthorName=&Case=any&CaseYear=&CaseNum=&Rubmit=RssRecent&RssJudgeName=Sykes&OpsOnly=yes"
        self.should_have_results = True
        self.court_id = self.__module__

    def _process_html(self):
        if self.test_mode_enabled():
            self.year = 2022
        feed = feedparser.parse(self.request["response"].content)

        # (feed entry time, filing date, docket, case). The first three are
        # the sort key only; just the case is kept. See the sort below
        rows = []

        for item in feed["entries"]:
            if item.get("published_parsed", None) is None:
                logger.warning("Skipping item with no published date")
                continue
            parts = item["summary"].split()
            docket = parts[parts.index("case#") + 1]
            name = item["summary"].split(docket)[1].split("(")[0]
            author = item["summary"].split("{")[1].split("}")[0]

            date = self.get_filing_date(item)
            if not date:
                # Falling back to the feed time reintroduces the bug this
                # guards against, but a wrong date beats dropping the case
                logger.warning(
                    "ca7: no filing date for docket %s, using feed time",
                    docket,
                )
                date = item["published"]

            per_curiam = False
            if "curiam" in author.lower():
                per_curiam = True
                author = ""

            rows.append(
                (
                    item["published_parsed"],
                    date,
                    docket,
                    {
                        "url": item["link"],
                        "docket": docket,
                        "date": date,
                        "name": name,
                        "status": "Published",
                        "judge": author,
                        "author": author,
                        "per_curiam": per_curiam,
                    },
                )
            )

        # CourtListener walks these top down and aborts at the fifth
        # consecutive duplicate, so the newest feed entries have to come
        # first: that guarantees every new row is seen before the first row
        # we already have. Ordering by filing date instead left opinions the
        # court posted later in the day sitting behind rows already in CL,
        # where nothing ever reached them again. Sorting by feed time rather
        # than filing date is also what keeps the backlog items visible once
        # their date is corrected to an older one. #2123
        #
        # `sort` reads only the first three members, so the case dicts are
        # never compared. Unlike `ca9`, the entry time cannot be carried on
        # the case itself: `OpinionSiteLinear._check_sanity` rejects any key
        # outside `valid_keys`
        rows.sort(key=lambda row: row[:3], reverse=True)
        self.cases.extend(row[-1] for row in rows)

    def get_filing_date(self, item: dict) -> str:
        """Get the date the opinion was filed

        `<pubDate>` is the moment the item entered the RSS feed, and the
        court re-stamps it whenever the feed is rebuilt, so it runs days
        ahead of the filing date for backlog items. The opinion's URL and
        its description both carry the real date. #2123

        :param item: a feedparser entry
        :return: the filing date as YYYY-MM-DD, or "" if neither field has one
        """
        if match := self.filing_date_in_url.search(item["link"]):
            year, month, day = match.groups()
            return f"{year}-{month}-{day}"

        if match := self.upload_date_in_summary.search(item["summary"]):
            month, day, year = match.groups()
            return f"{year}-{month}-{day}"

        return ""

    def _date_sort(self) -> None:
        """Preserve the feed ordering applied by `_process_html`

        `AbstractSite._date_sort` would reorder the cases by filing date,
        which is the ordering that made us miss opinions. #2123

        :return: None
        """

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        pattern = re.compile(
            r"""
            (?:
               Appeals?\s+from\s+the\s+
           | (?:On\s+)?Petitions?\s+for\s+Review\s+of\s+(?:an\s+)?Orders?\s+of\s+the\s+
            )
            (?P<lower_court>[^.]+?)
            (?=\s*(?:\.|Nos?\.|USDC))
            """,
            re.X,
        )

        lower_court = ""
        if match := pattern.search(scraped_text):
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()

        if lower_court:
            return {
                "Docket": {
                    "appeal_from_str": lower_court,
                }
            }
        return {}
