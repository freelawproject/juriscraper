from juriscraper.lib.html_utils import get_html5_parsed_text
from juriscraper.opinions.united_states.federal_appellate import ca11_p


class Site(ca11_p.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://media.ca11.uscourts.gov/opinions/unpub/logname.php"
        self.court_id = self.__module__
        self.back_scrape_iterable = list(range(20, 22000, 20))
        self.should_have_results = True

    def _make_html_tree(self, text):
        return get_html5_parsed_text(text)

    def _download_backwards(self, n):
        self.url = f"http://media.ca11.uscourts.gov/opinions/unpub/logname.php?begin={n}&num={n / 20 - 1}&numBegin=1"

        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
