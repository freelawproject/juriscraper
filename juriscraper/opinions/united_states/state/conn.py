import re
from datetime import date, datetime
from typing import Tuple

from dateutil.parser import parse

from casemine.casemine_util import CasemineUtil
from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import clean_string
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_abbv = "sup"
    start_year = 2000
    base_url = "http://www.jud.ct.gov/external/supapp/archiveARO{}{}.htm"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"

        self.current_year = int(date.today().strftime("%Y"))
        self.url = self.make_url(self.current_year)
        self.make_backscrape_iterable(kwargs)

        self.cipher = "AES256-SHA256"
        self.set_custom_adapter(self.cipher)

    @staticmethod
    def find_published_date(date_str: str) -> str:

        m = re.search(
            r"(\b\d{1,2}/\d{1,2}/\d{2,4}\b)|(\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}\b)",
            date_str,
        )
        return m.groups()[0] if m.groups()[0] else m.groups()[1]

    def extract_dockets_and_name(self, row) -> Tuple[str, str]:

        text = " ".join(row.xpath("ancestor::li[1]//text()"))
        clean_text = re.sub(r"[\n\r\t\s]+", " ", text)
        m = re.match(
            r"(?P<dockets>[SAC0-9, ]+)(?P<op_type> [A-Z].*)? - (?P<case_name>.*)",
            clean_text,
        )
        if not m:
            # Handle bad inputs
            m = re.match(
                r"(?P<dockets>[SAC0-9, ]+)(?P<op_type> [A-Z].*)? (?P<case_name>.*)",
                clean_text,
            )
        op_type = m.group("op_type")
        name = m.group("case_name")
        if op_type:
            name = f"{name} ({op_type.strip()})"
        return m.group("dockets"), name

    def _process_html(self) -> None:
        for row in self.html.xpath(".//*[contains(@href, '.pdf')]"):
            pub = row.xpath('preceding::*[contains(., "Published")][1]/text()')
            if pub:
                date_filed_is_approximate = False
                date_filed = self.find_published_date(pub[0])
            else:
                date_filed = f"{self.current_year}-07-01"
                date_filed_is_approximate = True

            # curr_date = datetime.strptime(date_filed, "%m/%d/%Y").strftime("%d/%m/%Y")
            curr_date = datetime.strptime(date_filed, "%B %d, %Y").strftime("%d/%m/%Y")
            res = CasemineUtil.compare_date(self.crawled_till, curr_date)
            if res == 1:
                return
            dockets, name = self.extract_dockets_and_name(row)
            self.cases.append(
                {
                    "url": row.get("href"),
                    "name": name,
                    "docket": dockets.split(', '),
                    "date": date_filed,
                    "date_filed_is_approximate": date_filed_is_approximate,
                }
            )

    def make_url(self, year: int) -> str:
        year_str = str(year % 2000).zfill(2)
        return self.base_url.format(self.court_abbv, year_str)

    def extract_from_text(self, scraped_text: str):
        metadata = {"OpinionCluster": {}}
        judges_end = 1_000_000
        regex_date = r"Argued.+officially\sreleased\s(?P<date>[JFMASOND]\w+\s\d{1,2},\s\d{4})"
        if date_match := re.search(regex_date, scraped_text):
            try:
                date_filed = parse(date_match.group("date")).date()
                metadata["OpinionCluster"].update(
                    {
                        "date_filed": date_filed,
                        "date_filed_is_approximate": False,
                    }
                )
            except ValueError:
                pass

            judges_end = date_match.start()

        ph_start_index = scraped_text.find("Procedural History")
        if ph_start_index != -1:
            end_index = scraped_text.find("Opinion", ph_start_index)
            if end_index != -1:
                procedural_history = scraped_text[
                    ph_start_index + 18 : end_index
                ]
                metadata["OpinionCluster"]["procedural_history"] = (
                    clean_extracted_text(procedural_history)
                )

            judges_end = min(judges_end, ph_start_index)

        sy_start_index = scraped_text.find("Syllabus")
        if sy_start_index != -1:
            if ph_start_index:
                syllabus = scraped_text[sy_start_index + 8 : ph_start_index]
                metadata["OpinionCluster"]["syllabus"] = clean_extracted_text(
                    syllabus
                )

            judges_end = min(judges_end, sy_start_index)
        if judges_end != 1_000_000:
            if docket_match := list(
                re.finditer(r"[AS]C\s\d{5}", scraped_text[:judges_end])
            ):
                judges = scraped_text[docket_match[-1].end() : judges_end]
                clean_judges = []
                for judge in (
                    judges.strip("\n )(").replace(" and ", ",").split(",")
                ):
                    if not judge.strip() or "Js." in judge or "C. J." in judge:
                        continue
                    clean_judges.append(judge.strip("\n "))

                metadata["OpinionCluster"]["judges"] = "; ".join(clean_judges)

        return metadata

    def _download_backwards(self, start_year: int, end_year : int) -> None:

        if start_year == end_year:
            logger.info("Backscraping for year %s", start_year)
            self.url = self.make_url(start_year)
            self.html = self._download()
            self._process_html()
        else:
            logger.info(f"Backscraping from the year {start_year} to {end_year}")
            n = end_year-start_year
            curr_year = start_year
            i=0
            while i<=n:
                self.url = self.make_url(curr_year)
                self.html = self._download()
                self._process_html()
                curr_year+=1
                i += 1


    def make_backscrape_iterable(self, kwargs: dict) -> None:
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        start = int(start) if start else self.start_year
        end = int(end) + 1 if end else self.current_year

        self.back_scrape_iterable = range(start, end)

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        # start_date=datetime(2020,1,1)

        self._download_backwards(start_date.year, end_date.year)
        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return len(self.cases)

    def get_state_name(self):
        return "Connecticut"

    def get_class_name(self):
        return "conn"

    def get_court_type(self):
        return "state"

    def get_court_name(self):
        return "Supreme Court of Connecticut"

def clean_extracted_text(text: str) -> str:

    clean_lines = []
    skip_next_line = False
    for line in text.split("\n"):
        if skip_next_line:
            skip_next_line = False
            continue
        if re.search(r"CONNECTICUT LAW JOURNAL|0\sConn\.\s(App\.\s)?1", line):
            skip_next_line = True
            # following line for one of these regexes is the case name
            continue

        clean_lines.append(line)
    return clean_string("\n".join(clean_lines))

