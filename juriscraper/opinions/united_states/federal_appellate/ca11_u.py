from juriscraper.lib.html_utils import get_html5_parsed_text
from juriscraper.opinions.united_states.federal_appellate import ca11_p


class Site(ca11_p.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://media.ca11.uscourts.gov/opinions/unpub/logname.php'
        self.court_id = self.__module__
        self.back_scrape_iterable = range(20, 22000, 20)

    def _make_html_tree(self, text):
        return get_html5_parsed_text(text)

    def _download_backwards(self, n):
        self.url = 'http://media.ca11.uscourts.gov/opinions/unpub/logname.php?begin={}&num={}&numBegin=1'.format(
            n,
            n/20 - 1
        )

        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
