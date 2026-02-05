"""
PACER HTTP utilities including session management and ACMS authentication.

The ACMS (Appellate Case Management System) authentication uses Playwright
browser automation for the complex Shibboleth/SAML flow required by
Circuit Court systems (ca2, ca9).
"""

import asyncio
import base64
import gzip
import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests
from requests.packages.urllib3 import exceptions



from juriscraper.lib.exceptions import PacerLoginException
from juriscraper.lib.html_utils import (
    get_html_parsed_text,
    get_xml_parsed_text,
    strip_bad_html_tags_insecure,
)
from juriscraper.lib.log_tools import make_default_logger

from juriscraper.pacer.utils import is_pdf, is_text

from playwright.async_api import (
    async_playwright,
    Page,
    Browser,
    BrowserContext,
    TimeoutError as PlaywrightTimeout
)
#nest_asyncio for prototype in notebook - can take away in prod
import nest_asyncio
nest_asyncio.apply()

logger = make_default_logger()

requests.packages.urllib3.disable_warnings(exceptions.InsecureRequestWarning)

# Compile the regex pattern once for efficiency.
# This pattern captures the court_id (e.g., 'ca9', 'ca2') from the URL.
ACMS_URL_PATTERN = re.compile(
    r"https?://(ca\d+)-showdoc(services)?\.azurewebsites\.us/.*"
)


# ============================================================================
# Utility Functions
# ============================================================================

def check_if_logged_in_page(content: bytes) -> bool:
    """Is this a valid HTML page from PACER?

    Check if the data in 'content' is from a valid PACER page or valid PACER
    XML document, or if it's from a page telling you to log in or informing you
    that you're not logged in.
    :param content: The data to test, of type bytes. This uses bytes to avoid
    converting data to text using an unknown encoding. (see #564)
    :return boolean: True if logged in, False if not.
    """

    valid_case_number_query = (
        b"<case number=" in content
        or b"<request number=" in content
        or b'id="caseid"' in content
        or b"Cost: " in content
    )
    no_results_case_number_query = re.search(b"<message.*Cannot find", content)
    sealed_case_query = re.search(b"<message.*Case Under Seal", content)
    if any(
        [
            valid_case_number_query,
            no_results_case_number_query,
            sealed_case_query,
        ]
    ):
        not_logged_in = re.search(b"text.*Not logged in", content)
        # An unauthenticated PossibleCaseNumberApi XML result. Simply
        # continue onwards. The complete result looks like:
        # <request number='1501084'>
        #   <message text='Not logged in.  Please refresh this page.'/>
        # </request>
        # An authenticated PossibleCaseNumberApi XML result.
        return not not_logged_in

    # Detect if we are logged in. If so, no need to do so. If not, we login
    # again below.
    found_district_logout_link = b"/cgi-bin/login.pl?logout" in content
    found_appellate_logout_link = b"InvalidUserLogin.jsp" in content

    # A download confirmation page doesn't contain a logout link but we're
    # logged into.
    is_a_download_confirmation_page = b"Download Confirmation" in content
    # When looking for a download confirmation page sometimes an appellate
    # attachment page is returned instead, see:
    # https://ecf.ca8.uscourts.gov/n/beam/servlet/TransportRoom?servlet=ShowDoc&pacer=i&dls_id=00802251695
    appellate_attachment_page = (
        b"Documents are attached to this filing" in content
    )
    # Sometimes the document is completely unavailable and an error message is
    # shown, see:
    # https://ecf.ca11.uscourts.gov/n/beam/servlet/TransportRoom?servlet=ShowDoc/009033568259
    appellate_document_error = (
        b"The requested document cannot be displayed" in content
    )
    return any(
        [
            found_district_logout_link,
            found_appellate_logout_link,
            is_a_download_confirmation_page,
            appellate_attachment_page,
            appellate_document_error,
        ]
    )

