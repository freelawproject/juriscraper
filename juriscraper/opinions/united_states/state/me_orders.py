from datetime import datetime

from bs4 import BeautifulSoup
from lxml import html

from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite
from juriscraper.opinions.united_states.state import me


class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.courts.maine.gov/courts/sjc/opinions.html"
        self.court_id = self.__module__

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.cases)

    def _process_html(self):
        table = self.html.xpath(
            "//table[@class='tbstriped']//tr[count(td//a) = 2]")
        for tr in table:
            table_text = html.tostring(tr, pretty_print=True).decode()
            # print(table_text)
            soup = BeautifulSoup(table_text, 'html.parser')
            tds = soup.find_all('td')
            cite = tds[0].text
            last_link = str(tds[1].find_all_next("a")[1])
            last_link = last_link[
                        last_link.index('href') + 6:last_link.index('pdf') + 3]
            title = tds[1].text.replace("\n", "")
            cleaned_text = ' '.join(title.split())
            date = tds[2].text
            formatted_date = datetime.strptime(date, "%B %d, %Y").strftime(
                "%m/%d/%Y")
            self.cases.append({
                "url": last_link,
                "name": cleaned_text,
                "docket": [],
                "date": formatted_date,
                "citation": [cite]
            })

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.parse()
        return 0

    def get_class_name(self):
        return "me_orders"

    def get_court_name(self):
        return "Maine Supreme Judicial Court"

    def get_court_type(self):
        return "state"

    def get_state_name(self):
        return "Maine"

