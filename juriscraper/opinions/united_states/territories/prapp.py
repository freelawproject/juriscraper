"""
Author: William Palin
Date created: 2023-01-21
Scraper for the Decisiones del Tribunal Apelaciones
CourtID: prapp
Court Short Name: Puerto Rico Court of Apelaciones
"""

from datetime import date, datetime

from dateparser import parse
from dateutil.relativedelta import relativedelta

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    first_opinion_date = "2015/01/01"
    today = today_str = datetime.now().strftime("%Y/%m/%d")
    base_url = "https://poderjudicial.pr/tribunal-apelaciones/decisiones-finales-del-tribunal-de-apelaciones"
    is_backscrape = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = date.today().year
        self.current_month = self.format_spanish_month_year(datetime.now())

        self.url = self.base_url
        self.status = "Published"
        self.make_backscrape_iterable(kwargs)

    def _download(self):
        """Download case pages

        If a backscrape ignore the need to find the correct page

        :param request_dict: Empty dict
        :return: HTML object
        """
        if self.test_mode_enabled():
            return super()._download()
        if not self.html:
            self.html = super()._download()

        if not self.is_backscrape:
            latest_url = self.html.xpath(
                f"(//a[contains(@href,'{self.year}') and contains(@href,'decisiones-del-tribunal-de-apelaciones')])[last()]/@href"
            )
            if not latest_url:
                logger.debug(f"No opinions posted for {self.year}")
                self.html = None
                return

            self.url = latest_url[0]
        if self.current_month not in self.url:
            logger.debug(
                f"No opinions yet posted for current month {self.current_month}, moving to most recent month."
            )

        return super()._download()

    def _process_html(self):
        """Process the html

        Long delays between posting necessitate a few extra warnings around
        Years and months missing

        :return: None
        """
        if self.html is None:
            logger.warning("No opinions yet posted for year")
            return

        for row in self.html.xpath("//table/tbody/tr/td[a]/.."):
            cells = row.xpath("./td")

            raw_name = cells[1].text_content().strip()
            raw_date = cells[2].text_content().strip()

            self.cases.append(
                {
                    "name": titlecase(raw_name),
                    "url": row.xpath(".//a/@href")[0],
                    "docket": cells[0].text_content().strip(),
                    "date": str(parse(raw_date, languages=["es"]).date()),
                }
            )

    def make_backscrape_iterable(self, kwargs):
        """Generate backscrape iterable

        Generate spanish language year month slug to be used in scraping

        :return None
        """
        start = kwargs.get("backscrape_start") or self.first_opinion_date
        end = kwargs.get("backscrape_end") or self.today

        start_date = datetime.strptime(start, "%Y/%m/%d").date()
        end_date = datetime.strptime(end, "%Y/%m/%d").date()

        current = start_date.replace(day=1)

        months = []
        while current <= end_date.replace(day=1):
            months.append(self.format_spanish_month_year(current))
            current += relativedelta(months=1)

        self.back_scrape_iterable = months

    def _download_backwards(self, year_month: str):
        """Download backwards

        :param year_month: spanish year month used to generate url
        :return None
        """
        self.is_backscrape = True
        logger.info("Backscraping for %s", year_month)
        self.url = f"{self.base_url}/decisiones-del-tribunal-de-apelaciones-{year_month}/"
        self.html = self._download()
        self._process_html()

    def format_spanish_month_year(self, datetime_obj: datetime) -> str:
        """Generate month year slug in spanish

        Use this method to avoid issues with changing locale to spanish

        :param datetime_obj: Datetime obj
        :return: spanish month year slug
        """
        SPANISH_MONTHS = [
            None,
            "enero",
            "febrero",
            "marzo",
            "abril",
            "mayo",
            "junio",
            "julio",
            "agosto",
            "septiembre",
            "octubre",
            "noviembre",
            "diciembre",
        ]

        return f"{SPANISH_MONTHS[datetime_obj.month]}-{datetime_obj.year}"
