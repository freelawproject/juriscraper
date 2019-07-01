import requests
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)


class LASCSession(object):
    def __init__(self, cookies=None, username=None, password=None):
        super(LASCSession, self).__init__()

        self.base_url = 'https://media.lacourt.org'
        self.login_url = 'https://media.lacourt.org/api/Account/Login'
        self.post_url = "https://login.microsoftonline.com/calcourts02b2c.onmicrosoft.com/B2C_1_Media-LASC-SUSI/SelfAsserted?tx=%s&p=B2C_1_Media-LASC-SUSI"
        self.post_url2 = "https://media.lacourt.org/signin-oidc"
        self.fetch_url = "https://media.lacourt.org/api/AzureApi/GetCaseDetail/%s"
        self.case_url = ""
        self.case_data = ""

        self.microsoft_login = "https://login.microsoftonline.com/calcourts02b2c.onmicrosoft.com/B2C_1_Media-LASC-SUSI/api/CombinedSigninAndSignup/confirmed?csrf_token={CSRF}&tx={TRANSID}&p=B2C_1_Media-LASC-SUSI&diags=%7B%22pageViewId%22%3A%22955aa286-f9d8-43de-b867-fb48bc4e08a3%22%2C%22pageId%22%3A%22CombinedSigninAndSignup%22%2C%22trace%22%3A%5B%7B%22ac%22%3A%22T005%22%2C%22acST%22%3A1559936193%2C%22acD%22%3A2%7D%2C%7B%22ac%22%3A%22T021%20-%20URL%3Ahttps%3A%2F%2Flascproduction.blob.core.windows.net%2Fb2clascbranding%2Flasc%2Funified.html%22%2C%22acST%22%3A1559936193%2C%22acD%22%3A111%7D%2C%7B%22ac%22%3A%22T029%22%2C%22acST%22%3A1559936193%2C%22acD%22%3A8%7D%2C%7B%22ac%22%3A%22T004%22%2C%22acST%22%3A1559936193%2C%22acD%22%3A3%7D%2C%7B%22ac%22%3A%22T019%22%2C%22acST%22%3A1559936193%2C%22acD%22%3A16%7D%2C%7B%22ac%22%3A%22T003%22%2C%22acST%22%3A1559936193%2C%22acD%22%3A13%7D%2C%7B%22ac%22%3A%22T002%22%2C%22acST%22%3A0%2C%22acD%22%3A0%7D%5D%7D"

        self.data = {
            "logonIdentifier": username,
            "password": password,
            "request_type": "RESPONSE"
        }

        self.data2 = {}

        self.headers = {
            "Origin": "https://login.microsoftonline.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest"
        }

        self.s = requests.session()
        self.html = ""

    def start_login(self):
        self.s.get(self.base_url, verify=False, allow_redirects=True)
        self.html = self.s.get(self.login_url, verify=False, allow_redirects=True).text

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

    def make_second_post_data(self):

        #this is hidden in javasript so harder to grab then lxml path
        self.data2['code'] = self.html.split("id='code' value='")[1].split("'")[0]
        self.data2['id_token'] = self.html.split("id='id_token' value='")[1].split("'")[0]
        self.data2['state'] = self.html.split("id='state' value='")[1].split("'")[0]

    def complete_login(self):
        self.post_url = self.post_url % (self.transid)

        self.s.post(self.post_url, headers=self.headers, data=self.data, allow_redirects=True, verify=False)

        self.create_login_url()

        self.html = self.s.get(self.second_post, headers=self.headers).text

        # A second login is required within the azure, microsoft court login.
        self.make_second_post_data()
        self.s.post(self.post_url2, headers=self.headers, allow_redirects=True, data=self.data2)

    # This returns the JSON value of the store
    def get_json_from_internal_case_id(self, internal_case_id):
        self.case_url = self.fetch_url % (internal_case_id)
        self.case_data = self.s.get(self.case_url, verify=False, allow_redirects=True).text

