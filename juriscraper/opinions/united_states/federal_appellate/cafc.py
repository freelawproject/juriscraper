from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.cafc.uscourts.gov/opinions-orders?field_origin_value=All&field_report_type_value=All'
        self.back_scrape_iterable = range(1, 700)
        self.court_id = self.__module__

    def _download(self, request_dict={}):
        html = super(Site, self)._download(request_dict)
        self._extract_cases_from_html(html)
        return html

    def _extract_cases_from_html(self, html):
        """Build list of data dictionaries, one dictionary per case (table row)."""
        self.cases = []

        for row in html.xpath('//table/tbody/tr'):
            date, docket, url, name, status = False, False, False, False, False

            date = convert_date_string(row.xpath('td[1]/span/text()')[0])
            docket = row.xpath('td[2]/text()')[0].strip()

            url_raw = row.xpath('td[4]/a/@href')
            if url_raw:
                url = url_raw[0]

            name_raw = row.xpath('td[4]/a/text()')
            if name_raw:
                name = titlecase(name_raw[0].split('[')[0].strip())

            status_raw = row.xpath('td[5]/text()')
            if status_raw:
                status_raw = status_raw[0].strip().lower()
                if 'nonprecedential' in status_raw.lower():
                    status = 'Unpublished'
                elif 'precedential' in status_raw.lower():
                    status = 'Published'
                else:
                    status = 'Unknown'

            if date and docket and url and name and status:
                self.cases.append({
                    'date': date,
                    'docket': docket,
                    'url': url,
                    'name': name,
                    'status': status,
                })

    def _get_case_names(self):
        return [case['name'] for case in self.cases]

    def _get_download_urls(self):
        return list(self.html.xpath('//table//tr/td[4]/a/@href'))

    def _get_case_dates(self):
        return [case['date'] for case in self.cases]

    def _get_docket_numbers(self):
        return [case['docket'] for case in self.cases]

    def _get_precedential_statuses(self):
        return [case['status'] for case in self.cases]

    def _download_backwards(self, n):
        self.url = "http://www.cafc.uscourts.gov/opinions-orders?page={}".format(n)

        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
