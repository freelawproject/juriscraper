from datetime import datetime, date

from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.lib.html_utils import get_row_column_text, get_row_column_links
from juriscraper.lib.date_utils import unique_year_month
from juriscraper.AbstractSite import logger

class Site(OpinionSiteLinear):
    first_opinion_date = datetime(2019, 7, 17)
    days_interval = 28  # Monthly interval
    abbreviation_to_lower_court = { 
        "Caddo": "First Judicial District Court for the Parish of Caddo, Louisiana",
        "Ouachita": "Fourth Judicial District Court for the Parish of Ouachita, Louisiana", 
        "Bossier": "Twenty-Sixth Judicial District Court for the Parish of Bossier, Louisiana",
        "DeSoto": "Forty-Second Judicial District Court for the Parish of DeSoto, Louisiana",
        "Lincoln": "Third Judicial District Court for the Parish of Lincoln, Louisiana",
        "Webster": "Twenty-Sixth Judicial District Court for the Parish of Webster, Louisiana",
        "Franklin": "Fifth Judicial District Court for the Parish of Franklin, Louisiana",
        "Richland": "Fifth Judicial District Court for the Parish of Richland, Louisiana",
        "Union": "Third Judicial District Court for the Parish of Union, Louisiana",
        "Winn": "Eighth Judicial District Court for the Parish of Winn, Louisiana",
        "Morehouse": "Fourth Judicial District Court for the Parish of Morehouse, Louisiana",
        "Claiborne": "Second Judicial District Court for the Parish of Claiborne, Louisiana",
        "Ouachita Monroe City Court": "Monroe City Court for the Parish of Ouachita, Louisiana",
        "Bienville": "Second Judicial District Court for the Parish of Bienville, Louisiana",
        "Madison": "Sixth Judicial District Court for the Parish of Madison, Louisiana",
        "Red River": "Ninth Judicial District Court for the Parish of Red River, Louisiana",
        "Tensas": "Sixth Judicial District Court for the Parish of Tensas, Louisiana",
        "Jackson": "Second Judicial District Court for the Parish of Jackson, Louisiana",
        "Ouachita OWC District 1-E": "Office of Workers' Compensation District 1-E for the Parish of Ouachita, Louisiana",
        "Caddo OWC District 1-W": "Office of Workers' Compensation District 1-W for the Parish of Caddo, Louisiana",
        "Caldwell": "Thirty-Seventh Judicial District Court for the Parish of Caldwell, Louisiana",
        "West Carroll": "Fifth Judicial District Court for the Parish of West Carroll, Louisiana",
        "East Carroll": "Sixth Judicial District Court for the Parish of East Carroll, Louisiana",
        "Caddo Juvenile Court": "Juvenile Court for the Parish of Caddo, Louisiana",
        "Caddo Shreveport City Court": "Shreveport City Court for the Parish of Caddo, Louisiana",
        "DeSoto OWC District 1-W": "Office of Workers' Compensation District 1-W for the Parish of DeSoto, Louisiana",
        "Lincoln Ruston City Court": "Ruston City Court for the Parish of Lincoln, Louisiana",
        "Ouachita West Monroe City Court": "West Monroe City Court for the Parish of Ouachita, Louisiana",
        "OUACHITA Monroe City Court": "Monroe City Court for the Parish of Ouachita, Louisiana",
        "Franklin OWC District 1-E": "Office of Workers' Compensation District 1-E for the Parish of Franklin, Louisiana",
        "Minden City Court Webster": "Minden City Court for the Parish of Webster, Louisiana",
        "Morehouse Bastrop City Court": "Bastrop City Court for the Parish of Morehouse, Louisiana", 
        "Morehouse OWC District 1-E": "Office of Workers' Compensation District 1-E for the Parish of Morehouse, Louisiana",
        "Webster Minden City Court": "Minden City Court for the Parish of Webster, Louisiana",
        "Winn OWC District 2": "Office of Workers' Compensation District 2 for the Parish of Winn, Louisiana"
    }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://www.la2nd.org/opinions/"
        self.year = datetime.now().year
        self.url = f"{self.base_url}?opinion_year={self.year}"
        self.status = "Published"
        self.target_date = None
        self.make_backscrape_iterable(kwargs)

    def _download(self):
        html = super()._download()
        #Currenly there are no opinions for 2025, so we need to go back one year
        if html is not None:
            tables = html.cssselect('table#datatable')
            if not tables or not tables[0].cssselect('tbody tr'):
                self.year -= 1
                self.url = f"{self.base_url}?opinion_year={self.year}"
                return self._download()
        return html

    def _process_html(self):
        if self.html is None:
            return
        
        tables = self.html.cssselect('table#datatable')
        if not tables or not tables[0].cssselect("tbody tr"):
            return
        
        logger.info(f"Processing cases for year: {self.year}")
        for row in tables[0].cssselect('tbody tr'):
            case_date = datetime.strptime(
                get_row_column_text(row, 1), 
                '%m/%d/%Y'
            ).date()
            
            if self.skip_row_by_date(case_date):
                continue

            author = get_row_column_text(row, 4)
            clean_author = self.clean_judge_name(author)        
            
            # Get the lower court abbreviation
            lower_court_abbr = get_row_column_text(row, 6)
            
            # Replace abbreviation with full name
            lower_court_full = self.abbreviation_to_lower_court.get(lower_court_abbr, lower_court_abbr)
            
            self.cases.append({
                "date": get_row_column_text(row, 1),
                "docket": get_row_column_text(row, 2),
                "name": get_row_column_text(row, 3),
                "author": clean_author,
                "disposition": get_row_column_text(row, 5),
                "lower_court": lower_court_full, 
                "url": get_row_column_links(row, 8),
            })
        
    def skip_row_by_date(self, case_date):
        """Determine if a row should be skipped based on the case date."""
        # Skip if before first opinion date
        if case_date < self.first_opinion_date.date():
            return True

    def clean_judge_name(self, name):
        """Remove everything after a comma in the judge's name."""
        return name.split(',')[0].strip()

    def _download_backwards(self, target_year: int) -> None:
        logger.info(f"Backscraping for date: {target_year}")
        self.year = target_year
        self.url = f"{self.base_url}?opinion_year={self.year}"

        #Pagination not required, all the opinions data is sent in the first request
        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Sets up the back scrape iterable using start and end year arguments.

        :param kwargs: passed when initializing the scraper, may or
            may not contain backscrape controlling arguments
        :return: None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        # Convert start and end to integers, defaulting to the scraper's start and current year
        start = int(start) if start else self.first_opinion_date.year
        end = int(end) + 1 if end else datetime.now().year + 1

        # Create a range of years for back scraping
        self.back_scrape_iterable = range(start, end)