import requests
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
from ..lib.log_tools import make_default_logger
logger = make_default_logger()


class LASCSession(object):
    def __init__(self, cookies=None, username=None, password=None):
        super(LASCSession, self).__init__()

        self.s = requests.session()
        self.html = ""

        self.base_url = 'https://media.lacourt.org'
        self.login_url = 'https://media.lacourt.org/api/Account/Login'
        self.post_url = "https://login.microsoftonline.com/calcourts02b2c.onmicrosoft.com/" \
                        "B2C_1_Media-LASC-SUSI/SelfAsserted?tx=%s&p=B2C_1_Media-LASC-SUSI"
        self.post_url2 = "https://media.lacourt.org/signin-oidc"
        self.fetch_url = "https://media.lacourt.org/api/AzureApi/GetCaseDetail/%s"
        self.case_url = None
        self.case_data = None

        self.microsoft_login = "https://login.microsoftonline.com/calcourts02b2c.onmicrosoft.com/B2C_1_Media-LASC-SUSI/" \
                               "api/CombinedSigninAndSignup/confirmed?csrf_token={CSRF}&tx={TRANSID}&p=B2C_1_Media-LASC-SUSI" \
                               "&diags=%7B%22pageViewId%22%3A%22955aa286-f9d8-43de-b867-fb48bc4e08a3%22%2C%22pageId%22%3A%22" \
                               "CombinedSigninAndSignup%22%2C%22trace%22%3A%5B%7B%22ac%22%3A%22T005%22%2C%22acST%22%3A1559936193" \
                               "%2C%22acD%22%3A2%7D%2C%7B%22ac%22%3A%22T021%20-%20URL%3Ahttps%3A%2F%2Flascproduction.blob.core.windows.net" \
                               "%2Fb2clascbranding%2Flasc%2Funified.html%22%2C%22acST%22%3A1559936193%2C%22acD%22%3A111%7D%2C%7B%22" \
                               "ac%22%3A%22T029%22%2C%22acST%22%3A1559936193%2C%22acD%22%3A8%7D%2C%7B%22ac%22%3A%22T004%22%2C%22a" \
                               "cST%22%3A1559936193%2C%22acD%22%3A3%7D%2C%7B%22ac%22%3A%22T019%22%2C%22acST%22%3A1559936193%2C%22a" \
                               "cD%22%3A16%7D%2C%7B%22ac%22%3A%22T003%22%2C%22acST%22%3A1559936193%2C%22acD%22%3A13%7D%2C%7B%22a" \
                               "c%22%3A%22T002%22%2C%22acST%22%3A0%2C%22acD%22%3A0%7D%5D%7D"

        self.data = {
            "logonIdentifier": username,
            "password": password,
            "request_type": "RESPONSE"
        }

        self.data2 = {}

        self.headers = {
            "Origin": "https://login.microsoftonline.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/74.0.3729.169 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest"
        }


    def log_into_map(self):
        logger.info(u'Attempting LASC MAP login')

        self.s.get(self.base_url, verify=False, allow_redirects=True)
        self.html = self.s.get(self.login_url, verify=False, allow_redirects=True).text

        self.extract_csrf_token()
        self.extract_trans_id()

        self.post_url = self.post_url % (self.transid)
        self.s.post(self.post_url, headers=self.headers, data=self.data, allow_redirects=True, verify=False)

        self.create_login_url()
        self.html = self.s.get(self.second_post, headers=self.headers).text

        # A second login is required within the azure, microsoft court login.
        self.make_second_post_data()
        self.html = self.s.post(self.post_url2, headers=self.headers, allow_redirects=True, data=self.data2)



    def extract_csrf_token(self):
        self.csrf = self.html.split("csrf")[1].split("\"")[2]
        self.headers['X-CSRF-TOKEN'] = self.html.split("csrf")[1].split("\"")[2]

    def extract_trans_id(self):
        self.transid = self.html.split("transId")[1].split("\"")[2]

    def create_login_url(self):
        self.second_post = self.microsoft_login.format(
            CSRF = self.headers['X-CSRF-TOKEN'],
            TRANSID = self.transid
            )

    #this is hidden in javasript so harder to grab then lxml path
    def make_second_post_data(self):
        self.data2['code'] = self.html.split("id='code' value='")[1].split("'")[0]
        self.data2['id_token'] = self.html.split("id='id_token' value='")[1].split("'")[0]
        self.data2['state'] = self.html.split("id='state' value='")[1].split("'")[0]


    # This returns the JSON value of the store
    def get_json_from_internal_case_id(self, internal_case_id):
        self.case_url = self.fetch_url % (internal_case_id)
        self.case_data = self.s.get(self.case_url, verify=False, allow_redirects=True).text