### THE JWT Code/ACMS Token classes can be taken away; they are included here because I was trying to replicate the token-based auth flow, but instead have to use cookies. Maybe JWT will be helpful for sometime in the future.
def decode_jwt_payload(token: str) -> dict:
    """Decode JWT payload without signature verification."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")

    payload = parts[1]
    # Add padding
    padding = 4 - len(payload) % 4
    if padding != 4:
        payload += "=" * padding

    decoded = base64.urlsafe_b64decode(payload)
    return json.loads(decoded)


def get_showdoc_url(court_id: str, case_number: Optional[str] = None) -> str:
    """Generate ShowDoc URL for a court."""
    base = f"https://{court_id}-showdoc.azurewebsites.us/"
    if case_number:
        return f"{base}{case_number}"
    return base


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ACMSCookies:
    """SAML session cookies from ACMS authentication."""
    cookies: list[dict]  # List of cookie dicts from Playwright
    court_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_requests_cookies(self) -> requests.cookies.RequestsCookieJar:
        """Convert to requests-compatible cookie jar."""
        jar = requests.cookies.RequestsCookieJar()
        for cookie in self.cookies:
            jar.set(
                cookie['name'],
                cookie['value'],
                domain=cookie.get('domain', ''),
                path=cookie.get('path', '/'),
                secure=cookie.get('secure', False),
            )
        return jar

    def is_expired(self) -> bool:
        """Check if any session cookies have expired."""
        now = datetime.utcnow().timestamp()
        for cookie in self.cookies:
            if '.AspNetCore.saml2' in cookie['name']:
                expires = cookie.get('expires', -1)
                if expires > 0 and expires < now:
                    return True
        return False

    def save(self, path: Path) -> None:
        """Save cookies to a JSON file."""
        data = {
            'cookies': self.cookies,
            'court_id': self.court_id,
            'created_at': self.created_at.isoformat(),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: Path) -> Optional["ACMSCookies"]:
        """Load cookies from a JSON file."""
        if not path.exists():
            return None
        try:
            with open(path) as f:
                data = json.load(f)
            return cls(
                cookies=data['cookies'],
                court_id=data['court_id'],
                created_at=datetime.fromisoformat(data['created_at']),
            )
        except (json.JSONDecodeError, KeyError):
            return None


@dataclass
class ACMSToken:
    """ACMS authentication token with metadata."""
    token: str
    cso_id: str
    login_id: str
    exempt_flag: bool
    user_ip_address: str
    issued_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    @classmethod
    def from_jwt(cls, token: str) -> "ACMSToken":
        """Create ACMSToken from a JWT string by decoding its claims."""
        claims = decode_jwt_payload(token)
        show_doc_claims = claims.get("showDocClaims", {})

        # Calculate expiry from JWT exp claim
        exp_timestamp = claims.get("exp")
        expires_at = datetime.fromtimestamp(exp_timestamp) if exp_timestamp else None

        return cls(
            token=token,
            cso_id=str(show_doc_claims.get("CSOId", "")),
            login_id=show_doc_claims.get("LoginId", ""),
            exempt_flag=show_doc_claims.get("exemptFlag", False),
            user_ip_address=show_doc_claims.get("UserIPAddress", ""),
            expires_at=expires_at
        )

    def is_expired(self, buffer_minutes: int = 5) -> bool:
        """Check if token is expired or about to expire."""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= (self.expires_at - timedelta(minutes=buffer_minutes))

    def to_juriscraper_format(self) -> tuple[dict, dict]:
        """
        Convert to format expected by PacerSession.

        Returns:
            Tuple of (acms_tokens[court_id], acms_user_data)
        """
        token_dict = {"Token": self.token}
        user_data = {
            "CsoId": self.cso_id,
            "ContactType": "PACER Only",  # Default contact type
        }
        return token_dict, user_data


@dataclass
class ACMSAuthResult:
    """Complete authentication result with both token and cookies."""
    token: ACMSToken
    cookies: ACMSCookies


# ============================================================================
# ACMS Authenticator (Async Playwright)
# ============================================================================

class ACMSAuthenticator:
    """
    Handles ACMS authentication using async Playwright browser automation.

    This class manages the complete Shibboleth/SAML authentication flow
    including session persistence and token/cookie caching.

    The authentication flow (observed via Chrome DevTools):
    1. GET /26-508 → 302 (unauthenticated)
    2. GET /Auth/Login → 302 (starts SAML)
    3. GET idp.ca9.uscourts.gov/idp/profile/SAML2/Redirect/SSO → redirects
    4. GET pacer.login.uscourts.gov/csologin/login.jsf → PACER login page
    5. POST login.jsf (AJAX with credentials)
    6. POST index.jsf (post-login, redaction agreement)
    7. GET idp/Authn/External → 302
    8. GET idp/profile/SAML2/...&_eventId_proceed=1 → SAML Response form
    9. POST /Saml2/Acs → 302 (consumes SAML)
    10. GET /26-508 → 200 (shell page)
    11. GET /Home/IndexContent → 200 (HTMX with token in window.showDocViewModel)
    """

    # Default case number to use for triggering auth (any valid case works)
    DEFAULT_CASE = "26-508"

    # Supported courts
    SUPPORTED_COURTS = ["ca2", "ca9"]

    def __init__(
        self,
        username: str,
        password: str,
        cache_dir: Optional[Path] = None,
        headless: bool = True
    ):
        """
        Initialize the authenticator.

        Args:
            username: PACER username
            password: PACER password
            cache_dir: Directory for caching browser state (optional)
            headless: Run browser in headless mode
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is required for ACMS authentication.\n"
                "Install with: pip install playwright && playwright install chromium"
            )

        self.username = username
        self.password = password
        self.headless = headless
        ### TODO: The cookies can be cached and often expire within 10 minutes. Here I am using local storage; please change for production
        self.cache_dir = cache_dir or Path.home() / ".cache" / "acms_auth"

        # Token cache: court_id -> ACMSToken
        self._tokens: dict[str, ACMSToken] = {}
        # Cookie cache: court_id -> ACMSCookies
        self._cookies: dict[str, ACMSCookies] = {}

    def _get_cookie_cache_path(self, court_id: str) -> Path:
        """Get the path for cached cookies for a court."""
        return self.cache_dir / f"{court_id}_cookies.json"

    def _get_token_cache_path(self, court_id: str) -> Path:
        """Get the path for cached token for a court."""
        return self.cache_dir / f"{court_id}_token.json"

    def _get_docket_sheet_url(self, court_id: str) -> str:
        """
        Retrieves the base docket sheet URL for a given court ID.

        :param court_id: The court identifier
        :return: The corresponding docket sheet URL.
        """
        return get_showdoc_url(court_id)

    # -------------------------------------------------------------------------
    # Sync API (wrappers around async methods)
    # -------------------------------------------------------------------------

    def authenticate(
        self,
        court_id: str,
        force_refresh: bool = False,
        timeout: int = 60000
    ) -> ACMSToken:
        """
        Authenticate to ACMS and return the token.

        This is a sync wrapper that calls the async authentication method.

        Args:
            court_id: Court identifier (ca2, ca9)
            force_refresh: Force re-authentication even if cached token exists
            timeout: Browser timeout in milliseconds

        Returns:
            ACMSToken containing the authentication token and user data
        """
        if court_id not in self.SUPPORTED_COURTS:
            raise ValueError(f"Unsupported court: {court_id}. Supported: {self.SUPPORTED_COURTS}")

        # Check memory cache first
        if not force_refresh and court_id in self._tokens:
            cached = self._tokens[court_id]
            if not cached.is_expired():
                return cached

        # Perform authentication (full result includes both token and cookies)
        result = self._authenticate_browser(court_id, timeout)
        self._tokens[court_id] = result.token
        self._cookies[court_id] = result.cookies

        # Persist cookies to disk
        result.cookies.save(self._get_cookie_cache_path(court_id))

        return result.token

    def authenticate_full(
        self,
        court_id: str,
        force_refresh: bool = False,
        timeout: int = 60000
    ) -> ACMSAuthResult:
        """
        Authenticate and return both token and cookies.

        This is useful when you need cookies for page-based requests
        in addition to the JWT token for API calls.

        Args:
            court_id: Court identifier (ca2, ca9)
            force_refresh: Force re-authentication even if cached
            timeout: Browser timeout in milliseconds

        Returns:
            ACMSAuthResult containing both ACMSToken and ACMSCookies
        """
        if court_id not in self.SUPPORTED_COURTS:
            raise ValueError(f"Unsupported court: {court_id}. Supported: {self.SUPPORTED_COURTS}")

        # Check memory cache
        if not force_refresh and court_id in self._tokens and court_id in self._cookies:
            token = self._tokens[court_id]
            cookies = self._cookies[court_id]
            if not token.is_expired() and not cookies.is_expired():
                return ACMSAuthResult(token=token, cookies=cookies)

        # Check disk cache for cookies
        if not force_refresh:
            cached_cookies = ACMSCookies.load(self._get_cookie_cache_path(court_id))
            if cached_cookies and not cached_cookies.is_expired():
                # We have valid cookies - could try to get token via cookies
                # For now, just do full auth - can optimize later
                pass

        result = self._authenticate_browser(court_id, timeout)
        self._tokens[court_id] = result.token
        self._cookies[court_id] = result.cookies

        # Persist cookies to disk
        result.cookies.save(self._get_cookie_cache_path(court_id))

        return result

    def get_cached_cookies(self, court_id: str) -> Optional[ACMSCookies]:
        """
        Get cached cookies without re-authenticating.

        Returns:
            ACMSCookies if valid cached cookies exist, None otherwise
        """
        # Check memory cache
        if court_id in self._cookies:
            cookies = self._cookies[court_id]
            if not cookies.is_expired():
                return cookies

        # Check disk cache
        cached = ACMSCookies.load(self._get_cookie_cache_path(court_id))
        if cached and not cached.is_expired():
            self._cookies[court_id] = cached
            return cached

        return None

    def get_token_for_court(self, court_id: str) -> Optional[str]:
        """Get the raw token string for a court (authenticating if needed)."""
        token = self.authenticate(court_id)
        return token.token

    def _authenticate_browser(self, court_id: str, timeout: int) -> ACMSAuthResult:
        """Perform browser-based authentication (sync wrapper for async method)."""
        logger.info(f"[ACMS] Starting browser authentication for {court_id}")
        return asyncio.get_event_loop().run_until_complete(
            self._authenticate_browser_async(court_id, timeout)
        )

    # -------------------------------------------------------------------------
    # Async API (core implementation)
    # -------------------------------------------------------------------------

    async def authenticate_async(
        self,
        court_id: str,
        force_refresh: bool = False,
        timeout: int = 60000
    ) -> ACMSToken:
        """
        Authenticate to ACMS asynchronously and return the token.

        Args:
            court_id: Court identifier (ca2, ca9)
            force_refresh: Force re-authentication even if cached token exists
            timeout: Browser timeout in milliseconds

        Returns:
            ACMSToken containing the authentication token and user data
        """
        if court_id not in self.SUPPORTED_COURTS:
            raise ValueError(f"Unsupported court: {court_id}. Supported: {self.SUPPORTED_COURTS}")

        # Check memory cache first
        if not force_refresh and court_id in self._tokens:
            cached = self._tokens[court_id]
            if not cached.is_expired():
                return cached

        # Perform authentication
        result = await self._authenticate_browser_async(court_id, timeout)
        self._tokens[court_id] = result.token
        self._cookies[court_id] = result.cookies

        # Persist cookies to disk
        result.cookies.save(self._get_cookie_cache_path(court_id))

        return result.token

    async def authenticate_full_async(
        self,
        court_id: str,
        force_refresh: bool = False,
        timeout: int = 60000
    ) -> ACMSAuthResult:
        """
        Authenticate asynchronously and return both token and cookies.

        Args:
            court_id: Court identifier (ca2, ca9)
            force_refresh: Force re-authentication even if cached
            timeout: Browser timeout in milliseconds

        Returns:
            ACMSAuthResult containing both ACMSToken and ACMSCookies
        """
        if court_id not in self.SUPPORTED_COURTS:
            raise ValueError(f"Unsupported court: {court_id}. Supported: {self.SUPPORTED_COURTS}")

        # Check memory cache
        if not force_refresh and court_id in self._tokens and court_id in self._cookies:
            token = self._tokens[court_id]
            cookies = self._cookies[court_id]
            if not token.is_expired() and not cookies.is_expired():
                return ACMSAuthResult(token=token, cookies=cookies)

        # Check disk cache for cookies
        if not force_refresh:
            cached_cookies = ACMSCookies.load(self._get_cookie_cache_path(court_id))
            if cached_cookies and not cached_cookies.is_expired():
                pass  # Could optimize here

        result = await self._authenticate_browser_async(court_id, timeout)
        self._tokens[court_id] = result.token
        self._cookies[court_id] = result.cookies

        # Persist cookies to disk
        result.cookies.save(self._get_cookie_cache_path(court_id))

        return result

    async def _authenticate_browser_async(self, court_id: str, timeout: int) -> ACMSAuthResult:
        """
        Perform browser-based authentication using async Playwright.

        Returns:
            ACMSAuthResult containing both the token and cookies
        """
        url = self._get_docket_sheet_url(court_id) + self.DEFAULT_CASE
        logger.info(f"[ACMS] Step 1: Launching Playwright browser (headless={self.headless})")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            logger.info("[ACMS] Step 2: Browser launched, creating context")
            context = await browser.new_context()
            page = await context.new_page()
            logger.info(f"[ACMS] Step 3: Navigating to {url}")

            try:
                # Navigate to trigger SAML flow
                await page.goto(url, wait_until="networkidle", timeout=timeout)
                logger.info(f"[ACMS] Step 4: Page loaded, current URL: {page.url}")

                # Wait for login page
                logger.info("[ACMS] Step 5: Waiting for login page...")
                if not await self._wait_for_login_page_async(page, timeout):
                    logger.info("[ACMS] Login page not found, checking if already authenticated...")
                    # Check if already authenticated
                    token = await self._try_extract_token_async(page)
                    if token:
                        logger.info("[ACMS] Found existing session token!")
                        cookies = await self._extract_cookies_async(context, court_id)
                        return ACMSAuthResult(token=token, cookies=cookies)
                    raise RuntimeError("Login page did not appear and no existing session found")

                logger.info("[ACMS] Step 6: Login page found, filling credentials...")
                # Fill and submit login
                await self._fill_login_form_async(page)
                logger.info("[ACMS] Step 7: Credentials filled, submitting login form...")
                await self._submit_login_async(page)

                # Handle redaction agreement if present
                logger.info("[ACMS] Step 8: Waiting for post-login processing...")
                await asyncio.sleep(2)  # Allow AJAX to process
                logger.info("[ACMS] Step 9: Checking for redaction agreement dialog...")
                handled = await self._handle_redaction_agreement_async(page)
                if handled:
                    logger.info("[ACMS] Redaction agreement accepted")
                else:
                    logger.info("[ACMS] No redaction agreement dialog found (OK)")

                # Wait for ACMS page with token
                logger.info("[ACMS] Step 10: Waiting for page to stabilize...")
                await page.wait_for_load_state("networkidle", timeout=timeout)
                logger.info(f"[ACMS] Step 11: Current URL after login: {page.url}")

                logger.info("[ACMS] Step 12: Waiting for ACMS token in page...")
                if not await self._wait_for_token_async(page, timeout):
                    self.cache_dir.mkdir(parents=True, exist_ok=True)
                    screenshot_path = str(self.cache_dir / "auth_error.png")
                    await page.screenshot(path=screenshot_path)
                    logger.error(f"[ACMS] FAILED: Token not found. Screenshot saved to {screenshot_path}")
                    raise RuntimeError(
                        "Failed to complete authentication. "
                        f"Debug screenshot saved to {self.cache_dir / 'auth_error.png'}"
                    )

                logger.info("[ACMS] Step 13: Extracting token from page...")
                token = await self._try_extract_token_async(page)
                if not token:
                    raise RuntimeError("Failed to extract token from authenticated page")

                # Extract cookies from context
                logger.info("[ACMS] Step 14: Extracting cookies from browser context...")
                cookies = await self._extract_cookies_async(context, court_id)

                logger.info(f"[ACMS] SUCCESS: Token obtained for {court_id} (expires: {token.expires_at})")
                return ACMSAuthResult(token=token, cookies=cookies)

            finally:
                logger.info("[ACMS] Closing browser...")
                await browser.close()

    async def _extract_cookies_async(self, context: BrowserContext, court_id: str) -> ACMSCookies:
        """Extract ACMS-related cookies from browser context."""
        all_cookies = await context.cookies()
        showdoc_domain = f"{court_id}-showdoc.azurewebsites.us"
        relevant_cookies = [
            c for c in all_cookies
            if showdoc_domain in c.get('domain', '')
        ]

        return ACMSCookies(
            cookies=relevant_cookies,
            court_id=court_id,
        )

    async def _wait_for_login_page_async(self, page: Page, timeout: int) -> bool:
        """Wait for PACER login page to appear."""
        try:
            await page.wait_for_selector(
                'input[name="loginForm:loginName"]',
                timeout=timeout
            )
            logger.debug("[ACMS] Login form selector found")
            return True
        except PlaywrightTimeout:
            logger.debug("[ACMS] Login form selector not found (timeout)")
            return False

    async def _fill_login_form_async(self, page: Page) -> None:
        """Fill the PACER login form."""
        await page.fill('input[name="loginForm:loginName"]', self.username)
        await page.fill('input[name="loginForm:password"]', self.password)
        logger.debug(f"[ACMS] Filled login form with username: {self.username[:3]}***")

    async def _submit_login_async(self, page: Page) -> None:
        """Submit the login form."""
        await page.click('button[name="loginForm:fbtnLogin"]')
        logger.debug("[ACMS] Login button clicked")

    async def _handle_redaction_agreement_async(self, page: Page) -> bool:
        """Handle redaction agreement dialog if present."""
        try:
            checkbox = await page.wait_for_selector(
                'div[id="regmsg:redactionConfirmation"] input[type="checkbox"]',
                timeout=5000
            )
            if checkbox:
                await checkbox.click()
                await page.click('button[id="regmsg:bpmConfirm"]')
                logger.debug("[ACMS] Redaction agreement checkbox clicked and confirmed")
                return True
        except PlaywrightTimeout:
            logger.debug("[ACMS] No redaction agreement dialog (timeout - normal)")
            pass
        return False

    async def _wait_for_token_async(self, page: Page, timeout: int) -> bool:
        """Wait for the token to be available in page context."""
        try:
            # Wait for CM/ECF logo (indicates ACMS page)
            logger.debug("[ACMS] Waiting for CM/ECF logo...")
            await page.wait_for_selector('img[alt="CM/ECF"]', timeout=timeout)
            logger.debug("[ACMS] CM/ECF logo found, waiting for authTokenResult in JS...")
            # Wait for token in JavaScript
            await page.wait_for_function(
                "window.showDocViewModel && window.showDocViewModel.authTokenResult",
                timeout=timeout
            )
            logger.debug("[ACMS] authTokenResult found in window.showDocViewModel")
            return True
        except PlaywrightTimeout:
            logger.warning("[ACMS] Timeout waiting for token in page context")
            return False

    async def _try_extract_token_async(self, page: Page) -> Optional[ACMSToken]:
        """Extract token from page if available."""
        try:
            result = await page.evaluate("""
                () => {
                    if (window.showDocViewModel && window.showDocViewModel.authTokenResult) {
                        return { token: window.showDocViewModel.authTokenResult.token };
                    }
                    return null;
                }
            """)

            if result and result.get("token"):
                token = ACMSToken.from_jwt(result["token"])
                logger.debug(f"[ACMS] Token extracted: CSO ID={token.cso_id}, Login={token.login_id}")
                return token
            logger.debug("[ACMS] No token found in page evaluate result")
        except Exception as e:
            logger.warning(f"[ACMS] Error extracting token: {e}")
            pass
        return None


