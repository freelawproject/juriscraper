import os

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from juriscraper.lib.cookie_utils import normalize_cookies
from juriscraper.lib.html_utils import (
    clean_html,
    fix_links_but_keep_anchors,
    get_html_parsed_text,
)


class WebDriven:
    def __init__(self, *args, **kwargs):
        self.cookies = {}
        self.url = False
        self.uses_selenium = True
        self.wait = False  # type: WebDriverWait
        self.webdriver = False  # type: webdriver

    def __del__(self):
        self.close_webdriver_session()

    def action_chain_click(self, element: WebElement):
        """Try this when you are getting an error like:
        Element is not clickable at point (x, y) because
        another element obscures it
        """
        ActionChains(self.webdriver).move_to_element(element).click().perform()

    def close_webdriver_session(self):
        if self.webdriver:
            # sometimes quiting below throws a cryptic and otherwise ignorable OS error
            try:
                self.webdriver.quit()
            except:
                pass

    def dump_html_web_element(self, element: WebElement):
        """Use this for debugging purposes"""
        print(element.get_attribute("innerHTML"))

    def find_element(self, by: str, path: str) -> WebElement:
        if self.webdriver:
            return self.webdriver.find_element(by, path)
        raise Exception("webdriver not initiated")

    def find_element_by_class_name(self, path: str) -> WebElement:
        return self.find_element(By.CLASS_NAME, path)

    def find_element_by_id(self, path: str) -> WebElement:
        return self.find_element(By.ID, path)

    def find_element_by_xpath(self, path: str) -> WebElement:
        return self.find_element(By.XPATH, path)

    def get_page(self) -> WebElement:
        text = clean_html(self.webdriver.page_source)
        html = get_html_parsed_text(text)
        html.rewrite_links(fix_links_but_keep_anchors, base_href=self.url)
        return html

    def initiate_webdriven_session(self):
        if not self.url:
            raise Exception("self.url not set")

        options = webdriver.FirefoxOptions()
        if os.environ.get("SELENIUM_VISIBLE", False):
            options.headless = False
        else:
            options.headless = True
        options.accept_insecure_certs = True
        webdriver_conn = os.environ.get("WEBDRIVER_CONN", "local")
        if webdriver_conn == "local":
            # See README instruction for installing geckodriver
            self.webdriver = webdriver.Firefox(options=options)
        else:
            capabilities = options.to_capabilities()
            self.webdriver = webdriver.Remote(
                webdriver_conn,
                desired_capabilities=capabilities,
                keep_alive=True,
            )

        self.webdriver.implicitly_wait(30)
        self.webdriver.set_window_size(5000, 10000)
        self.wait = WebDriverWait(self.webdriver, 20)
        self.webdriver.get(self.url)
        self.cookies = normalize_cookies(self.webdriver.get_cookies())

    def scroll_to_element_then_click(self, element: WebElement):
        script = "arguments[0].click();"
        webdriver.Firefox.execute_script(script, element)

    def select_form_option(self, form_id: str) -> Select:
        element = self.find_element_by_id(form_id)
        return Select(element)

    def select_form_option_value(self, form_id: str, form_value: str):
        self.select_form_option(form_id).select_by_value(form_value)

    def select_form_option_text(self, form_id: str, form_value_text: str):
        self.select_form_option(form_id).select_by_visible_text(
            form_value_text
        )

    def wait_for_id_then_click(self, id: str):
        self.wait.until(EC.element_to_be_clickable((By.ID, id))).click()

    def wait_for_path_then_click(self, xpath: str):
        self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath))).click()

    def wait_for_id(self, id_attr):
        self.wait.until(EC.presence_of_element_located((By.ID, id_attr)))

    def take_screenshot(self, name: str = None):
        """Use this method to snap screenshots during debugging"""
        name = name if name else f"screenshot.{self.__module__}.png"
        self.webdriver.save_screenshot(name)
