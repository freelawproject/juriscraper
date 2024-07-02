from datetime import datetime

from juriscraper.opinions.united_states_backscrapers.state import mass


class Site(mass.Site):
    backscrape_date_range_mapper = [
        {
            "start": datetime(2021, 7, 9),
            "end": None,
            "url": "http://masscases.com/app100-124.html",
        },
        {
            "start": datetime(2009, 8, 20),
            "end": datetime(2021, 5, 12),
            "url": "http://masscases.com/app75-99.html",
        },
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__

    def extract_from_text(self, scraped_text: str) -> dict:
        """Check comment on backscraper parent class"""
        return {}
