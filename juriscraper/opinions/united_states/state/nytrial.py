"""
Scraper template for the 'Other Courts' of the NY Reporter
Court Contact: phone: (518) 453-6900
Author: Gianfranco Rossi
History:
 - 2024-01-05, grossir: created
"""
import os
import re
from datetime import date
from itertools import chain
from typing import Any, Dict, List, Optional

import pdfkit
import requests
from bs4 import BeautifulSoup
from dateutil.rrule import MONTHLY, rrule
from lxml.html import fromstring
from tldextract.tldextract import update
from typing_extensions import override

from juriscraper.AbstractSite import logger
from juriscraper.lib.judge_parsers import normalize_judge_string
from juriscraper.lib.string_utils import harmonize
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_regex: str  # to be defined on inheriting classes
    base_url = "https://nycourts.gov/reporter/slipidx/miscolo.shtml"
    first_opinion_date = date(2003, 12, 1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.court_id = self.__module__
        self.url = self.build_url()

        date_keys = rrule(
            MONTHLY, dtstart=self.first_opinion_date, until=date(2023, 12, 30)
        )
        self.back_scrape_iterable = [i.date() for i in date_keys]
        self.expected_content_types = ["application/pdf", "text/html"]

    def build_url(self, target_date: Optional[date] = None) -> str:
        """URL as is loads most recent month page
        There is an URL for each month of each year back to Dec 2003

        :param target_date: used to extract month and year for backscraping
        :returns str: formatted url
        """
        if not target_date:
            return self.base_url

        end = f"_{target_date.year}_{target_date.strftime('%B')}.shtml"

        return self.base_url.replace(".shtml", end)

    def is_court_of_interest(self, court: str) -> bool:
        """'Other Courts' of NY Reporter consists of 10 different
        family of sources. Each family has an scraper that inherits
        from this class and defines a `court_regex` to capture those
        that belong to its family

        For example
        "Civ Ct City NY, Queens County" and "Civ Ct City NY, NY County"
        belong to nycivct family

        :param court: court name
        :return: true if court name matches
                family of courts of calling scraper
        """
        return bool(re.search(self.court_regex, court))

    def _process_html(self) -> None:
        """Parses a page's HTML into opinion dictionaries

        :return: None
        """
        row_xpath = "//table[caption]//tr[position()>1 and td]"
        for row in self.html.xpath(row_xpath):
            court = re.sub(
                r"\s+", " ", row.xpath("td[2]")[0].text_content()
            ).strip(", ")

            if not self.is_court_of_interest(court):
                logger.debug("Skipping %s", court)
                continue

            url = row.xpath("td[1]/a/@href")[0]
            name = harmonize(row.xpath("td[1]/a")[0].text_content())
            opinion_date = row.xpath("td[3]")[0].text_content()
            slip_cite = row.xpath("td[4]")[0].text_content()
            status = "Unpublished" if "(U)" in slip_cite else "Published"

            self.cases.append(
                {
                    "name": name,
                    "date": opinion_date,
                    "status": status,
                    "url": url,
                    "citation": [slip_cite],
                    "child_court": court,
                }
            )

    def _get_docket_numbers(self) -> List[str]:
        """Overriding from OpinionSiteLinear, since docket numbers are
        not in the HTML and they are required

        We will get them on the extract_from_text stage on courtlistener

        :return: list of empty strings values
        """
        return ["" for _ in self.cases]

    def _download_backwards(self, target_date: date) -> None:
        """Method used by backscraper to download historical records

        :param target_date: an element of self.back_scrape_iterable
        :return: None
        """
        self.url = self.build_url(target_date)

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Extract values from opinion's text

        :param scraped_text: pdf or html string contents
        :return: dict where keys match courtlistener model objects
        """
        pattern = r"Judge:\s?(.+)|([\w .,]+), [JS]\.\s"
        judge = self.match(scraped_text, pattern)

        pattern = r"</table><br><br\s?/?>\s?(.*)\r?\n|Docket Number:\s?(.+)"
        docket_number = self.match(scraped_text, pattern)

        pattern = r"\[(?P<volume>\d+) (?P<reporter>Misc 3d) (?P<page>.+)\]"
        cite_match = re.search(pattern, scraped_text[:2000])

        # Only for .htm links
        full_case = None
        if scraped_text.find("<table") != -1:
            # replace <br> with newlines because text_content() replaces <br>
            # with whitespace. If not, case names would lack proper separation
            scraped_text = scraped_text.replace("<br>", "\n")
            full_case = fromstring(scraped_text).xpath("//table")
            full_case = full_case[1].text_content() if full_case else ""

        metadata = {
            "Docket": {"docket_number": docket_number},
        }

        if judge:
            metadata["Opinion"] = {
                "author_str": normalize_judge_string(judge)[0]
            }
        if cite_match:
            metadata["Citation"] = cite_match.groupdict("")
            metadata["Citation"]["type"] = 2  # 'State' type in courtlistener
        if full_case:
            full_case = harmonize(full_case)
            metadata["Docket"]["case_name_full"] = full_case
            metadata["OpinionCluster"] = {"case_name_full": full_case}

        return metadata

    @staticmethod
    def match(scraped_text: str, pattern: str) -> str:
        """Returns first match

        :param scraped_text: HTML or PDF string content
        :param pattern: regex string

        :returns: first match
        """
        m = re.findall(pattern, scraped_text)
        r = list(filter(None, chain.from_iterable(m)))
        return r[0].strip() if r else ""

    def get_court_type(self):
        return "state"

    def get_state_name(self):
        return "New York"

    @override
    def download_pdf(self, data, objectId):
        pdf_url = str(data.__getitem__('pdf_url'))
        year = int(data.__getitem__('year'))

        court_name = data.get('court_name')
        court_type = data.get('court_type')
        state_name = data.get('state')

        if str(court_type).__eq__('state'):
            path = "/synology/PDFs/US/juriscraper/"+court_type+"/"+state_name+"/"+court_name+"/"+str(year)
        else:
            path = "/synology/PDFs/US/juriscraper/" + court_type + "/" + court_name + "/" + str(year)

        obj_id = str(objectId)
        download_pdf_path = os.path.join(path, f"{obj_id}.pdf")
        os.makedirs(path, exist_ok=True)
        update_query={}
        try:
            response = requests.get(url=pdf_url, headers={"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"}, proxies={"http": "p.webshare.io:9999","https": "p.webshare.io:9999"}, timeout=120)
            response.raise_for_status()
            if pdf_url.endswith('.html') or pdf_url.endswith('.htm'):
                # if pdf url contains html then refine it and convert html to pdf and also save modified html
                soup = BeautifulSoup(response.text, 'html.parser')
                # print(soup.text)
                center_divs = soup.find_all('div', align='center')
                for div in center_divs:
                    if div and div.find('input',{'value': 'Return to Decision List'}):
                        div.decompose()

                # Find all anchor tags and remove the href attribute
                for tag in soup.find_all('a'):
                    del tag['href']

                # Find all <p> tags and remove the ones that are empty
                for p in soup.find_all('p'):
                    if not p.get_text(strip=True):  # Check if the <p> tag is empty or contains only whitespace
                        p.decompose()  # Remove the <p> tag

                # Print the modified HTML
                modified_html = soup.prettify()
                pdfkit.from_string(modified_html, download_pdf_path)
                update_query.__setitem__("response_html", modified_html)
            elif pdf_url.endswith(".pdf"):
                with open(download_pdf_path, 'wb') as file:
                    file.write(response.content)
            else:
                with open(download_pdf_path, 'wb') as file:
                    file.write(response.content)

            # if pdf has been downloaded successfully mark processed as 0 and update the record
            update_query.__setitem__("processed", 0)
            self.judgements_collection.update_one({"_id": objectId}, {"$set": update_query})
        except Exception as e:
            # if any error occur during downloading the pdf print the error and mark the record as processed 2
            print(f"Error while downloading the PDF: {e}")
            update_query.__setitem__("processed", 2)
            self.judgements_collection.update_one({"_id": objectId}, {"$set": update_query})
        return download_pdf_path

