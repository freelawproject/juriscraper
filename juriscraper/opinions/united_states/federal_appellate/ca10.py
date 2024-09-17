from datetime import datetime

from bs4 import BeautifulSoup
from lxml import html
from lxml.etree import tostring
from six import text_type

from casemine.casemine_util import CasemineUtil
from juriscraper.lib.html_utils import fix_links_in_lxml_tree
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__

    def _process_html_2(self):
        for item in self.html.xpath(".//item"):
            for e in item.xpath(
                ".//description/text()",
                namespaces={"dc": "http://purl.org/dc/elements/1.1/"},
            ):
                if "Published Opinion" in e:
                    status = "Published"
                else:
                    status = "Unpublished"
                docket = e.split()[1].strip()
            date = convert_date_string(item.xpath(".//pubdate/text()")[0])
            formatted_date = date.strftime("%Y-%m-%d")
            self.cases.append(
                {
                    "url": html.tostring(item.xpath("link")[0], method="text")
                    .decode()
                    .replace("\\n", "")
                    .strip(),
                    "name": item.xpath(".//title/text()")[0],
                    "date": formatted_date,
                    "status": status,
                    "docket": docket,
                }
            )

    def _process_html(self):
        data = tostring(self.html).decode('utf-8')
        soup = BeautifulSoup(data, 'html.parser')
        div = soup.find('div', class_='view-content')
        table = div.find('table')
        tbody = table.find('tbody')
        trs = tbody.findAll("tr")
        for tr in trs:
            tds = tr.findAll('td')
            docket = tds[0].text.replace('\n','').strip()
            name = tds[1].text.replace('\n','').strip()
            date = tds[2].text.replace('\n','').strip()
            lower_court = tds[3].text.replace('\n','').strip()
            pdf_url = tds[4].find('a').attrs.get('href')
            self.cases.append({"url": pdf_url,
                               "name": name,
                               "date": date,
                               "status": "Published",
                               "docket": docket, }
                              )


    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        start_date1 = start_date.strftime('%Y/%m/%d')
        end_date1 = end_date.strftime('%Y/%m/%d')
        sdate = start_date1.split('/')
        edate = end_date1.split('/')
        page = 0
        # flag=True
        while(True):
            self.url = 'https://www.ca10.uscourts.gov/opinion/search?combine=&parties=&judges=&field_opinion_date_value%5Bmin%5D%5Bdate%5D='+str(sdate[1])+'%2F'+str(sdate[2])+'%2F'+str(sdate[0])+'&field_opinion_date_value%5Bmax%5D%5Bdate%5D='+str(edate[1])+'%2F'+str(edate[2])+'%2F'+str(edate[0])+'&exclude=&page='+str(page)
            if not self.downloader_executed:
                # Run the downloader if it hasn't been run already
                self.html = self._download()

                # Process the available html (optional)
                data = tostring(self.html).decode('utf-8')
                soup = BeautifulSoup(data, 'html.parser')
                div = soup.find('div', class_='view-content')
                if (div is None):
                    self.downloader_executed=False
                    break
                table = div.find('table')
                tbody = table.find('tbody')
                trs = tbody.findAll("tr")
                for tr in trs:
                    tds = tr.findAll('td')
                    docket = tds[0].text.replace('\n', '').strip()
                    name = tds[1].text.replace('\n', '').strip()
                    date = tds[2].text.replace('\n', '').strip()
                    date_object = datetime.strptime(date, '%m/%d/%Y')
                    date_filed = date_object.strftime('%d/%m/%Y')
                    res = CasemineUtil.compare_date(date_filed,self.crawled_till)
                    if (res == 1):
                        self.crawled_till = date_filed
                    lower_court = tds[3].text.replace('\n', '').strip()
                    pdf_url = tds[4].find('a').attrs.get('href')
                    self.cases.append(
                        {"url": pdf_url, "name": name, "date": date,
                         "status": "Published", "docket": docket, "lower_court":lower_court})
                self.downloader_executed = False

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
            page = page+1

            # Set the attribute to the return value from _get_foo()
            # e.g., this does self.case_names = _get_case_names()

            # return self
        return 0
