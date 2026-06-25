# Scraper for Minnesota Supreme Court
# CourtID: minn
# Court Short Name: MN
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-03
# Contact:  Liz Reppe (Liz.Reppe@courts.state.mn.us), Jay Achenbach (jay.achenbach@state.mn.us)

# 2024-08-09: update and implement backscraper, grossir

import re
from datetime import date, datetime, timezone
from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.exceptions import BotChallengeError
from juriscraper.lib.network_utils import add_delay
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_query = "supct"
    days_interval = 7
    first_opinion_date = date(1998, 1, 1)

    base_url = "https://mn.gov/law-library/search/"
    # Seconds to wait before querying, to space out the shared-source scrapers
    # and respect the site's `Request-rate` (see robots.txt). See #2006
    request_delay = 5

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("verify", False)
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__

        self.status = "Published"
        if self.court_query == "ctapun":
            self.status = "Unpublished"

        self.url = self.base_url
        self.params = self.base_params = {
            "v:sources": "mn-law-library-opinions",
            "query": f" (url:/archive/{self.court_query}) ",
            "sortby": "date",
        }

        self.request["headers"] = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Dest": "document",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Fetch-Mode": "navigate",
            "Host": "mn.gov",
            "User-Agent": "Juriscraper/3.0 Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Referer": "https://mn.gov/law-library/search/?v%3Asources=mn-law-library-opinions&query=+%28url%3A%2Farchive%2Fsupct%29+&citation=&qt=&sortby=&docket=&case=&v=&p=&start-date=&end-date=",
            "Connection": "keep-alive",
        }
        self.make_backscrape_iterable(kwargs)
        self.needs_special_headers = True

    async def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        # parse() issues an initial _download() (no query params). If that was
        # skipped because we are out of the visit window, self.html is None and
        # we abort without issuing the query.
        if self.html is None:
            return

        # Pause before the actual query to respect the site's rate limit.
        if not self.test_mode_enabled():
            await add_delay(self.request_delay, deviation=2)
        self.html = await self._download({"params": self.params})

        if self.html is None:
            return

        self._check_for_bot_challenge()

        # This warning is useful for backscraping
        results_number = self.html.xpath(
            "//div[@class='searchresult_number']/text()"
        )
        if results_number:
            results_number = results_number[0].split(" of ")[-1].strip()
            if int(results_number) > 10:
                logger.warning(
                    "Page has a size 10, and there are %s results for this query",
                    results_number,
                )

        for case in self.html.xpath("//div[@class='searchresult']"):
            name = re.sub(r"\s+", " ", case.xpath(".//a/text()")[0])
            name_match = re.search(r"(?P<name>.+)\. A\d{2}-\d+", name)
            if name_match:
                name = name_match.group("name")

            summary = case.xpath(
                ".//div[@class='searchresult_snippet']/text()"
            )[0]
            disposition = ""
            # minnctapp_u sometimes has a disposition, but it's format
            # is much more variable
            if self.status == "Published":
                parts = summary.split(".")
                if (
                    len(parts) > 2
                    and len(parts[-2].split()) <= 10
                    and not re.search(r"\d", parts[-2])
                ):
                    # Sometimes there is no disposition. Ex: A23-1504
                    # False positives usually contain numbers. Ex: A22-0776
                    disposition = parts[-2].strip()

            raw_date = case.xpath(".//div[@class='searchresult_date']")[
                -1
            ].text_content()
            date_filed = re.sub(r"\s+", " ", raw_date).split(":")[1].strip()

            # Backscrapers may find citations, since they are attached some
            # months after the initial release of an opinion
            citation = ""
            if cite_element := case.xpath(
                ".//div[b[contains(text(), 'Citation:')]]"
            ):
                citation = (
                    cite_element[0].text_content().split(":", 1)[-1].strip()
                )

            url = case.xpath(".//a/@href")[0]
            docket = url.split("/")[-1].split("-")[0][2:]
            self.cases.append(
                {
                    "date": date_filed,
                    "name": name,
                    "url": urljoin("https://", url),
                    "disposition": disposition,
                    "summary": summary,
                    "docket": docket,
                    "citation": citation,
                }
            )

    async def _download_backwards(self, dates: tuple[date, date]):
        logger.info("Backscraping for range %s - %s", *dates)
        params = {**self.base_params}
        params.update(
            {
                "start-date": dates[0].strftime("%-m/%-d/%Y"),
                "end-date": dates[1].strftime("%-m/%-d/%Y"),
                "query": f"{params['query']}date:[{dates[0].strftime('%Y-%m-%d')}..{dates[1].strftime('%Y-%m-%d')}]",
            }
        )
        self.params = params
        self.html = await self._download()
        await self._process_html()

    def _within_visit_window(self) -> bool:
        """Whether we are inside the crawl window the site's robots.txt allows.

        mn.gov's robots.txt declares ``Visit-time: 0000-1200`` (in GMT), i.e.
        crawling is only welcome between midnight and noon UTC. Scraping
        outside that window is part of what gets us flagged by the bot
        manager. Always True in test mode. See #2006.

        :return: True if the current UTC time is within the allowed window
        """
        if self.test_mode_enabled():
            return True
        return datetime.now(timezone.utc).hour < 12

    async def _download(self, request_dict=None):
        """Skip the request entirely when outside the robots.txt visit window.

        Returning None aborts the scrape gracefully: ``parse()`` leaves
        ``self.html`` as None, ``_process_html`` bails out early, and the run
        ends with zero results (a warning, not an error) instead of querying
        the bot-managed endpoint at a disallowed time. See #2006.

        :param request_dict: passed through to the parent downloader
        :return: the parsed response, or None when outside the visit window
        """
        if not self._within_visit_window():
            logger.warning(
                "%s: outside the robots.txt visit window (0000-1200 GMT); "
                "skipping this run",
                self.court_id,
            )
            return None
        return await super()._download(request_dict)

    def _check_for_bot_challenge(self) -> None:
        """Raise if the source served a Radware Bot Manager captcha page
        instead of the search results, so the block surfaces in Sentry
        rather than being ingested as a successful zero-result scrape.

        :raises BotChallengeError: when a captcha challenge is detected
        """
        title = " ".join(self.html.xpath("//title//text()"))
        if "Bot Manager Captcha" in title or self.html.xpath(
            "//div[contains(@class, 'h-captcha')]"
        ):
            raise BotChallengeError(
                f"{self.court_id}: blocked by Radware Bot Manager captcha",
                fingerprint=[f"{self.court_id}-bot-challenge"],
            )
