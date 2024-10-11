# Editor: mlr
# Maintenance log
#    Date     | Issue
# 2013-01-28  | InsanityException due to the court adding busted share links.
# 2014-07-02  | New website required rewrite.

from datetime import datetime

from casemine.casemine_util import CasemineUtil
from juriscraper.lib.string_utils import clean_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    title = []
    dates = []
    urls = []
    status = []
    dockets = []
    nature = []
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.back_scrape_iterable = list(range(20, 10000, 20))

    def _get_case_names(self):
        return self.title

    def _get_download_urls(self):
        return self.urls

    def _get_case_dates(self):
        return self.dates

    def _get_docket_numbers(self):
        return self.dockets

    def _get_precedential_statuses(self):
        if "unpub" in self.url:
            return ["Unpublished"] * len(self.case_names)
        else:
            return ["Published"] * len(self.case_names)

    def _get_nature_of_suit(self):
        return self.nature

    def _download_backwards(self, n):
        self.url = "http://media.ca11.uscourts.gov/opinions/pub/logname.php?begin={}&num={}&numBegin=1".format(
            n, int( n / 20 )
        )

        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        num = 1
        begin = 0
        numbegin = 1
        flag = True
        while(flag):
            if(self.get_class_name().__eq__("ca11_p")):
                self.url = 'https://media.ca11.uscourts.gov/opinions/pub/logname.php?begin='+str(begin)+'&num='+str(num)+'&numBegin='+str(numbegin)
            else:
                self.url = 'http://media.ca11.uscourts.gov/opinions/unpub/logname.php?begin='+str(begin)+'&num='+str(num)+'&numBegin='+str(numbegin)

            if not self.downloader_executed:
                # Run the downloader if it hasn't been run already
                self.html = self._download()

                # Process the available html (optional)
                for e in self.html.xpath("//tr[./td[1]/a//text()]/td[1]//text()"):
                    self.title.append(e)

                for e in self.html.xpath("//tr[./td[1]/a//text()]/td[1]/a/@href"):
                    self.urls.append(e)

                for date_string in self.html.xpath(
                    "//tr[./td[1]/a//text()]/td[5]//text()"):
                    s = clean_string(date_string)
                    if s == "00-00-0000" and "begin=21160" in self.url:
                        # Bad data found during backscrape.
                        s = "12-13-2006"
                    date_obj = datetime.strptime(clean_string(s), "%m-%d-%Y").date()
                    formatted_date = date_obj.strftime("%d/%m/%Y")
                    res = CasemineUtil.compare_date(formatted_date,self.crawled_till)
                    if(res==-1):
                        flag=False

                    self.dates.append(date_obj)

                for e in self.html.xpath("//tr[./td[1]/a//text()]/td[2]//text()"):
                    doc=[e]
                    self.dockets.append(doc)

                for e in self.html.xpath("//tr[./td[1]/a//text()]/td[4]//text()"):
                    self.nature.append(e)
                self.downloader_executed = False
                num = num + 1
                begin = begin + 20
                # if (num == 5):
                #     break
                if (num == 20):
                    numbegin = numbegin + 20
        # Set the attribute to the return value from _get_foo()
        # e.g., this does self.case_names = _get_case_names()
        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())
        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            # This needs to be done *after* _clean_attributes() has been run.
            # The current architecture means this gets run twice. Once when we
            # iterate over _all_attrs, and again here. It's pretty cheap though.
            self.case_name_shorts = self._get_case_name_shorts()
            self._post_parse()
            self._check_sanity()
            self._date_sort()
            self._make_hash()
        return 0

    def get_class_name(self):
        return "ca11_p"

    def get_court_name(self):
        return 'United States Court Of Appeals For The Eleventh Circuit'

    def get_court_type(self):
        return 'Federal'
