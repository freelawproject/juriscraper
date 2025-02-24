# Author: Michael Lissner
# Date created: 2013-06-21
from datetime import datetime
from juriscraper.opinions.united_states.state import wva
from juriscraper.lib.string_utils import convert_date_string

class Site(wva.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.courtswv.gov/appellate-courts/intermediate-court-of-appeals/opinions/prior-terms"

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        print(f"start : {start_date} and end : {end_date}")
        self.page = 0
        total_opinions = 0
        codes1 = {
            "MD": "MD-Published",
            "SO": "SO-Published",
            "PC": "PC-Published",
            "SEP": "SEP-Separate",
        }
        codes2 = {
            "CR-F": "CR-F (Felony (non-Death Penalty))",
            "CR-M": "CR-M (Misdemeanor)",
            "CR-O": "CR-O (Criminal-Other)",
            "TCR": "TCR (Tort, Contract, and Real Property)",
            "PR": "PR (Probate)",
            "FAM": "FAM (Family)",
            "JUV": "JUV (Juvenile)",
            "CIV-O": "CIV-O (Civil-Other)",
            "WC": "WC (Workers Compensation)",
            "TAX": "TAX (Revenue (Tax))",
            "ADM": "ADM (Administrative Agency-Other)",
            "MISC": "MISC (Appeal by Right-Other)",
            "OJ-H": "OJ-H (Habeas Corpus)",
            "OJ-M": "OJ-M (Writ Application-Other)",
            "OJ-P": "OJ-P (Writ Application-Other)",
            "L-ADM": "L-ADM (Bar Admis   sion)",
            "L-DISC": "L-DISC (Bar Discipline/Eligibility)",
            "L-DISC-O": "L-DISC-O (Bar/Judiciary Proceeding-Other)",
            "J-DISC": "J-DISC (Bar/Judiciary Proceeding-Other)",
            "CERQ": "CERQ (Certified Question)",
            "OJ-O": "OJ-O (Original Proceeding/Appellate Matter-Other)",
            "POST": "POST (Post-Conviction Appeal)",
        }

        while True:
            self.url = (
                f"https://www.courtswv.gov/appellate-courts/intermediate-court-of-appeals/opinions/prior-terms?page={self.page}&field_sca_opinion_year_value={self.year}&field_ica_opinion_year_value={self.year}"
            )
            # if not self.downloader_executed:
            self.html = self._download()

            for cell in self.html.xpath(self.cell_path % 3):
                anchor = cell.xpath(".//a[1]")
                if anchor:
                    text = anchor[0].text_content()
                    if text:
                        self.names.append(text)
                    else:
                        self.names.append("null")
                else:
                    text=cell.xpath(".//p[1]")
                    self.names.append(text[0].text_content())

            for cell in self.html.xpath(self.cell_path % 3):
                anchor = cell.xpath(".//a[1]")
                if anchor:
                    href = anchor[0].get("href")
                    if href: self.urls.append(href)
                    else:
                        self.urls.append("null")
                else:
                    self.urls.append("null")


            for cell in self.html.xpath(self.cell_path % 1):
                self.dates.append(
                    convert_date_string(cell.text_content().strip()))

            for cell in self.html.xpath(self.cell_path % 2):
                self.dockets.append([cell.text_content().lower().strip()])

            self.status.extend(
                self.decode_cell_text(self.cell_path % 5, codes1))

            self.nature.extend(
                self.decode_cell_text(self.cell_path % 4, codes2))

            next_page = self.html.xpath("//a[@rel='next']")
            if not next_page:
                break
            self.page += 1

        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()

        self._post_parse()

        self._check_sanity()
        self._date_sort()
        self._make_hash()

        return total_opinions

    def get_class_name(self):
        return "wvactapp"

    def get_court_name(self):
        return "Intermediate Court of Appeals of West Virginia"
