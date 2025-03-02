from datetime import datetime
from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from lxml import html

from juriscraper.lib.utils import clean_date_string


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.la3circuit.org/"
        self.driver = None
        self.html = None  # Initialize HTML content

    def _setup_webdriver(self):
        """Set up the Selenium WebDriver."""
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")  # Run in headless mode
        self.driver = webdriver.Firefox(options=options)

    def _teardown_webdriver(self):
        """Close the Selenium WebDriver."""
        if self.driver:
            self.driver.quit()

    def _download(self, opinion_date=None):
        """
        Download the page using Selenium and interact with the 'Search Opinions' form.
        :param opinion_date: The opinion date to search for (YYYY-MM-DD).
        """
        self.downloader_executed = True
        try:
            self._setup_webdriver()
            self.driver.get(self.url)

            # Locate the dropdowns for year and month
            year_dropdown = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "MainContent_ddlSearchOpinions2_Year"))
            )
            month_dropdown = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "MainContent_ddlSearchOpinions2_Month"))
            )

            if opinion_date:
                opinion_date_obj = datetime.strptime(opinion_date, "%Y-%m-%d")
                year = str(opinion_date_obj.year)
                month = opinion_date_obj.strftime("%B")  # Full month name (e.g., "January")

                # Select the year
                year_dropdown.send_keys(year)

                # Select the month
                month_dropdown.send_keys(month)

            # Wait for the loading overlay to disappear
            WebDriverWait(self.driver, 20).until(
                EC.invisibility_of_element_located((By.ID, "dvLoading"))
            )

            # Locate and click the 'Search' button
            search_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.ID, "MainContent_btnSearchOpinionsByMonthYear"))
            )
            search_button.click()

            # Wait for the modal to appear
            modal = WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located((By.ID, "searchModal"))
            )

            # Extract the HTML content of the modal
            modal_html = modal.get_attribute("innerHTML")
            return modal_html

        except Exception as e:
            self.html = None  # Ensure self.html is reset if an error occurs
        finally:
            self._teardown_webdriver()

    def _process_html(self):
        """
        Parse the HTML content to extract opinions and populate attributes.
        """
        self.html = self._download()
        if not self.html:
            return

        tree = html.fromstring(self.html)

        # Extract rows from the table
        rows = tree.xpath("//table[@class='table table-striped table-responsive']//tr")

        # Initialize the list to store cases
        self.cases = []

        for i, row in enumerate(rows):
            try:
                # Skip header and footer rows
                if not row.xpath(".//h4//a") or "table-info-footer" in row.attrib.get("class", ""):
                    continue

                # Construct the case dictionary
                raw_date = row.xpath(".//strong[contains(text(), 'Opinion Date:')]/following-sibling::text()[1]")[0].strip()
                cleaned_date = clean_date_string(raw_date)  # Clean and reformat the date

                case = {
                    "name": row.xpath(".//strong[contains(text(), 'Case Title:')]/following-sibling::text()[1]")[0].strip(),
                    "url": row.xpath(".//h4//a/@href")[0],
                    "date": cleaned_date,  # Use the cleaned date
                    "docket": row.xpath(
                        ".//strong[starts-with(text(), 'CA') or starts-with(text(), 'KH') or starts-with(text(), 'CW') or starts-with(text(), 'KA') or starts-with(text(), 'WCA') or starts-with(text(), 'KW')]/text()"
                    )[0].strip(),
                    "lower_court": row.xpath(".//strong[contains(text(), 'Lower Court:')]/following-sibling::text()[1]")[0].strip(),
                    "status": "Published",  # Default status; adjust as needed
                    "date_filed_is_approximate": False,  # Default value; adjust as needed
                }

                # Add optional fields if present in the source data
                optional_fields = {
                    "judge": "Judge",
                    "citation": "Citation",
                    "summary": "Summary",
                    "cause": "Cause",
                    "disposition": "Disposition",
                    "division": "Division",
                    "adversary_number": "Adversary Number",
                    "nature_of_suit": "Nature of Suit",
                    "lower_court_number": "Lower Court Number",
                    "lower_court_judge": "Lower Court Judge",
                    "author": "Author",
                    "per_curiam": "Per Curiam",
                    "type": "Type",
                    "other_date": "Other Date",
                    "attorney": "Attorney",
                }

                for key, label in optional_fields.items():
                    try:
                        case[key] = row.xpath(f".//strong[contains(text(), '{label}:')]/following-sibling::text()[1]")[0].strip()
                    except IndexError:
                        pass  # Field is not present in the source data

                # Append the case to the list
                self.cases.append(case)

            except IndexError:
                continue
            except Exception:
                continue