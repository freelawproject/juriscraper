"""
Scraper for New York Court of Appeals
CourtID: ny
Court Short Name: NY
History:
 2014-07-04: Created by Andrei Chelaru, reviewed by mlr.
 2015-10-23: Parts rewritten by mlr.
 2016-05-04: Updated by arderyp to handle typos in docket string format
 2024-09-05: Updated by flooie to deal with block from main website
"""
import os
import re
import shutil
from datetime import date, timedelta, datetime
from io import FileIO
from time import sleep
from typing import Any, Dict, Optional, Tuple

import pdfkit
import requests
from bs4 import BeautifulSoup
from lxml.html import tostring
from tldextract.tldextract import update
from typing_extensions import override
from weasyprint.css.validation.properties import continue_

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import set_response_encoding, \
    fix_links_in_lxml_tree
from juriscraper.lib.judge_parsers import normalize_judge_string
from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time


class Site(OpinionSiteLinear):
    first_opinion_date = date(2003, 9, 25)
    days_interval = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court = "Court of Appeals"
        self.court_id = self.__module__
        self.url = "https://iapps.courts.state.ny.us/lawReporting/Search?searchType=all"
        # self._set_parameters()
        self.expected_content_types = ["application/pdf", "text/html"]
        self.make_backscrape_iterable(kwargs)  # set_api_token_header(self)

    def _set_parameters(self, start_date: Optional[date] = None,
        end_date: Optional[date] = None, ) -> None:
        """Set the parameters for the POST request.

        If no start or end dates are given, scrape last month.
        This is the default behaviour for the present time scraper

        :param start_date:
        :param end_date:
        :return: None
        """
        self.method = "POST"
        if not end_date:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)

        self.parameters = {"rbOpinionMotion": "opinion", "Pty": "",
            "and_or": "and", "dtStartDate": start_date.strftime("%m/%d/%Y"),
            "dtEndDate": end_date.strftime("%m/%d/%Y"), "court": self.court,
            "docket": "", "judge": "", "slipYear": "", "slipNo": "",
            "OffVol": "", "Rptr": "", "OffPage": "", "fullText": "",
            "and_or2": "and", "Order_By": "Party Name", "Submit": "Find",
            "hidden1": "", "hidden2": "", }

    def _process_html(self):
        i=0
        for row in self.html.xpath(".//table")[-1].xpath(".//tr")[1:]:
            slip_cite = " ".join(row.xpath("./td[5]//text()")).strip()
            official_citation = " ".join(row.xpath("./td[4]//text()")).strip()
            if slip_cite.__eq__('Slip Number') and official_citation.__eq__('Official Citation'):
                continue
            url = row.xpath(".//a")[0].get("href")
            if str(url).__contains__(".pdf"):
                url = re.findall(r"(http.*pdf)", url)[0]
            elif str(url).__contains__(".htm"):
                url = re.findall(r"(http.*htm)", url)[0]
            else:
                url = re.findall(r"(http.*htm)", url)[0]

            status = "Unpublished" if "(U)" in slip_cite else "Published"
            case = {"name": row.xpath(".//td")[0].text_content(),
                "date": row.xpath(".//td")[1].text_content(), "url": url,
                "status": status, "docket": [],
                "citation": [official_citation],
                "parallel_citation": [slip_cite],
                "judge": [],
                "per_curiam": False, }
            judge = row.xpath("./td")[-2].text_content()

            # Because P E R C U R I A M, PER CURIAM, and Per Curiam
            pc = re.sub(r"\s", "", judge.lower())
            if "percuriam" in pc:
                case["per_curiam"] = True
            elif judge:
                cleaned_author = normalize_judge_string(judge)[0]
                if cleaned_author.endswith(" J."):
                    cleaned_author = cleaned_author[:-3]
                case["judge"] = [cleaned_author]
            if(self.cases.__contains__(case)):
                return
            else:
                self.cases.append(case)
            i=i+1

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Can we extract the docket number from the text?

        :param scraped_text: The content of the document downloaded
        :return: Metadata to be added to the case
        """
        dockets = re.search(
            r"^<br>(?P<docket_number>No\. \d+(\s+SSM \d+)?)\s?$",
            scraped_text[:2000], re.MULTILINE, )
        if dockets:
            return {"Docket": dockets.groupdict()}
        return {}

    def _download_backwards(self, dates: Tuple[date]):
        """Make custom date range request

        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        # self._set_parameters(*dates)
        request_dict={
            'start_date':dates[0],
            'end_date':dates[1],
            'court':self.court
        }
        self.html = self._download(request_dict=request_dict)
        self._process_html()
        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            # This needs to be done *after* _clean_attributes() has been run.
            # The current architecture means this gets run twice. Once when we
            # iterate over _all_attrs, and again here. It's pretty cheap though.
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return self

    def _download(self, request_dict={}):
        """Download the latest version of Site"""
        global driver
        self.downloader_executed = True

        try:
            driver=self.set_selenium_driver()
            driver.get(
                "https://iapps.courts.state.ny.us/lawReporting/Search?searchType=all")  # Replace with your form page URL
            # Fill out the form fields
            driver.find_element(By.NAME, "rbOpinionMotion").send_keys("opinion")
            driver.find_element(By.NAME, "and_or").send_keys("and")
            driver.find_element(By.NAME, "dtStartDate").send_keys(request_dict['start_date'].strftime("%m/%d/%Y"))
            driver.find_element(By.NAME, "dtEndDate").send_keys(request_dict['end_date'].strftime("%m/%d/%Y"))
            driver.find_element(By.NAME, "court").send_keys(request_dict['court'])
            driver.find_element(By.NAME, "and_or2").send_keys("and")
            driver.find_element(By.NAME, "Order_By").send_keys("Party Name")
            driver.find_element(By.NAME, "Submit").send_keys("Find")
            # Submit the form
            driver.find_element(By.XPATH,"//form").submit()  # Adjust the selector if necessary

            # Wait for the response page to load
            time.sleep(3)  # Adjust as necessary
            # Print the page HTML after the POST request
            resp_html = driver.page_source
            soup = BeautifulSoup(resp_html, 'html.parser')
            body=soup.find('body')
            body_text=body.text
            if body_text.__contains__('The search returns more than 500 results.'):
                driver.quit()
                start_date = request_dict['start_date']
                end_date = request_dict['end_date']
                total_days = (end_date - start_date).days
                divided_days=8
                segment_length = total_days // divided_days

                custom_html = "<html><head><title>LRB Search Results</title><script language='javascript'>function funcNewWindow(url) {var x;x = window.open(url, 'newwin', 'height=600, width=800, left=25, top=25, resizable, scrollbars=yes, status=1');}</script></head><script type='text/javascript' src='/lawReporting/javascript/validRequest.js'></script><body topmargin=0 leftmargin=0><form name=form><table border=0 width='100%' cellspacing=0 cellpadding=0 align=center><tr><td align=center><br><table border=0 align=center><tr><td align=right>&nbsp;</td><td><font color='#000099' face=arial size=5>Slip Decisions Search Results</font></td></tr><tr><td colspan=2><table border=0><tr><td valign=top><table border=0 cellspacing=1 cellpadding=1><tr bgcolor=#e6e6e6><td><font face=arial size=2><b>Search Criteria</b></font></td></tr><tr><td><font face=arial size=2> &nbsp; &nbsp; Decision Start Date :</font><font face=arial size=2 color=#000099><b>01/01/2024</b></font></td></tr><tr><td><font face=arial size=2> &nbsp; &nbsp; Decision End Date :</font><font face=arial size=2 color=#000099><b>02/01/2024</b></font></td></tr><tr><td><font face=arial size=2> &nbsp; &nbsp; Court :</font><font face=arial size=2 color=#000099><b>App Div, 1st Dept</b></font></td></tr></table></td></tr></table><br><table border=0 width='100%' cellspacing=1 cellpadding=1><tr><td><font face=arial size=2><b>Total number of records found: 229</b>&nbsp; &nbsp;&nbsp; &nbsp;</font></td></tr><tr><td colspan=4 align=center><input type=button name=again value='Search Again'onclick='history.back()'> <input type=button name=cancelvalue='Home Page'onclick=location.href='http://www.nycourts.gov/reporter/'><br><br></td></tr><tr><td><table></table></td></tr></table></td></tr></table></td></tr></table></form></body></html>"
                custom_parser = BeautifulSoup(custom_html,'html.parser')
                custom_form=custom_parser.find("form")
                custom_table=custom_form.find_all('table')[5]
                custom_trs=custom_table.find_all("tr")
                date_ranges = []
                for i in range(divided_days):
                    segment_start = start_date + timedelta(
                        days=i * segment_length)
                    segment_end = segment_start + timedelta(
                        days=segment_length - 1)
                    if i == divided_days - 1:  # Adjust the last segment to include the end date
                        segment_end = end_date
                    date_ranges.append((segment_start.strftime('%d/%m/%Y'),
                                        segment_end.strftime('%d/%m/%Y')))

                # Output the date ranges
                for idx, (start, end) in enumerate(date_ranges, 1):
                    # new_driver= self.set_selenium_driver()
                    start2 = datetime.strptime(start, '%d/%m/%Y').strftime('%m/%d/%Y')
                    end2 = datetime.strptime(end, '%d/%m/%Y').strftime('%m/%d/%Y')
                    print(f"Date Range {idx}: {start2} to {end2}")

                    flag = True
                    while flag:
                        driver = self.set_selenium_driver()
                        driver.get("https://iapps.courts.state.ny.us/lawReporting/Search?searchType=all")
                        if driver.page_source.__contains__('<title>Just a moment...</title>'):
                            driver.quit()
                            time.sleep(3)
                        else:
                            flag = False

                    driver.find_element(By.NAME, "rbOpinionMotion").send_keys("opinion")
                    driver.find_element(By.NAME, "and_or").send_keys("and")
                    driver.find_element(By.NAME, "dtStartDate").send_keys(start2)
                    driver.find_element(By.NAME, "dtEndDate").send_keys(end2)
                    driver.find_element(By.NAME, "court").send_keys(request_dict['court'])
                    driver.find_element(By.NAME, "and_or2").send_keys("and")
                    driver.find_element(By.NAME, "Order_By").send_keys("Party Name")
                    driver.find_element(By.NAME, "Submit").send_keys("Find")
                    # Submit the form
                    driver.find_element(By.XPATH,"//form").submit()  # Adjust the selector if necessary
                    # print(f"Date Range {idx}: {start} to {end}")
                    time.sleep(3)  # Adjust as necessary
                    # Print the page HTML after the POST request
                    resp_html = driver.page_source
                    resp_soup = BeautifulSoup(resp_html,'html.parser')
                    resp_form=resp_soup.find("form")
                    resp_table=resp_form.find_all('table')[5]
                    resp_trs=resp_table.find_all("tr")
                    for tr in resp_trs:
                        custom_table.append(tr)
                    driver.quit()
                # print(custom_table.find_all_next("tr").__len__())
                final_html = "<html><head><title>LRB Search Results</title><script language='javascript'>function funcNewWindow(url) {var x;x = window.open(url, 'newwin', 'height=600, width=800, left=25, top=25, resizable, scrollbars=yes, status=1');}</script></head><script type='text/javascript' src='/lawReporting/javascript/validRequest.js'></script><body topmargin=0 leftmargin=0><form name=form><table border=0 width='100%' cellspacing=0 cellpadding=0 align=center><tr><td align=center><br><table border=0 align=center><tr><td align=right>&nbsp;</td><td><font color='#000099' face=arial size=5>Slip Decisions Search Results</font></td></tr><tr><td colspan=2><table border=0><tr><td valign=top><table border=0 cellspacing=1 cellpadding=1><tr bgcolor=#e6e6e6><td><font face=arial size=2><b>Search Criteria</b></font></td></tr><tr><td><font face=arial size=2> &nbsp; &nbsp; Decision Start Date :</font><font face=arial size=2 color=#000099><b>01/01/2024</b></font></td></tr><tr><td><font face=arial size=2> &nbsp; &nbsp; Decision End Date :</font><font face=arial size=2 color=#000099><b>02/01/2024</b></font></td></tr><tr><td><font face=arial size=2> &nbsp; &nbsp; Court :</font><font face=arial size=2 color=#000099><b>App Div, 1st Dept</b></font></td></tr></table></td></tr></table><br><table border=0 width='100%' cellspacing=1 cellpadding=1><tr><td><font face=arial size=2><b>Total number of records found: 229</b>&nbsp; &nbsp;&nbsp; &nbsp;</font></td></tr><tr><td colspan=4 align=center><input type=button name=again value='Search Again'onclick='history.back()'> <input type=button name=cancelvalue='Home Page'onclick=location.href='http://www.nycourts.gov/reporter/'><br><br></td></tr><tr><td><table></table></td></tr></table></td></tr></table></td></tr></table></form></body></html>"
                final_parser = BeautifulSoup(final_html, 'html.parser')
                final_form = final_parser.find("form")
                final_table = final_form.find_all('table')[5]
                final_table.replaceWith(custom_table)
                final_form.replaceWith(custom_form)
                const_html="<html><head><title>LRB Search Results</title><script language='javascript'>function funcNewWindow(url) {var x;x = window.open(url, 'newwin', 'height=600, width=800, left=25, top=25, resizable, scrollbars=yes, status=1');}</script></head><script type='text/javascript' src='/lawReporting/javascript/validRequest.js'></script><body topmargin=0 leftmargin=0>"+str(final_form)+"</body></html>"
                # print(const_html)
                text = self._clean_text(const_html)
                html_tree = self._make_html_tree(text)
                if hasattr(html_tree, "rewrite_links"):
                    html_tree.rewrite_links(fix_links_in_lxml_tree,
                                            base_href=self.request["url"])
                return html_tree
        finally:
            # Close the browser
            driver.quit()
        text = self._clean_text(resp_html)
        html_tree = self._make_html_tree(text)
        if hasattr(html_tree, "rewrite_links"):
            html_tree.rewrite_links(fix_links_in_lxml_tree, base_href=self.request["url"])
        return html_tree

    def get_state_name(self):
        return "New York"

    def get_class_name(self):
        return "ny"

    def get_court_name(self):
        return "New York Court of Appeals"

    def get_court_type(self):
        return "state"

    @override
    def download_pdf(self, data, objectId):
        pdf_url = data.__getitem__('pdf_url')
        year = int(data.__getitem__('year'))
        court_name = data.get('court_name')
        court_type = data.get('court_type')
        state_name = data.get('state')

        update_query = {}
        if str(pdf_url).__contains__('motions'):
            update_query.__setitem__("opinion_type", "motion")
        else:
            update_query.__setitem__("opinion_type", "opinion")

        if str(court_type).__eq__('state'):
            path = "/synology/PDFs/US/juriscraper/" + court_type + "/" + state_name + "/" + court_name + "/" + str(year)
        else:
            path = "/synology/PDFs/US/juriscraper/" + court_type + "/" + court_name + "/" + str(year)

        obj_id = str(objectId)
        download_pdf_path = os.path.join(path, f"{obj_id}.pdf")
        os.makedirs(path, exist_ok=True)

        # Create a temporary download directory
        temp_download_dir = os.path.join(os.path.expanduser("~"), "Downloads", "temp_pdf_downloads")
        os.makedirs(temp_download_dir, exist_ok=True)

        try:
            if str(pdf_url).endswith(".htm") or str(pdf_url).endswith(".html"):
                options = webdriver.ChromeOptions()
                options.add_argument("--no-sandbox")
                options.add_argument("--headless")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36")
                options.add_argument("--disable-blink-features=AutomationControlled")

                # Use proxy as required
                proxy = "http://p.webshare.io:9999"  # Replace with your proxy
                options.add_argument(f"--proxy-server={proxy}")

                # Create a WebDriver instance
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
                driver.get(pdf_url)
                driver_content = driver.page_source
                if driver_content.__contains__('Sorry, but the page you requested') and driver_content.__contains__('We apologize for any inconvenience this may have caused you.'):
                    raise Exception('Html not found')
                soup = BeautifulSoup(driver_content, 'html.parser')
                # print(soup.text)
                center_divs = soup.find_all('div', align='center')
                for div in center_divs:
                    if div and div.find('input', {'value': 'Return to Decision List'}):
                        div.decompose()

                # Find all anchor tags and remove the href attribute
                for tag in soup.find_all('a'):
                    del \
                    tag[
                        'href']

                # Find all <p> tags and remove the ones that are empty
                for p in soup.find_all('p'):
                    if not p.get_text(strip=True):  # Check if the <p> tag is empty or contains only whitespace
                        p.decompose()  # Remove the <p> tag

                # Print the modified HTML
                modified_html = soup.prettify()
                pdfkit.from_string(modified_html, download_pdf_path)
                update_query.__setitem__("response_html", modified_html)
                update_query.__setitem__("processed", 0)
                self.judgements_collection.update_one({'_id': objectId}, {'$set': update_query})
                driver.quit()

            elif str(pdf_url).endswith(".pdf"):
                # Use a more reliable approach for PDF downloads
                options = webdriver.ChromeOptions()
                options.add_argument("--no-sandbox")
                options.add_argument("--headless")
                options.add_argument("--window-size=1920x1080")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36")
                options.add_argument("--disable-blink-features=AutomationControlled")

                # Use proxy as required
                proxy = "http://p.webshare.io:9999"  # Replace with your proxy
                options.add_argument(f"--proxy-server={proxy}")

                # Set preferences for downloading PDFs automatically without a prompt
                prefs = {
                    "download.default_directory": temp_download_dir, "download.prompt_for_download": False, "download.directory_upgrade": True, "plugins.always_open_pdf_externally": True, "safebrowsing.enabled": True}
                options.add_experimental_option("prefs", prefs)

                # Create a WebDriver instance
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

                try:
                    # Navigate to the PDF URL
                    print(f"Attempting to download PDF from: {pdf_url}")
                    driver.get(pdf_url)

                    # Wait for download to complete (up to 30 seconds)
                    max_wait = 30
                    wait_time = 0
                    pdf_filename = \
                    pdf_url.split('/')[
                        -1]
                    expected_file = os.path.join(temp_download_dir, pdf_filename)

                    while not os.path.exists(expected_file) and wait_time < max_wait:
                        time.sleep(1)
                        wait_time += 1
                        print(f"Waiting for download to complete... {wait_time}s")

                    if os.path.exists(expected_file):
                        # Move the file to the final destination
                        shutil.move(expected_file, download_pdf_path)
                        print(f"PDF successfully downloaded to: {download_pdf_path}")
                        update_query.__setitem__("processed", 0)
                        self.judgements_collection.update_one({'_id': objectId}, {'$set': update_query})
                    else:
                        # Try direct download with requests as fallback, still using proxy
                        print("Selenium download failed, trying direct download with requests...")
                        proxies = {
                            "http": "http://p.webshare.io:9999", "https": "http://p.webshare.io:9999"}
                        response = requests.get(pdf_url, stream=True, proxies=proxies)
                        if response.status_code == 200:
                            with open(download_pdf_path, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                            print(f"PDF successfully downloaded with requests to: {download_pdf_path}")
                            update_query.__setitem__("processed", 0)
                            self.judgements_collection.update_one({'_id': objectId}, {'$set': update_query})
                        else:
                            raise Exception(f"Failed to download PDF. Status code: {response.status_code}")
                finally:
                    driver.quit()
            else:
                print(f"Invalid pdf extension: {pdf_url}")
                raise Exception(f"Invalid pdf extension: {pdf_url}")
        except Exception as e:
            print(f"Error while downloading the PDF: {e}")
            update_query.__setitem__("processed", 2)
            self.judgements_collection.update_one({"_id": objectId}, {"$set": update_query})
            # If there was an error, return None to indicate failure
            return None
        return download_pdf_path

    def set_selenium_driver(self):
        # Setup the Chrome WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36")
        options.add_argument("--disable-blink-features=AutomationControlled")

        proxy = "http://p.webshare.io:9999"  # Replace with your proxy
        options.add_argument(f"--proxy-server={proxy}")
        # Create a WebDriver instance
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver

    def set_headless_selenium_driver(self):
        # Setup the Chrome WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--headless")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36")
        options.add_argument("--disable-blink-features=AutomationControlled")

        proxy = "http://p.webshare.io:9999"  # Replace with your proxy
        options.add_argument(f"--proxy-server={proxy}")
        # Create a WebDriver instance
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        # start_date=datetime(2024,1,1)
        # end_date=datetime(2024,7,31)
        dates = (start_date, end_date)
        print(dates)
        self._download_backwards(dates)
        return 0