# ============================================================================
# PacerSession
# ============================================================================

class PacerSession(requests.Session):
    """
    Extension of requests.Session to handle PACER oddities making it easier
    for folks to just POST data to PACER endpoints/apis.

    Also includes utilities for logging into PACER and re-logging in when
    sessions expire.
    """

    LOGIN_URL = "https://pacer.login.uscourts.gov/services/cso-auth"

    def __init__(
        self,
        cookies=None,
        username=None,
        password=None,
        client_code=None,
        get_acms_tokens=False,
        acms_cookies=None,
        auto_load_acms_cache=True,
    ):
        """
        Instantiate a new PACER API Session with some Juriscraper defaults
        :param cookies: an optional RequestsCookieJar object with cookies for the session
        :param username: a PACER account username
        :param password: a PACER account password
        :param client_code: an optional PACER client code for the session
        :param get_acms_tokens: boolean flag to enable ACMS authentication during login.
        :param acms_cookies: dict mapping court_id to cookie list for ACMS ShowDoc pages.
            Format: {"ca9": [{"name": "...", "value": "...", ...}, ...]}
            These are the .AspNetCore.saml2* cookies from SAML authentication.
        :param auto_load_acms_cache: If True, automatically load cached ACMS cookies
            from disk on initialization (default: True).
        """
        super().__init__()
        self.headers["User-Agent"] = "Juriscraper"
        self.headers["Referer"] = "https://external"  # For CVE-001-FLP.
        self.verify = False

        if cookies:
            assert not isinstance(cookies, str), (
                "Got str for cookie parameter. Did you mean "
                "to use the `username` and `password` kwargs?"
            )
            self.cookies = cookies

        self.username = username
        self.password = password
        self.client_code = client_code
        self.additional_request_done = False
        self.get_acms_tokens = get_acms_tokens
        self.acms_user_data = {}
        self.acms_tokens = {}
        self.acms_cookies = acms_cookies or {}

        # Auto-load cached ACMS cookies from disk
        if auto_load_acms_cache and username and password:
            self._load_cached_acms_auth()

    def _load_cached_acms_auth(self) -> None:
        """
        Load cached ACMS cookies and tokens from disk for all supported courts.

        This is called automatically on session init if auto_load_acms_cache=True.
        Cookies are validated and only loaded if not expired.
        """
        cache_dir = Path.home() / ".cache" / "acms_auth"
        supported_courts = ["ca2", "ca9"]

        for court_id in supported_courts:
            cookie_path = cache_dir / f"{court_id}_cookies.json"
            cached_cookies = ACMSCookies.load(cookie_path)

            if cached_cookies and not cached_cookies.is_expired():
                logger.info(f"[ACMS] Loaded cached cookies for {court_id} from disk")
                self.acms_cookies[court_id] = cached_cookies.cookies

                # Try to get a fresh token using cached cookies
                token = self._refresh_token_with_cookies(court_id, cached_cookies)
                if token:
                    token_dict, user_data = token.to_juriscraper_format()
                    self.acms_tokens[court_id] = token_dict
                    if not self.acms_user_data:
                        self.acms_user_data = user_data
                    logger.info(
                        f"[ACMS] Refreshed token for {court_id} using cached cookies "
                        f"(expires: {token.expires_at})"
                    )
            else:
                if cached_cookies:
                    logger.debug(f"[ACMS] Cached cookies for {court_id} are expired")
                else:
                    logger.debug(f"[ACMS] No cached cookies found for {court_id}")

    def _check_url_and_retrieve_acms_token(self, url: str) -> str:
        """
        Checks if the provided URL is an ACMS URL and, if so, ensures the
        ACMS bearer token is available for that court ID.

        If the ACMS bearer token for the detected court ID is not already
        in the session's `acms_tokens`, this method will trigger the
        `get_acms_auth_object()` method to perform authentication and
        retrieve the token.

        :param url: The URL of the request to check.
        :return: The ACMS bearer token if the URL is an ACMS URL and a token
                 is available. Returns an empty string otherwise
        """
        # Check if the URL matches the ACMS pattern
        match = ACMS_URL_PATTERN.match(url)
        if not match:
            return ""

        acms_court_id = match.group(1)
        logger.debug(f"Detected ACMS request for court: {acms_court_id}")

        if acms_court_id not in self.acms_tokens:
            self.get_acms_auth_object(acms_court_id)

        return self.acms_tokens[acms_court_id]["Token"]

    def set_acms_cookies(self, court_id: str, cookies: list[dict]) -> None:
        """
        Set ACMS cookies for a court from a list of cookie dicts.

        :param court_id: Court identifier (e.g., "ca9")
        :param cookies: List of cookie dicts from Playwright browser context.
            Each dict should have at least 'name' and 'value' keys.
        """
        self.acms_cookies[court_id] = cookies

    def get_acms_cookies_jar(self, court_id: str) -> Optional[requests.cookies.RequestsCookieJar]:
        """
        Get ACMS cookies for a court as a RequestsCookieJar.

        :param court_id: Court identifier (e.g., "ca9")
        :return: RequestsCookieJar with the court's ACMS cookies, or None if not set.
        """
        if court_id not in self.acms_cookies:
            return None

        jar = requests.cookies.RequestsCookieJar()
        for cookie in self.acms_cookies[court_id]:
            jar.set(
                cookie['name'],
                cookie['value'],
                domain=cookie.get('domain', ''),
                path=cookie.get('path', '/'),
                secure=cookie.get('secure', False),
            )
        return jar

    def get(self, url, auto_login=True, **kwargs):
        """Overrides request.Session.get with session retry logic.

        :param url: url string to GET
        :param auto_login: Whether the auto-login procedure should happen.
        :return: requests.Response
        """
        # Check if the URL matches the ACMS pattern
        acms_token = self._check_url_and_retrieve_acms_token(url)
        # If it's an ACMS request, add the bearer token to the headers
        if acms_token:
            # JWT Token doesnt work for the
            kwargs.setdefault("headers", {})
            kwargs["headers"].update({"Authorization": f"Bearer {acms_token}"})
        court_id = url[url.rfind("/") + 3 :]
        cookies_jar = self.get_acms_cookies_jar(court_id)
        if cookies_jar:
            # Merge ACMS cookies with any existing cookies in kwargs
            if "cookies" in kwargs:
                kwargs["cookies"].update(cookies_jar)
            else:
                kwargs["cookies"] = cookies_jar

        if "timeout" not in kwargs:
            kwargs.setdefault("timeout", 300)

        r = super().get(url, **kwargs)

        if b"This user has no access privileges defined." in r.content:
            # This is a strange error that we began seeing in CM/ECF 6.3.1 at
            # ILND. You can currently reproduce it by logging in on the central
            # login page, selecting "Court Links" as your destination, and then
            # loading: https://ecf.ilnd.uscourts.gov/cgi-bin/WrtOpRpt.pl
            # The solution when this error shows up is to simply re-run the get
            # request, so that's what we do here. PACER needs some frustrating
            # and inelegant hacks sometimes.
            r = super().get(url, **kwargs)
        if auto_login and not acms_token:
            updated = self._login_again(r)
            if updated:
                # Re-do the request with the new session.
                r = super().get(url, **kwargs)
                # Do an additional check of the content returned.
                self._login_again(r)
        return r

    def post(self, url, data=None, json=None, auto_login=True, **kwargs):
        """
        Overrides requests.Session.post with PACER-specific fun.

        Will automatically convert data dict into proper multi-part form data
        and pass to the files parameter instead.

        Will set a timeout of 300 if not provided.

        All other uses or parameters will pass through untouched
        :param url: url string to post to
        :param data: post data
        :param json: json object to post
        :param auto_login: Whether the auto-login procedure should happen.
        :param kwargs: assorted keyword arguments
        :return: requests.Response
        """
        # Check if the URL matches the ACMS pattern
        acms_token = self._check_url_and_retrieve_acms_token(url)
        # If it's an ACMS request, add the bearer token to the headers
        if acms_token:
            # Ensure 'headers' key exists in kwargs as a dictionary.
            # If it doesn't exist, it's created as an empty dict.
            kwargs.setdefault("headers", {})
            kwargs["headers"].update({"Authorization": f"Bearer {acms_token}"})

        # Check if this is an ACMS ShowDoc page request (not API)
        match = ACMS_URL_PATTERN.match(url)
        if match:
            court_id = match.group(1)
            is_api_request = match.group(2) is not None  # "services" captured
            # For page requests, use cookies instead of/in addition to token
            if not is_api_request and court_id in self.acms_cookies:
                cookies_jar = self.get_acms_cookies_jar(court_id)
                if cookies_jar:
                    if "cookies" in kwargs:
                        kwargs["cookies"].update(cookies_jar)
                    else:
                        kwargs["cookies"] = cookies_jar

        kwargs.setdefault("timeout", 300)

        if data:
            pacer_data = self._prepare_multipart_form_data(data)
            kwargs.update({"files": pacer_data})
        else:
            kwargs.update({"data": data, "json": json})

        r = super().post(url, **kwargs)
        if auto_login and not acms_token:
            updated = self._login_again(r)
            if updated:
                # Re-do the request with the new session.
                return super().post(url, **kwargs)
        return r

    def head(self, url, **kwargs):
        """
        Overrides request.Session.head with a default timeout parameter.

        :param url: url string upon which to do a HEAD request
        :param kwargs: assorted keyword arguments
        :return: requests.Response
        """
        kwargs.setdefault("timeout", 300)
        return super().head(url, **kwargs)

    @staticmethod
    def _prepare_multipart_form_data(data):
        """
        Transforms a data dictionary into the multi-part form data that PACER
        expects as the POST body
        :param data: dict of data to transform
        :return: dict with values wrapped into tuples like:(None, <value>)
        """
        output = {}
        for key in data:
            output[key] = (None, data[key])
        return output

    @staticmethod
    def _get_view_state(r):
        """Get the viewState parameter of the form

        This is an annoying thing we have to do. The login flow has three
        requests that you make and each requires the view state from the one
        prior. Thus, we capture that viewState each time and submit it during
        each of the next submissions.

        The HTML takes the form of:

        <input type="hidden" name="javax.faces.ViewState"
               id="j_id1:javax.faces.ViewState:0"
               value="some-long-value-here">

        :param r: A request.Response object
        :return The value of the "value" attribute of the ViewState input
        element.
        """
        tree = get_html_parsed_text(r.content)
        xpath = (
            '//form[@id="loginForm"]//input['
            '    @name="javax.faces.ViewState"'
            "]/@value"
        )
        return tree.xpath(xpath)[0]

    @staticmethod
    def _get_xml_view_state(r):
        """Same idea as above, but sometimes PACER returns XML so we parse
        that instead of the HTML.

        Here's a sample of the XML:

        <partial-response id="j_id1">
          <changes>
            <update id="regmsg:bpmConfirm">
              <![CDATA[<button id="regmsg:bpmConfirm" name="regmsg:bpmConfirm" class="ui-button ui-widget ui-state-default ui-corner-all ui-button-text-only" onclick="PrimeFaces.ab({s:&quot;regmsg:bpmConfirm&quot;,pa:[{name:&quot;dialogName&quot;,value:&quot;redactionDlg&quot;}]});return false;" style="margin-right: 20px;" type="submit"><span class="ui-button-text ui-c">Continue</span></button><script id="regmsg:bpmConfirm_s" type="text/javascript">PrimeFaces.cw("CommandButton","widget_regmsg_bpmConfirm",{id:"regmsg:bpmConfirm"});</script>]]>
            </update>
            <update id="loginForm:pclLoginMessages">
              <![CDATA[<div id="loginForm:pclLoginMessages" class="ui-messages ui-widget" style="font-size: 0.85em;" aria-live="polite"></div>]]>
            </update>
            <update id="j_id1:javax.faces.ViewState:0"><![CDATA]]>
            </update>
          </changes>
        </partial-response>
        """
        tree = get_xml_parsed_text(r.content)
        xpath = "//update[@id='j_id1:javax.faces.ViewState:0']/text()"
        return tree.xpath(xpath)[0]

    def _prepare_login_request(self, url, data, headers, *args, **kwargs):
        """Prepares and sends a POST request for login purposes.

        This internal helper function constructs a POST request to the provided URL
        using the given headers and data. It sets a timeout of 60 seconds for the
        request.

        :param url: The URL of the login endpoint.
        :param data: A dictionary containing login credentials.
        :param headers: Additional headers to include in the request.
        :param *args: Additional arguments to be passed to the underlying POST
               request.
        :param **kwargs: Additional keyword arguments to be passed to the
               underlying POST request.
        :return: requests.Response: The response object from the login request.
        """
        return super().post(
            url,
            headers=headers,
            timeout=60,
            data=data,
        )

    def login(self, url=None):
        """Attempt to log into the PACER site.
        The first step is to get an authentication token using a PACER
        username and password.
        To get the authentication token, it's necessary to send a POST request:
        curl --location --request POST 'https://pacer.login.uscourts.gov/services/cso-auth' \
            --header 'Accept: application/json' \
            --header 'User-Agent: Juriscraper' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "loginId": "USERNAME",
                "password": "PASSWORD"
            }'

        All documentation for PACER Authentication API User Guide can be found here:
        https://pacer.uscourts.gov/help/pacer/pacer-authentication-api-user-guide
        """
        logger.info("Attempting PACER API login")
        # Clear any remaining cookies. This is important because sometimes we
        # want to login before an old session has entirely died.
        self.cookies.clear()
        if url is None:
            url = self.LOGIN_URL
        # By default, it's assumed that the user is a filer. Redaction flag is set to 1
        data = {
            "loginId": self.username,
            "password": self.password,
            "redactFlag": "1",
        }
        # If optional client code information is included, include in login request
        if self.client_code:
            data["clientCode"] = self.client_code

        headers = {
            "User-Agent": "Juriscraper",
            "Content-type": "application/json",
            "Accept": "application/json",
        }
        login_post_r = self._prepare_login_request(
            url, data=json.dumps(data), headers=headers
        )

        if login_post_r.status_code != requests.codes.ok:
            message = f"Unable connect to PACER site: '{login_post_r.status_code}: {login_post_r.reason}'"
            logger.warning(message)
            raise PacerLoginException(message)

        # Continue with login when response code is "200: OK"
        response_json = login_post_r.json()

        # 'loginResult': '0', user successfully logged; '1', user not logged
        if (
            response_json.get("loginResult") is None
            or response_json.get("loginResult") == "1"
        ):
            message = f"Invalid username/password: {response_json.get('errorDescription')}"
            raise PacerLoginException(message)
        # User logged, but with pending actions for their account
        if response_json.get("loginResult") == "0" and response_json.get(
            "errorDescription"
        ):
            logger.info(response_json.get("errorDescription"))

        if not response_json.get("nextGenCSO"):
            raise PacerLoginException(
                "Did not get NextGenCSO cookie when attempting PACER login."
            )
        # Set up cookie with 'nextGenCSO' token (128-byte string of characters)
        session_cookies = requests.cookies.RequestsCookieJar()
        session_cookies.set(
            "NextGenCSO",
            response_json.get("nextGenCSO"),
            domain=".uscourts.gov",
            path="/",
        )
        # Support "CurrentGen" servers as well. This can be remoevd if they're
        # ever all upgraded to NextGen.
        session_cookies.set(
            "PacerSession",
            response_json.get("nextGenCSO"),
            domain=".uscourts.gov",
            path="/",
        )
        # If optional client code information is included,
        # 'PacerClientCode' cookie should be set
        if self.client_code:
            session_cookies.set(
                "PacerClientCode",
                self.client_code,
                domain=".uscourts.gov",
                path="/",
            )
        self.cookies = session_cookies
        logger.info("New PACER session established.")

        if self.get_acms_tokens:
            for court_id in ["ca2", "ca9"]:
                self.get_acms_auth_object(court_id)

    def _do_additional_request(self, r: requests.Response) -> bool:
        """Check if we should do an additional request to PACER, sometimes
        PACER returns the login page even though cookies are still valid.
        Do an additional GET request if we haven't done it previously.
        See https://github.com/freelawproject/courtlistener/issues/2160.

        :param r: The requests Response object.
        :return: True if an additional request should be done, otherwise False.
        """
        if r.request.method == "GET" and self.additional_request_done is False:
            self.additional_request_done = True
            return True
        return False

    def _login_again(self, r):
        """Log into PACER if the session has credentials and the session has
        expired.

        :param r: A response object to inspect for login errors.
        :returns: A boolean indicating whether a new session needed to be
        created.
        :raises: PacerLoginException, if unable to create a new session.
        """
        if is_pdf(r):
            return False

        if is_text(r):
            return False

        logged_in = check_if_logged_in_page(r.content)
        if logged_in:
            return False

        if self.username and self.password:
            logger.info(
                "Invalid/expired PACER session. Establishing new session."
            )
            self.login()
            return True
        else:
            if self._do_additional_request(r):
                return True
            raise PacerLoginException(
                "Invalid/expired PACER session and do not have credentials "
                "for re-login."
            )

    def _get_saml_auth_request_parameters(
        self, court_id: str
    ) -> dict[str, str]:
        """
        Retrieves SAML authentication request parameters by initiating a request
        to the DOCKET_SHEET_URL. This simulates the initial browser interaction
        that triggers the SAML flow, parsing hidden input fields from the
        response.

        :param court_id: The court identifier.
        :return: A dictionary where keys are the 'name' attributes and values are
            the 'value' attributes of hidden input elements found in the SAML
            authentication request form.
        """
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
        }
        logger.info(f"Attempting to get SAML credentials for {court_id}")
        # Base URL for retrieving SAML credentials.
        url = get_showdoc_url(court_id)
        response = self._prepare_login_request(url, data={}, headers=headers)
        result_parts = response.text.split("\r\n")
        # Handle gzip decoding
        js_screen = result_parts[-1]
        try:
            # Try to decompress if it's gzipped
            inflated_screen = gzip.decompress(js_screen.encode()).decode()
        except Exception:
            # If decompression fails, use the original
            inflated_screen = js_screen

        # Strip potentially problematic HTML tags for safer parsing.
        html = strip_bad_html_tags_insecure(inflated_screen)
        # Extract all hidden input elements from the HTML.
        hidden_inputs = html.xpath('//input[@type="hidden"]')

        # Return a dictionary of hidden input names and their values.
        return {
            input_element.get("name"): input_element.get("value")
            for input_element in hidden_inputs
        }

    def get_acms_auth_object(
        self, court_id: str, force_refresh: bool = False
    ) -> ACMSAuthResult:
        """
        Retrieves the ACMS authentication object, using cached cookies when available.

        This method first checks for valid cached cookies on disk. If found and not
        expired, it uses them to obtain a fresh token without launching a browser.
        Only falls back to full Playwright authentication when necessary.

        The result is stored in:
        - self.acms_tokens[court_id]: {"Token": <jwt_token>} for API Bearer auth
        - self.acms_cookies[court_id]: list of cookie dicts for page requests
        - self.acms_user_data: user info from the token

        :param court_id: The court identifier (e.g., "ca2", "ca9").
        :param force_refresh: If True, skip cache and do full browser auth.
        :return: ACMSAuthResult containing both the token and cookies.
        """
        if not self.username or not self.password:
            raise ValueError("PacerSession must have username and password set for ACMS auth")

        auth = ACMSAuthenticator(
            self.username,
            self.password,
            headless=True
        )

        # Try to use cached cookies first (avoids browser launch)
        if not force_refresh:
            cached_cookies = auth.get_cached_cookies(court_id)
            if cached_cookies and not cached_cookies.is_expired():
                logger.info(f"[ACMS] Found valid cached cookies for {court_id}, attempting token refresh...")

                # Try to get a fresh token using cached cookies
                token = self._refresh_token_with_cookies(court_id, cached_cookies)
                if token:
                    token_dict, user_data = token.to_juriscraper_format()
                    self.acms_tokens[court_id] = token_dict
                    if not self.acms_user_data:
                        self.acms_user_data = user_data
                    self.acms_cookies[court_id] = cached_cookies.cookies

                    logger.info(
                        f"[ACMS] Successfully refreshed token for {court_id} using cached cookies "
                        f"(expires: {token.expires_at})"
                    )
                    return ACMSAuthResult(token=token, cookies=cached_cookies)
                else:
                    logger.info("[ACMS] Cached cookies invalid, falling back to browser auth...")

        # Full browser authentication
        result = auth.authenticate_full(court_id, force_refresh=force_refresh)
        token_dict, user_data = result.token.to_juriscraper_format()

        # Set JWT token for API calls
        self.acms_tokens[court_id] = token_dict

        # Set user data (only if not already set to preserve any existing data)
        if not self.acms_user_data:
            self.acms_user_data = user_data

        # Set cookies for page requests
        self.acms_cookies[court_id] = result.cookies.cookies

        logger.info(
            f"[ACMS] Successfully obtained auth for {court_id}: "
            f"token expires {result.token.expires_at}, "
            f"cookies count: {len(result.cookies.cookies)}"
        )

        return result

    def _refresh_token_with_cookies(
        self, court_id: str, cookies: ACMSCookies
    ) -> Optional[ACMSToken]:
        """
        Attempt to get a fresh token using cached SAML cookies.

        This makes an HTTP request to the ShowDoc page which returns a fresh
        JWT token if the cookies are still valid.

        :param court_id: The court identifier.
        :param cookies: Cached ACMSCookies object.
        :return: ACMSToken if successful, None if cookies are invalid/expired.
        """
        import re

        url = f"https://{court_id}-showdoc.azurewebsites.us/Home/IndexContent"
        params = {"caseIdentifier": "26-508"}  # Any valid case works
        headers = {
            "Accept": "text/html",
            "HX-Request": "true",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                cookies=cookies.to_requests_cookies(),
                timeout=30
            )

            # Check if redirected to login (cookies expired)
            if 'login.jsf' in response.url or 'loginForm' in response.text:
                return None

            # Extract token from JavaScript
            match = re.search(
                r'window\.showDocViewModel\s*=\s*(\{.*?\});',
                response.text,
                re.DOTALL
            )
            if match:
                view_model = json.loads(match.group(1))
                auth_result = view_model.get("authTokenResult", {})
                token_str = auth_result.get("token")
                if token_str:
                    return ACMSToken.from_jwt(token_str)

            return None

        except Exception as e:
            logger.warning(f"[ACMS] Error refreshing token with cookies: {e}")
            return None

