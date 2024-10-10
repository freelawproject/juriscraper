"""
History:
 - 2014-08-05: Adapted scraper to have year-based URLs.
 - 2023-11-18: Fixed and updated
"""

from datetime import datetime, timedelta

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_code = "p17027coll3"
    detail_url = "https://ojd.contentdm.oclc.org/digital/bl/dmwebservices/index.php?q=dmQuery/{}/identi^{}^all^and/title!subjec!descri!dmrecord/title/1024/1/0/0/0/0/json"
    download_url = "https://ojd.contentdm.oclc.org/digital/api/collection/{}/id/{}/download"
    days_interval = 720
    # Earliest opinion as of development in Oct 2024
    first_opinion_date = datetime(2023, 4, 1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://www.courts.oregon.gov/publications/sc/Pages/default.aspx"
        )
        self.make_backscrape_iterable(kwargs)

        # By default, scrape at most 10 days into the past
        # It's important to limit regular scrapes, since
        # this scraper makes secondary requests and the site
        # loads all opinions back to a year; which would
        # create a lot of hits to the server each time
        # the hourly scraper is triggered
        # The limits will be modified in a backscrape
        self.start_date = (datetime.today() - timedelta(10)).date()
        self.end_date = (datetime.today() + timedelta(1)).date()

    def _process_html(self):
        for date_header in self.html.xpath(
            "//h4[a[contains(@href, '/dated/')]]"
        ):
            date_string = date_header.text_content().strip()
            if not date_string:
                logger.info("Skipping section with no date string")
                continue

            date = datetime.strptime(date_string, "%m/%d/%Y").date()
            if date > self.end_date:
                # Opinions come in descending date order
                continue
            if date < self.start_date and not self.test_mode_enabled():
                logger.info(
                    "Date %s is out of range [%s to %s]",
                    date,
                    self.start_date,
                    self.end_date,
                )
                break

            self.process_a_date(date_header)

    def process_a_date(self, date_header) -> None:
        """Process a section defined by a date header

        :param date_header: the lxml element containing the date
        :return None
        """
        date_string = date_header.text_content().strip()

        # orctapp has h5 tags which describe the status of the
        # opinions in the next ul
        for sibling in date_header.xpath("following-sibling::*"):
            if sibling.tag not in ["ul", "h5"]:
                # Time to jump to another date
                break

            if "orctapp" in self.court_id:
                if sibling.tag == "h5":
                    status = sibling.text_content().strip()
                    if status == "Precedential Opinions":
                        status = "Published"
                    elif status == "Nonprecedential Memorandum Opinions":
                        status = "Unpublished"
                    else:
                        status = "Unknown"
            else:
                status = "Published"

            for item in sibling.xpath("li"):
                # Ensure two links are present (skip Petitions
                # for Review rows)
                text = item.text_content().strip()
                anchors = item.xpath(".//a")
                if not (len(anchors) > 1):
                    logger.info("Skipping row without 2 links. Row: %s", text)
                    continue

                detail_url = anchors[0].xpath("./@href")[0]
                download_url, disposition = self.get_details(detail_url)
                if not download_url:
                    # Usually happens for
                    # "Miscellaneous Supreme Court Dispositions"
                    logger.info("No records for detail JSON")
                    continue

                name = text.split(")", 1)[-1]
                # Clean up names like:
                # "Knopp v. Griffin-Valade (Certified appeal accepted)"
                if "(" in name:
                    name, disposition = name.split("(", 1)
                    disposition = disposition.strip(")")

                self.cases.append(
                    {
                        "date": date_string,
                        "name": name,
                        "docket": anchors[1].text_content().strip(),
                        "url": download_url,
                        "citation": item.xpath("b/text()")[0].strip(),
                        "status": status,
                        "disposition": disposition,
                    }
                )

    def get_details(self, detail_url: str) -> tuple[str, str]:
        """Makes a request to get a case details, including the URL

        :param detail_url: case detail's page url
        :return: a tuple: (the pdf download url, the disposition)
        """
        if self.test_mode_enabled():
            return "placeholder url", "placeholder disposition"

        identifier = detail_url.split("=")[-1]
        detail_url = self.detail_url.format(self.court_code, identifier)

        logger.info("Getting detail JSON from %s", detail_url)
        json = self.request["session"].get(detail_url).json()
        logger.debug(json)
        if not json.get("records"):
            return "", ""

        disposition = json["records"][0].get("descri") or ""
        download_url = self.download_url.format(
            self.court_code, json["records"][0]["pointer"]
        )
        return download_url, disposition

    def _download_backwards(self, dates: tuple) -> None:
        """The site loads by default the last couple years of data.
        So it's not necessary to query the page in a special way to
        target data in these years, only to set the proper date limits

        To back scrape older opinions, we would need to target another
        site
        """
        self.start_date, self.end_date = dates
        logger.info("Backscraping for range %s %s", *dates)
        self.html = self._download()
        self._process_html()
