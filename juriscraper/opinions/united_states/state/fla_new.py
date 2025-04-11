from datetime import date, datetime, timedelta
import \
    json

import \
    requests

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_code='68f021c4-6a44-4735-9a76-5360b2e8af13'

    def _process_html(self):
        results = self.html['_embedded']['results']
        i=0
        for result in results:
            if result['caseHeader']['closedFlag']:
                case_id=result['caseHeader']['caseInstanceUUID']
                html_url=f"https://acis-api.flcourts.gov/courts/{self.court_code}/cms/cases/{case_id}/docketentries?page=0&size=20&sort=docketEntryHeader.filedDate%2Cdesc"
                # Hitting html page
                response1 = requests.get(url=html_url,headers={"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"},proxies={"http": "206.206.124.133:6714", "https": "206.206.124.133:6714"},timeout=120)
                link_details=json.loads(response1.text)
                disposition = link_details["_embedded"]["results"][0]["docketEntryHeader"]['docketEntryName']
                summary =link_details["_embedded"]["results"][0]["docketEntryHeader"]['docketEntryDescription']

                pdf_link_id = link_details['_embedded']['results'][0]['docketEntryHeader']['docketEntryUUID']
                link2=f"https://acis-api.flcourts.gov/courts/cms/docketentrydocumentsaccess?page=0&size=10&sort=documentName%2Casc&caseHeader.courtID={self.court_code}&docketEntryHeader.docketEntryUUID={pdf_link_id}&caseHeader.caseInstanceUUID={case_id}"
                # print(link2)
                # Hitting dialog box for pdf url
                response2 = requests.get(url=link2, headers={"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"}, proxies={"http": "206.206.124.133:6714", "https": "206.206.124.133:6714"}, timeout=120)
                pdf_url_details = dict(json.loads(response2.text))
                if not pdf_url_details.__contains__("_embedded"):
                    continue
                pdf_url_id = pdf_url_details["_embedded"]["results"][0]["documentLinkUUID"]
                # Creating pdf Url
                pdf_url=f'https://acis-api.flcourts.gov/courts/{self.court_code}/cms/case/{case_id}/docketentrydocuments/{pdf_url_id}'

                docket = result['caseHeader']['caseNumber']
                title = result['caseHeader']['caseTitle']
                date = result['caseHeader']['filedDate']
                i+=1
                self.cases.append({
                    "url":pdf_url,
                    "docket": [docket],
                    "name": title,
                    "date": date,
                    "summary":summary,
                    "disposition":disposition,
                    "status": "Published",
                })

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        page=0
        s_date = start_date.strftime("%Y-%m-%d")
        e_date = end_date.strftime("%Y-%m-%d")
        end_page=1
        #        0 < 1
        while page < end_page:
            self.url=f'https://acis-api.flcourts.gov/courts/cms/cases?caseHeader.filedDateFrom={s_date}T00%3A00%3A00.001%2B05%3A30&caseHeader.filedDateTo={e_date}T23%3A59%3A59.900%2B05%3A30&caseHeader.courtID={self.court_code}&page={page}&size=25&sort=caseHeader.filedDate%2Cdesc'
            self.parse()
            self.downloader_executed=False
            end_page = self.html['page']['totalPages']
            page+=1

        return 0

    def get_class_name(self):
        return "fla_new"

    def get_court_type(self):
        return "state"

    def get_state_name(self):
        return "Florida"

    def get_court_name(self):
        return "Supreme Court of Florida"
