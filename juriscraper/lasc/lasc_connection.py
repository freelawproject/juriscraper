import requests, json
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
from ..lib.log_tools import make_default_logger
from urllib import urlencode
logger = make_default_logger()
from lxml.html import fromstring as f

# strengthen comments
# login commentary, http.py file 202 onward...

class LASC_Session(requests.Session):
    """
    Extension for Courtlistner to connect into the Los Angeles
    Superior Court Media Access Portal.

    """

    def __init__(self, username=None, password=None):
        """
        Instantiate a new LASC HTTP Session with some Juriscraper defaults.
        This method requires credentials from the media access portal to

        :param username: media access portal credentials
        :param password: media access portal credentials

        """


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

        self.api_call1 = "%s%s" % (self.micro_domain, self.api_path1)
        self.api_call2 = "%s%s" % (self.micro_domain, self.api_path2)

        # Login Post Data
        self.data = {
            "logonIdentifier": username,
            "password": password,
            "request_type": "RESPONSE"
        }

        self.data2 = {}

        self.bsc_param = "B2C_1_Media-LASC-SUSI"
        self.api_params1 = {"p":self.bsc_param, "tx":""}

        self.api_params2 = {"p":self.bsc_param}

        self.headers = {
            "Origin": self.micro_domain,
            "User-Agent": "Juriscraper",
        }

    def get(self, url, auto_login=False, **kwargs):
        """Overrides request.Session.get with session retry logic.

        Use it to import very obvious functions.

        :param url: url string to GET
        :param auto_login: Whether the auto-login procedure should happen.
        :return: requests.Response
        """

        kwargs.setdefault('headers', self.headers)
        kwargs.setdefault('timeout', 30)

        r = self.s.get(url, **kwargs)

        return r

    def post(self, url, auto_login=False, **kwargs):
        """Overrides request.Session.get with session retry logic.

        :param url: url string to GET
        :param auto_login: Whether the auto-login procedure should happen.
        :return: requests.Response
        """

        kwargs.setdefault('headers', self.headers)
        kwargs.setdefault('timeout', 30)

        r = self.s.post(url, **kwargs)

        return r


    def login(self):
        """
        Logging into Media Access Portal.
        If you have media access credentials and permission two GET request and two POST requests
        You need to collect the transID/tx cookie value and X-CSRF-TOKEN from hidden form inputs during the process
        You also need to identify a "state, id_token and code" values as parameters during the process.

        If you do *not* have media access permissions you can not log into the media access portal.

        More details coming for the four requests.

        A session is required.

        The first request ...
        =====================

        The second request ...
        =====================

        The third request ...
        =====================

        The fourth request ...
        =====================

        """

        logger.info(u'Attempting LASC MAP login')

        # Load the page in order to get the TransID and CSFR Token values from the HTML
        self.html = self.get(self.la_login_url).text

        # Parse token and ID from html of LA Login Page
        self.parse_html_for_keys()

        # Call Part one of Microsoft login API
        r = self.post(self.api_call1, params=self.api_params1, data=self.data)

        # Error handling for authentication.
        if json.loads(r.content)['status'] != "200":
            if u'Your password is incorrect' in json.loads(r.content)['message']:
                logger.info(u'Password was incorrect')
                raise LASCLoginException("Invalid username/password")

            if u'We can\'t seem to find your account' in json.loads(r.content)['message']:
                logger.info(u'Invalid Email Address')
                raise LASCLoginException("Invalid Email Address")

        # Call Part two of Microsoft login API - Redirect
        self.html = self.get(self.api_call2, params=self.api_params2 ).text

        # Parse the current page for new key data
        self.parse_new_html_for_keys()

        # Finalize login with post into LA MAP site
        self.post(self.la_signin_url, data=self.data2)
        logger.info(u'Successfully Logged into MAP')


    def parse_html_for_keys(self):
        """
        This method parses the HTML after the first login page and idenitifies the two parameter values
        Both parameters are required and both are used multiple times.

        :return:

        """

        self.csrf = self.html.split("csrf")[1].split("\"")[2]
        self.transid = self.html.split("transId")[1].split("\"")[2]

        self.headers['X-CSRF-TOKEN'] = self.csrf

        self.api_params1['tx'] = self.transid

        self.api_params2['csrf_token'] = self.csrf
        self.api_params2['TRANSID'] = self.transid



    def parse_new_html_for_keys(self):
        """
        This method parses the HTML after the first login page and idenitifies the three parameter values required.
        the f method comes from lxml.html import fromstring as f


        :return:
        """
        # Parse HTML with LXML by Xpath.
        j = f(self.html)

        self.data2['code'] = j.xpath('//*[@id="code"]')[0].value
        self.data2['id_token'] = j.xpath('//*[@id="id_token"]')[0].value
        self.data2['state'] = j.xpath('//*[@id="state"]')[0].value



class LASCLoginException(Exception):

    """
    Raised when the system cannot authenticate with LASC MAP
    """

    def __init__(self, message):
        Exception.__init__(self, message)

