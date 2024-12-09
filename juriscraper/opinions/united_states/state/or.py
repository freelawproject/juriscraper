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
    base_url = "https://cdm17027.contentdm.oclc.org/digital/api/search/collection/{}/searchterm/{}-{}/field/dated/mode/exact/conn/and/maxRecords/200"
    # technically they have an 1870 case but just one
    first_opinion_date = datetime(1997, 8, 12)
    days_interval = 15

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        today = datetime.today()
        self.url = self.format_url(today - timedelta(15), today)
        self.make_backscrape_iterable(kwargs)

    def _process_html(self):
        for row in self.html["items"]:
            docket, name, citation, date = (
                x["value"] for x in row["metadataFields"]
            )
            if not name:
                # Happens on rows like:
                # "Miscellaneous Supreme Court dispositions, June 10 and 13, 2024"
                logger.info("Skipping row '%s'", docket)
                continue

            judge, disposition, status, lower_court_number = self.get_details(
                row
            )
            per_curiam = False
            if judge and judge == "PC" or "per curiam" in judge.lower():
                per_curiam = True
                judge = ""

            self.cases.append(
                {
                    "name": name,
                    "date": date,
                    "docket": docket.split(",")[0],
                    "url": f"https://ojd.contentdm.oclc.org/digital/api/collection/{row['collectionAlias']}/id/{row['itemId']}/download",
                    "citation": citation,
                    "judge": judge,
                    "per_curiam": per_curiam,
                    "status": status,
                    "disposition": disposition,
                    "lower_court_number": lower_court_number,
                }
            )

    def get_details(self, row: dict) -> tuple[str, str, str, str]:
        """Makes a secondary request to get details for a single
        opinion

        :param row: the JSON records, to get the item id for the request
            or the JSON object in tests
        :return: a tuple containing, if it has a valid value
            - judge
            - disposition
            - status
            - lower court number (only for `or`)
        """
        if self.test_mode_enabled():
            if not row.get("detailJson"):
                return (
                    "placeholder judge",
                    "placeholder disposition",
                    "Unknown",
                    "placeholder lower court number",
                )
            # Some test cases have their detail data manually copy pasted
            json = row["detailJson"]
        else:
            item_id = row["itemId"]
            url = f"https://cdm17027.contentdm.oclc.org/digital/api/collections/{self.court_code}/items/{item_id}/false"
            logger.debug("Getting detail JSON from %s", url)
            self._request_url_get(url)
            json = self.request["response"].json()

        if len(json["fields"]) == 1:
            fields = json["parent"]["fields"]
        else:
            fields = json["fields"]

        judge, disposition, status, lower_court_number = "", "", "Unknown", ""
        for field in fields:
            if field["key"] == "judge":
                judge = field["value"]
            elif field["key"] == "type":
                if field["value"] in [
                    "Nonprecedential opinion",
                    "Unpublished",
                ]:
                    status = "Unpublished"
                else:
                    status = "Published"
            elif field["key"] == "descri":
                disposition = field["value"]
            elif field["key"] == "relhapt":
                # For orctapp this field may be populated with consolidated docket
                # numbers
                if self.court_id.endswith("or") and not field[
                    "value"
                ].startswith("S"):
                    lower_court_number = field["value"]

        return judge, disposition, status, lower_court_number

    def _download_backwards(self, dates: tuple) -> None:
        logger.info("Backscraping for range %s %s", *dates)
        self.url = self.format_url(*dates)
        self.html = self._download()
        self._process_html()

    def format_url(self, start_date: datetime, end_date: datetime) -> str:
        """
        Creates a date range URL by formatting input dates
        """
        start = datetime.strftime(start_date, "%Y%m%d")
        end = datetime.strftime(end_date, "%Y%m%d")
        return self.base_url.format(self.court_code, start, end)
