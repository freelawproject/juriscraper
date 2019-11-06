import requests
from lxml import html
from selenium.webdriver.firefox.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

class PublicSession(object):
    """
    This requires a different version of selenium and firefox webdriver
    Session needs major revisions but is a being pushed to test on a
    experimental task-server docker install.
    """
    def __init__(self, docket_number=None):
        self.data = {
            '__VIEWSTATE' : "",
            '__VIEWSTATEGENERATOR': "",
            '_ctl0:_ctl0:siteMasterHolder:basicBodyHolder:userId': "GUEST",
            'login': "Continue as Guest",
            'passwd': "",
        }
        self.doc_ids = []
        self.s = requests.session()
        self.slug1 = "https://www.lacourt.org/paonlineservices/civilImages/waitpreview.aspx?id=%s&ct=CIVIL"
        self.slug2 = "http://ww2.lacourt.org/api/documents/v2/open/preview/%s(1).pdf"

        self.url1 = "http://www.lacourt.org/paonlineservices/civilImages/externalAppLink.aspx?casenumber=%s"
        self.url2 = "https://www.lacourt.org/paonlineservices/civilImages/searchByCaseNumberResult.aspx?caseNumber=%s"
        self.url3 = "https://www.lacourt.org/paonlineservices/pacommerce/login.aspx?appid=IMG&casetype=CIV"

        # self.url2 = None
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument("silent")
        options.add_experimental_option('w3c', False)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(chrome_options=options)
        self.docket_number = docket_number

    def launch_driver(self):
        self.driver.get("https://www.lacourt.org")

    def get_single_page_pdfs(self):
        """

        :param case_number:
        :return:
        """

        self.s.get(self.url1 % self.docket_number)
        self.s.get(self.url2 % self.docket_number)
        r = self.s.post(self.url3, data=self.data)

        soup = html.fromstring(r.text, "lxml")
        table = soup.xpath('//*[@id="_ctl0__ctl0_siteMasterHolder_basicBodyHolder_Table1"]')

        self.doc_ids = [x.name[8:] for x in table[0].xpath(".//input[@value='1-1']")]

    def get_all_first_page_pdfs(self):
        """

        :param case_number:
        :return:
        """

        self.s.get(self.url1 % self.docket_number)
        self.s.get(self.url2 % self.docket_number)
        r = self.s.post(self.url3, data=self.data)

        soup = html.fromstring(r.text, "lxml")
        table = soup.xpath('//*[@id="_ctl0__ctl0_siteMasterHolder_basicBodyHolder_Table1"]')

        self.doc_ids = [x.name[8:] for x in table[0].xpath(".//input[@class='pageListingInput']")]


    def generate_ff(self):
        """
        This method takes the cookies from the requests session to load up the
        PDFs neeeded.  Returns the list of PDFs opened.
        :return:
        """
        dict_resp_cookies = self.s.cookies.get_dict()
        response_cookies_browser = [{'name': name, 'value': value} for
                                    name, value in dict_resp_cookies.items()]

        [self.driver.add_cookie(c) for c in response_cookies_browser]

        for d in self.doc_ids:
            x1 = self.slug1 % d
            self.driver.get(x1)
            wait = WebDriverWait(self.driver, 10)
            wait.until(lambda driver: self.driver.current_url == self.slug2 % d)

        return self.doc_ids

class PublicFetch(object):
    """
    A requests.Session object with special tooling to handle the Los Angeles
    Superior Court Public Access Portal.
    """

    def __init__(self, s):
        self.session = s
        self.slug2 = "http://ww2.lacourt.org/api/documents/v2/open/preview/%s(1).pdf"


    def get_pdf(self, doc_id):
        url2 = self.slug2 % (doc_id)
        pdfstream = self.session.get(url2, allow_redirects=True).content
        return pdfstream
