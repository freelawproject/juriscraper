import requests
from lxml.html import fromstring
from ..lib.log_tools import make_default_logger

requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)

logger = make_default_logger()


class LASCSession(requests.Session):
    """
    A requests.Session object with special tooling to handle the Los Angeles
    Superior Court Media Access portal.
    """

    def __init__(self, username=None, password=None):
        """
        Instantiate a new LASC HTTP Session with some Juriscraper defaults.
        This method requires credentials from the media access portal.

        :param username: MAP username
        :param password: MAP password
        :return: A LASCSession object
        """
        super(LASCSession, self).__init__()

        self.html = None

        # Los Angeles Superior Court MAP urls and paths
        la_url = "https://media.lacourt.org"
        self.login_url = "%s/api/Account/Login" % la_url
        self.signin_url = "%s/signin-oidc" % la_url

        # Microsoft urls and paths
        ms_base_url = "https://login.microsoftonline.com"
        api_path1 = (
            "/calcourts02b2c.onmicrosoft.com/"
            "B2C_1_Media-LASC-SUSI/SelfAsserted?"
        )
        api_path2 = (
            "/calcourts02b2c.onmicrosoft.com/"
            "B2C_1_Media-LASC-SUSI/api/"
            "CombinedSigninAndSignup/confirmed?"
        )
        self.api_url1 = "%s%s" % (ms_base_url, api_path1)
        self.api_url2 = "%s%s" % (ms_base_url, api_path2)

        self.login_data = {
            "logonIdentifier": username,
            "password": password,
            "request_type": "RESPONSE",
        }
        self.headers = {
            "Origin": ms_base_url,
            "User-Agent": "Juriscraper",
        }

    def get(self, url, auto_login=False, **kwargs):
        """Overrides request.Session.get with session retry logic.

        :param url: url string to GET
        :param auto_login: Whether the auto-login procedure should happen.
        :return: requests.Response
        """
        kwargs.setdefault("timeout", 30)
        kwargs.setdefault("params", {"p": "B2C_1_Media-LASC-SUSI"})

        return super(LASCSession, self).get(url, **kwargs)

    def post(self, url, auto_login=False, **kwargs):
        """Overrides request.Session.post with session retry logic.

        :param url: url string to GET
        :param auto_login: Whether the auto-login procedure should happen.
        :return: requests.Response
        """
        kwargs.setdefault("timeout", 30)
        kwargs.setdefault("params", {"p": "B2C_1_Media-LASC-SUSI"})

        return super(LASCSession, self).post(url, **kwargs)

    @staticmethod
    def _parse_new_html_for_keys(r):
        """Parse the current page for new key data

        This method parses the HTML after the first login page and identifies
        the parameter values required for the next step.

        :param r: A request.Response object
        :return: A dict containing the needed keys
        """
        html = fromstring(r.text)
        return {
            "code": html.xpath('//*[@id="code"]')[0].value,
            "id_token": html.xpath('//*[@id="id_token"]')[0].value,
            "state": html.xpath('//*[@id="state"]')[0].value,
        }

    @staticmethod
    def _check_login(r):
        """Check that the login succeeded

        :param r: A request.Response object
        :return: None
        :raises LASCLoginException
        """
        if r.status_code == 200:
            return

        message = r.json["message"]
        if u"Your password is incorrect" in message:
            logger.info(u"Password was incorrect")
            raise LASCLoginException("Invalid username/password")
        if u"We can't seem to find your account" in message:
            logger.info(u"Invalid Email Address")
            raise LASCLoginException("Invalid Email Address")

    def _update_header_token(self, r):
        self.headers["X-CSRF-TOKEN"] = r.text.split("csrf")[1].split('"')[2]

    def login(self):
        """Log into the LASC Media Access Portal
        The process is tricky, requiring two GET requests, each of which
        returns HTML or JSON that is parsed for values to send in a subsequent
        POST.
        Note that if you do not have media access permissions you can not log
        into the media access portal.
        The individual requests are displayed below for reference.
        The first request
        =================
        First we capture the login page and capture and parse out of the
        TransID and Cross Site Forgery Request token
        curl -X 'GET'
            -H 'Accept: */*'
            -H 'Accept-Encoding: gzip, deflate'
            -H 'Connection: keep-alive'
            -H 'Origin: https://login.microsoftonline.com'
            -H 'User-Agent: Juriscraper'
            'https://login.microsoftonline.com/te/
            calcourts02b2c.onmicrosoft.com/b2c_1_media-lasc-susi/
            oauth2/v2.0/authorize?client_id=64f6a02f-a3d7-4871-a7b0-0883a24bd
            bda&redirect_uri=https%3A%2F%2Fmedia.lacourt.org%2Fsignin-oidc&res
            ponse_type=code%20id_token&scope=openid%20profile%20offline_acce
            ss%20https%3A%2F%2Fcalcourts02b2c.onmicrosoft.com%2Fapi%2Fread&r
            esponse_mode=form_post&nonce=636989032254084125.MWY4YWQxN2UtNDM5M
            S00ZTc5LThkN2YtMTlhYWZmZjBhZDk5YTVlNDEyMmEtMzI5ZS00YzExLTg4YTMtY
            mU2MDNhZjgzMWNj&state=CfDJ8Pwr5_ZSA25Lq9tGMhyZSHpY1A9mXEeyoedJD-
            KgsE5SoZhpEwenEHXOe0PmMbNxFslFGyGgyA4COKS_zqKlJghkVIYO02_amjN6-
            JOSfcGISf9rY9uqF2yOnwhkda3D00JcU_sOPP6uKexwG87dXvMLaxN6LuCu2GqXGk
            kAe6fOVKBlzjL8-G_EqX3j0ok8zwUaRJW8D6I4GeCfjg2LJOk4YBmGGmRYYTdCG4
            usSI1FKYLjhyCVly7aXf__QfHMvCKzVO9tjmK-Sq3REFtCLdPTiBuv1YjE6DlVj6
            _iUJ_D&x-client-SKU=ID_NET&x-client-ver=2.1.4.0'

        The second request
        ==================
        We make our first POST request to Microsoft's login API and check that
        login credentials were correct.
        curl -X 'POST'
            -H 'Accept: */*'
            -H 'Accept-Encoding: gzip, deflate'
            -H 'Connection: keep-alive'
            -H 'Content-Length: 83'
            -H 'Content-Type: application/x-www-form-urlencoded'
            -H 'Cookie: stsservicecookie=cpim_te; x-ms-gateway-slice=001-000;
             x-ms-cpim-cache:00ruicnscuqczl9ni9npwg_0=m1.wIcg9B5U2mpN0+In.SA
             ustPP2BSni6Z5+88x2tg==.0.3JkQtcZE7mGmeyqKOwSUXJJY4vWQ2TUI7poxFb
             EKknCO6oVl+g+z0Zql7fgd0C6o3hOJfqk9DxjTJvkRcSfY6piitXoAQCfsIGnPC5
             VhVMbyZPPOKyDgRnZpKhxJrutFvdpHWHQ41hBhrxpsJydFaXzdzX9iss8//X6RYf
             h0Fef6nuP8Qv+OA+THBz8xzzfDF7qJddHZftGKZ2BT/rR6/yOPgeuvuPljYEMsO
             Jfx+KVgyLYBYWSj+JDv7IvGIMfC8AAtuMVFtEE/Hb6ZBBdDbdfnWLd3DtuZkAuqF
             VeZDbk54mA6E6MQal7zhwhhoqh5Z76+DKNIWBYaehTlRfYyj7qL/mSSctNltg7vz
             DWVxEUL9z4O6bUACTCBM/Z/yFY6YJCuOBwyXAfJcRJtewDs+MjzcXE0qpe9bXfw4
             L9290GrzDTgreIAXjuvNBVLtHcb+8v0XqH8MRRnuthwi1/OVtAtoeLsIOBWAGXw
             9J15wN5qO+PotuBEFVJmbWWZGWtI2ZpMlneBIOCSYBcIKoA/+RuF2GWBzRhvBYZX
             RYchFA85AJtlmr8ql8yuvMqwkWxICXG5TBjGfJrkDduZSyChaeK9No8mssNjUDMh
             4wNkaK8bARGRtW7LRnOqOG5E4/dzpjOCNaK+2UEiwc5JfvipNQK30yF9qG0P36E
             e35eaBUaHwfaAH0MM/YaKrX8SXt3Xco2w60rlpqTfYxloabR96v8dxbQxFJETB9
             HG4cS4A5e9jJ/FJTHYk0VXFIHJn3uCgSmI4Y4eZUmV58yCfEZo8ICBXbZSCRjOQ
             ROfpCklcrI0EFkj1zk/PhHntpUAXct6BcNdu7RcmAnlqgkfusUEmij7RcXjB2TN
             ZAaqA3Pzkyk5dBOlAPXtqjKfhBHbLJLeUDdAwneMyEtZzzmKZFK2w685VwvJVw6
             NejnULArwwwXPq7G//ROYBdmLt91b8Fabq9d0UMB4S2TN8zz1ebtUWqKzrNKgf3
             bqyTm/B8mNuhjRtfKYMEkq/CZBeTbAzibyCfkjRNOjjYz1bg94Zed3T0NUT4wC
             Cckx+HrwfsEFlwd99Xh9+IaKuaE88vAFNp7EEm/aFdoRmTCyNRgJTsT8d/R/F
             7SoUag=; x-ms-cpim-trans=eyJUX0RJQyI6W3siSSI6Ijg5ZWU0YWQzLTZj
             YzMtNGE3MS05YzY2LTVmNjcyM2Q5Y2ZjMiIsIlQiOiJjYWxjb3VydHMwMmIyYy
             5vbm1pY3Jvc29mdC5jb20iLCJQIjoiYjJjXzFfbWVkaWEtbGFzYy1zdXNpIiwiQ
             yI6IjY0ZjZhMDJmLWEzZDctNDg3MS1hN2IwLTA4ODNhMjRiZGJkYSIsIlMiOjEs
             Ik0iOnt9LCJEIjowfV0sIkNfSUQiOiI4OWVlNGFkMy02Y2MzLTRhNzEtOWM2Ni0
             1ZjY3MjNkOWNmYzIifQ==; x-ms-cpim-csrf=MG9tTzRzUTNRWjlaTEVUOG1TT
             1RsN0w5dTdMdTM4RHpwUGlHcEJwTmxudkNTUXE3T3RGQzNkVEJrRHVrTzc5OEcrM
             2VSWnlUZ3hyNzJtQUJWYTVnN1E9PTsyMDE5LTA3LTE2VDE5OjQ5OjE4LjQyMjE
             xOTlaO2kzMjhnTURMQ0NuYytZTGRCdDVjRWc9PTt7Ik9yY2hlc3RyYXRpb25Td
             GVwIjoxfQ==' -H 'Origin: https://login.microsoftonline.com'
             -H 'User-Agent: Juriscraper' -H 'X-CSRF-TOKEN: MG9tTzRzUTNRWjl
             aTEVUOG1TT1RsN0w5dTdMdTM4RHpwUGlHcEJwTmxudkNTUXE3T3RGQzNkVEJrRH
             VrTzc5OEcrM2VSWnlUZ3hyNzJtQUJWYTVnN1E9PTsyMDE5LTA3LTE2VDE5OjQ5
             OjE4LjQyMjExOTlaO2kzMjhnTURMQ0NuYytZTGRCdDVjRWc9PTt7Ik9yY2hlc3
             RyYXRpb25TdGVwIjoxfQ=='
            -d 'request_type=RESPONSE&password={{PASSWORD}}&logonIdentifier=
            {{USERNAME}}'
            'https://login.microsoftonline.com/calcourts02b2c.onmicrosoft.
            com/B2C_1_Media-LASC-SUSI/SelfAsserted?p=B2C_1_Media-LASC-SUSI&
            csrf_token=MG9tTzRzUTNRWjlaTEVUOG1TT1RsN0w5dTdMdTM4RHpwUGlHcEJwT
            mxudkNTUXE3T3RGQzNkVEJrRHVrTzc5OEcrM2VSWnlUZ3hyNzJtQUJWYTVnN1E9PT
            syMDE5LTA3LTE2VDE5OjQ5OjE4LjQyMjExOTlaO2kzMjhnTURMQ0NuYytZTGRCdDV
            jRWc9PTt7Ik9yY2hlc3RyYXRpb25TdGVwIjoxfQ%3D%3D&TRANSID
            =StateProperties%3DeyJUSUQiOiI4OWVlNGFkMy02Y2MzLTRhNzEtOWM2Ni01Z
            jY3MjNkOWNmYzIifQ&tx=StateProperties%3DeyJUSUQiOiI4OWVlNGFkMy02
            Y2MzLTRhNzEtOWM2Ni01ZjY3MjNkOWNmYzIifQ'

        The third request
        =================
        The third request handles a redirect request that is required by the
        system. And we generate the parameters we need for the final request.
        curl -X 'GET'
            -H 'Accept: */*'
            -H 'Accept-Encoding: gzip, deflate'
            -H 'Connection: keep-alive'
            -H 'Cookie: stsservicecookie=cpim_te; x-ms-gateway-slice=001-000;
             x-ms-cpim-trans=eyJUX0RJQyI6W3siSSI6IjlkNDk3MjUwLTdkZjMtNGIwYS1h
             Njk3LWJlZDYwOTAzMDk5MiIsIlQiOiJjYWxjb3VydHMwMmIyYy5vbm1pY3Jvc29
             mdC5jb20iLCJQIjoiYjJjXzFfbWVkaWEtbGFzYy1zdXNpIiwiQyI6IjY0ZjZhMDJ
             mLWEzZDctNDg3MS1hN2IwLTA4ODNhMjRiZGJkYSIsIlMiOjIsIk0iOnt9LCJEIj
             owfV0sIkNfSUQiOiI5ZDQ5NzI1MC03ZGYzLTRiMGEtYTY5Ny1iZWQ2MDkwMzA5O
             TIifQ==; x-ms-cpim-cache:uhjjnfn9ckuml77wcqmjkg_0=m1.4Df4p+alIR
             6v2hGl.ITZLREieC04EqRrl9BxyeA==.0.xxHdeSM8OJh9vSWkTVzzh9fpDr2uda
             IBKcOOtgm3FpDThaLLlir9XIYMKVF4CkRX18HZKbxr3bv9Kwgm9ic/R1/g/y1nQR
             p9T9V7XNyHr/vemalGjeAgdhPpFnwfbDZm9NVPdTEkN71HYbkJV56dlq+zpG6U9Z
             4Nm4jT6NWlBmeLDoErgACZ9BUJXO5EPWEmLnyrqlMZeK0qB4cnYBvyoa9hFvkJvh
             KNsmFlrvD1KutuzuaBQShOjSGdsqbrnNCvQQWwrHaCrhXBV5oG03aLUjpKk8Tg4
             mV21C4U5h9tQxHtq5a+WB/fowLhkQ+3ZY5b3lKHds0rGHH0CRpS9juyJ9peGCi
             NdsdM6HVGDCCmg+wW/Hs6f/OOba4QBcNMVATe4cAZ1xxd8vOjXnQnkrTGuuKmO
             XEXRve6i+Y70x8T9I6S2nmGagSn3wVcc5IEZRLEksb/u76hIQjdGPdwWgg8SvM+
             Gxc68I+8uF5BGrzNbK6s7JHus9IS3p3J5zfT3fyXVrmHWkpsVMN0Pkyblt8CNH
             w0vRRx14iE17Kd9iV7c2OYS7c6lfuAaI2I75cdtYYiXghExOxUm1WgfYGf4LXX
             WSj9xNfhf35N4DvrMsK+3maegA4gAHs86oIEueGyDYFxPe8hJOyhX956C0JDjGk
             p+eqHwxB9dmkLSmeLBxhvGdDkr2o9zy/Ovs0T6TdJvAQf9AwUz6uNPa90heBbJ
             KbPptrrWFFBxx/2a/R8u+Ca0g4Udicn61evtugkwf0hWYgb3sBLZmDKoQAJJ9zt
             +qM99JWhmkCyoRc7xU9YPB+jTl4HpmUaO4PW6Vg1VbQZMR6eFvZoYQTiJbAdNkl
             8W65hjzByrZ0G6bhgBK7oClHLbRwMIlXlv+dUV0EQi23FYWnMtvoSDYWRjmdXEg
             JRAukNhfsYLyUxYhAJVIO3M//609Qydo5WMeYeXDYvGMDv2YV7nmGC0VJ/JYxJ0
             c3nZP4IagztZ+21CTyab1vChr+hDsrpzmHkLENIS8HFqT+1vAWF4GxiNrpnQo8n
             Fnsy/SGqezymixfr+FwqpgR6L0Km2l6qVytvdDL9X+x1iAqLFXtO/22+i9T8oK0
             AQneOEN7ClyKjPS3pmSDRiQOsauVFKQD81egjv0Pn19h+XxPebv4qfnn7bis5lW
             wKhFdaO8q5wNSDmzotF4Kp52+mmzZutHqSv+bPg683zQuu3THAdy3ANTNlgBFE2
             f/TIv/cne4OOrkV55HwBHOXVAi8AF5f3l/LmIgHND4CJYgIJSvfvYYYUVwXzsad
             OQNFvOUTMlC2omxuag==; x-ms-cpim-csrf=QzdLais4SU11S2l0WVBKWGRHOW
             VyMHFyU0hOcWNlNUJJTkN6MFJ3dnBLdGY1a2VnTW4vZS9jQk9hRnJrU0NHTVZtb
             EVWWXoxeEZFbFpXQ1FUaXFtZ0E9PTsyMDE5LTA3LTE2VDE5OjUxOjA3LjI4Mjc2
             OVo7cFkwekVwN0VvMVdQazdYNTc2MkYvQT09O3siT3JjaGVzdHJhdGlvblN0ZXAi
             OjF9'
            -H 'Origin: https://login.microsoftonline.com'
            -H 'User-Agent: Juriscraper'
            -H 'X-CSRF-TOKEN: QzdLais4SU11S2l0WVBKWGRHOWVyMHFyU0hOcWNlNUJJTkN
            6MFJ3dnBLdGY1a2VnTW4vZS9jQk9hRnJrU0NHTVZtbEVWWXoxeEZFbFpXQ1FUaXFt
            Z0E9PTsyMDE5LTA3LTE2VDE5OjUxOjA3LjI4Mjc2OVo7cFkwekVwN0VvMVdQazdY
            NTc2MkYvQT09O3siT3JjaGVzdHJhdGlvblN0ZXAiOjF9'
            'https://login.microsoftonline.com/calcourts02b2c.onmicrosoft.com
            /B2C_1_Media-LASC-SUSI/api/CombinedSigninAndSignup/confirmed?p
            =B2C_1_Media-LASC-SUSI&csrf_token=QzdLais4SU11S2l0WVBKWGRHOWVy
            MHFyU0hOcWNlNUJJTkN6MFJ3dnBLdGY1a2VnTW4vZS9jQk9hRnJrU0NHTVZtbEV
            WWXoxeEZFbFpXQ1FUaXFtZ0E9PTsyMDE5LTA3LTE2VDE5OjUxOjA3LjI4Mjc2OV
            o7cFkwekVwN0VvMVdQazdYNTc2MkYvQT09O3siT3JjaGVzdHJhdGlvblN0ZXAiO
            jF9&TRANSID=StateProperties%3DeyJUSUQiOiI5ZDQ5NzI1MC03ZGYzLTRiM
            GEtYTY5Ny1iZWQ2MDkwMzA5OTIifQ&tx=StateProperties%3DeyJUSUQiOiI5
            ZDQ5NzI1MC03ZGYzLTRiMGEtYTY5Ny1iZWQ2MDkwMzA5OTIifQ'

        The fourth request
        ==================
        The last request finishes the and navigates to the signin page.  We
        submit our credentials and check that we are logged in.
        curl -X 'GET'
            -H 'Accept: */*'
            -H 'Accept-Encoding: gzip, deflate'
            -H 'Connection: keep-alive'
            -H 'Cookie: .AspNetCore.Cookies=CfDJ8Pwr5_ZSA25Lq9tGMhyZSHr8UY6g7h
            wjNU0XlUHTOl3E8jJL2J9zZCP_M8hPTu9jkTnz48n7Xh04NsryQVtHsekPLasvImD
            u9vVB9Yh5Q1ZLXcLSLyUbErgz1n6r2c7A9R4DI5BRGz3IM10QxpF9p9Pv9zzWieQU
            d47LHY2jKXmjdW-ygHMVrLHKVMJuiijm0JsprghvGKm1Poqj8MSOapUeyKbIVtie
            -2q0RpwiUA-KljZu95-k08d2G33ZHo8ntgLYLY_fgOL2Mz8n038Sa5zSCtlqgxan
            WmTF5OS7-ijcuYXmdbl8Ln7_uA9181-uJjaKM_qLawemVGPhzSSKG9y0txRyol0
            UBu6xy7zp2M5QcpJ3ZDU6nVG05RGKd3OjgU5VxXvuNI2kriXiNfzAaJzxhY_vlK7
            nBccPjGJrF5UlZyfdNUQS9PbDkRmITHQHGYe2HAQBqgIQ7DLq5RzQWK5201_ADnS
            8Ge_hJk6sb1iv_n8iPjsT28jsEtO0Wlk_Sk3kxabE1NWEOXV8aPesgWw6Yicyn6c
            u4mR1Bkatm3avewOCUEct7nBDGpcosrR9spOt_vXyjmqI3KbumFtmrLxnR0SjwXB
            Nnsi1uGunjF_Lsan8aprc-CfQr7gHKUGXd3xLz3-3N66G8jbwxRnSeLOnYQ2vykV
            KFHM_QoA9TBVeJJ4XIHNW0blaIzkeI_X9InJy8-5ZCRJ_2ebKkvbcLC7hEnKVk8P
            xwyomOMW8CeF8l8MrqDgpXtwLq52L6tU2PJu4gIMSmxDymldDrBoHQDNveMX8P3i
            85OklGMIH9mRlXZJaJKdLcM3d08MUz7cpB3AjpBLp5LZPP2YLRkJXMF53eZwZDEG
            i1b1hZDmoUeKAs1ALsE2OwhPZ8YTxSsO9jlylAoZEv-52VCKI-58iq08JJNn27WbF
            uYumCwaUU3eElhy8BF4XcNdKmdiHHOfrv2Cg3hNqCadPsYejtYApoQ2EYX98e7lh
            ajwrUZTY4ymsge7aq4masSkM468Huah-W4eq7fK5gbBr1vZX0ef9uj6k9RqYJXlO
            aIN2cl0vamNZvYLHAxWhtP1gHwC0QalRCffOod00z4t3qS3V2Xj7YBBp_uWkjlbM
            32JKiAWH99pc2C81Xwp2LomaF5JQweS_qawQ7z0l_yIEGAN9DStN3cvGd0lsMZRG
            vDSWVXQ8IJk0EHkqSmNsQoKsdaaN9FuNM_vLCgdFBKPhgkJTjjsyWAdldOhJAL57
            AU5x5Ay54nh886sh-94CtuJ5Jd18_yuqKqBsiTa8NV0DbRNl2uYM1MSCs1iYUxye
            NY8HI7iyj-Q5kh4WpDQjHhckeT3SLX8PvCEyRctLzhAx__UhTRC-b6xZViCUMaUu
            Lh70ioLBy7hTESQmaciIHDczeQKbfmw70USzj5hRE9oDfjAOTRAMT2FquTuRlVep
            C3SCQ3Vjqv5j_gjUTGlYcHazbnGY4VSacOQv4az2wE96xXnRL3NoBgN_icp4F-A8
            YwLmPYJRyK64ouxc2GJPbMEUbJysmCUPYTyCRdoMDszyxc47VJFu-5Zzn-yXab_y
            5L4Cl_W-Tj105KKgATJLAhwLqQZHBFs4cDTYZ2lhzqEQdKvNyKDrEN_zi-dDvTTF
            24poPQyWRAlMTgA5I9uZrBof4EXcjad0mISA--RFEseDao5kfzfzPSNHZBgwffIX
            1bYcxGGfxZ5wGrqg1KCudXnWwSmIuHPlM_uTEGefNBg_dRcaIyif0AnP75hKKA01
            rdyK48E8UnCrkITXqBdcTy0eYXIHtRCaZNF41nfUCjgIa7MBcpMnfOsHrz-fiKL0
            5DYZmG4MBcX6434QA3srLxXY7u6gsKBj_phEaE5vKYnFt-Oal8JRjjBozrJ7haGh
            kPSM-of1jj-4dvGLirzObZ716Se2Z8naDL6TriQDj9218T3uRJvwwuXMkwgCSfIA
            YKWYcBUKKz18IJ8CaloKMPn7QnOlrtfIU0fLoyTsxpBc0T0uIIAu5RELJ6squzU
            wigR2VkaJ9mhAQ1CvXiR3PTkagP_xt42TifuxnOluf0WyJbXrPg61o4z64GqMSza
            Edpf3efI8prfQfx_krXP4gSgKHw5qanPK0ID0-aZ4A1wv2i3gp8mRapYrcmf4Y_V
            lWSJqEOzm2SSSvM1WvjNevJrQQYPwwXuLIwy8Zi6l8nhd-9PnWBD02R1hjUdTv_V
            YxoF2nRgP-qMXPeVg99eNfOzJ1wo9pW0gxQ; .AspNetCore.Session=CfDJ8Pw
            r5%2FZSA25Lq9tGMhyZSHqSUZ1fdAhQfTXbZveNz5Cd4zSPbFO%2FoUukxlHK7Li
            HmkicHk85LyDx4gO85rjEeUYnoWRnUEeZ3T9%2BWiV7COW%2BuZnAsBHtJDMj%2B
            X9hzh9STn9tXURw1isdbX4hNBVziHR7695e6oxnwHSbm1tI5ip2' -H 'Origin:
             https://login.microsoftonline.com' -H 'User-Agent: Juriscraper'
              -H 'X-CSRF-TOKEN: YlREUUpJUEJMcCtac1UweVVwRDZRM1hIdjVLK1JzL1BV
              T3d4TFpaR0ZPVkY0dENlMDN0OVBta01IU3E4Vk5iMjhWd1JxVTk1NE4rZy9WUU
              FOemdXaWc9PTsyMDE5LTA3LTE2VDE5OjUyOjM4LjA5ODYxNzhaO3c2VnJrT1V
              YYkxkRW5RUURtYmQ5anc9PTt7Ik9yY2hlc3RyYXRpb25TdGVwIjoxfQ=='
            'https://media.lacourt.org/'
        :return: None
        :raises: LASCLoginException
        """

        logger.info(u"Logging into MAP has begun")
        r = self.get(self.login_url)
        self._update_header_token(r)

        # Call part one of Microsoft login API
        r = self.post(self.api_url1, data=self.login_data)
        self._check_login(r)

        # Call part two of Microsoft login API - Redirect
        r = self.get(self.api_url2)

        # Finalize login with post into LA MAP site
        parsed_keys = self._parse_new_html_for_keys(r)

        self.post(self.signin_url, data=parsed_keys)

        logger.info(u"Successfully Logged into MAP")


class LASCLoginException(Exception):
    """
    Raised when the system cannot authenticate with LASC MAP
    """

    def __init__(self, message):
        Exception.__init__(self, message)
