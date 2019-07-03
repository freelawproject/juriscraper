import requests
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
from ..lib.log_tools import make_default_logger
from urllib import urlencode
logger = make_default_logger()
from lxml.html import fromstring as f

class LASC_Session(object):
    def __init__(self, username=None, password=None):
        super(LASC_Session, self).__init__()

        self.s = requests.session()
        self.html = None

        # Los Angeles Superior Court MAP urls and paths
        self.la_domain = 'https://media.lacourt.org'

        self.la_signin_path = "/signin-oidc"
        self.la_login_path = "/api/Account/Login"

        self.la_login_url = '%s%s' % (self.la_domain, self.la_login_path)
        self.la_signin_url = "%s%s" % (self.la_domain, self.la_signin_path)

        # Microsoft urls and paths
        self.micro_domain = "https://login.microsoftonline.com"
        self.api_base_path = "/calcourts02b2c.onmicrosoft.com/B2C_1_Media-LASC-SUSI/"

        self.api1 = "SelfAsserted?"
        self.api2 = "api/CombinedSigninAndSignup/confirmed?"

        self.api_path1 = "%s%s" % (self.api_base_path, self.api1)
        self.api_path2 = "%s%s" % (self.api_base_path, self.api2)

        self.api_call1 = "%s%s{url_encoding1}" % (self.micro_domain, self.api_path1)
        self.api_call2 = "%s%s{url_encoding2}" % (self.micro_domain, self.api_path2)

        # Login Post Data
        self.data = {
            "logonIdentifier": username,
            "password": password,
            "request_type": "RESPONSE"
        }

        self.data2 = {}

        self.url_encoding1 = {"p":"B2C_1_Media-LASC-SUSI",
                              "tx":""}

        self.url_encoding2 = {"p":"B2C_1_Media-LASC-SUSI"}

        self.headers = {
            "Origin": self.micro_domain,
            "User-Agent": "Juriscraper",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest"
        }


    def login(self):
        logger.info(u'Attempting LASC MAP login')

        # Initialize connection to LASC MAP
        self.s.get(self.la_domain)

        # Redirect to login page
        self.html = self.s.get(self.la_login_url, timeout=30).text

        # Parse tokens and key data from html of Microsoft login page
        self.parse_html_for_keys()

        # Call Part one of Microsoft login API
        self.s.post(self.api_call1.format(url_encoding1=urlencode(self.url_encoding1)), headers=self.headers, data=self.data, timeout=30)

        # Call Part two of Microsoft login API - Redirect
        self.html = self.s.get(self.api_call2.format(url_encoding2 = urlencode(self.url_encoding2)), headers=self.headers, timeout=30).text

        # Parse the current page for new key data
        self.parse_new_html_for_keys()

        # Finalize login with post into LA MAP site
        self.s.post(self.la_signin_url, headers=self.headers, data=self.data2, timeout=30)


    # This is a setting required to continue
    def parse_html_for_keys(self):
        # CSRF Token
        self.csrf = self.html.split("csrf")[1].split("\"")[2]
        self.transid = self.html.split("transId")[1].split("\"")[2]

        self.headers['X-CSRF-TOKEN'] = self.csrf

        self.url_encoding1['tx'] = self.transid

        self.url_encoding2['csrf_token'] = self.csrf
        self.url_encoding2['TRANSID'] = self.transid


    # Xpath added
    def parse_new_html_for_keys(self):
        # Parse HTML with LXML by Xpath.
        j = f(self.html)

        self.data2['code'] = j.xpath('//*[@id="code"]')[0].value
        self.data2['id_token'] = j.xpath('//*[@id="id_token"]')[0].value
        self.data2['state'] = j.xpath('//*[@id="state"]')[0].value


