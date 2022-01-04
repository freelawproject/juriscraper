# Author: Michael Lissner
# Date created: 2013-06-11

import re
from datetime import datetime
from time import sleep

from lxml import html

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteWebDriven import OpinionSiteWebDriven


class Site(OpinionSiteWebDriven):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.sdjudicial.com/sc/scopinions.aspx"
        self.uses_selenium = True
        self.year = False

    def _get_download_urls(self):
        path = '//tr[contains(@id, "ctl00xmainCopyxWGOpinions_r")]//a[2]/@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        if self.year == 2005:
            strings = []
            path = '//tr[contains(@id, "ctl00xmainCopyxWGOpinions_r")]/td[2]'
            for e in self.html.xpath(path):
                strings.append(
                    html.tostring(e, method="text", encoding="unicode")
                )
        else:
            path = '//tr[contains(@id, "ctl00xmainCopyxWGOpinions_r")]/td[2]/text()'
            strings = list(self.html.xpath(path))
        case_names = []
        for s in strings:
            try:
                case_name = re.search(
                    r"(.*)(\d{4} S\.?D\.? \d{1,4})", s, re.MULTILINE
                ).group(1)
                case_names.append(titlecase(case_name.lower()))
            except AttributeError:
                print(f"AttributeError on: {titlecase(s)}")
                if "myrl" in s.lower() and self.year == 2000:
                    case_names.append("Lends His Horse v. Myrl & Roy")
                elif "springer" in s.lower() and self.year == 2000:
                    case_names.append("State v. Springer-Ertl")
                elif (
                    "formatting provided courtesy" in s.lower()
                    and self.year == 2000
                ):
                    case_names.append("Lois F. Henry v. Harold L. Henry")
                elif "spec. v. avera" in s.lower() and self.year == 2001:
                    case_names.append(
                        "Drs., Residents, and Orth. Surg. Spec. v. Avera St. Luke"
                    )
                elif "clausen" in s.lower() and self.year == 2003:
                    case_names.append(
                        "Kelly Clausen v. Northern Plains Recycling, Fireman"
                    )
                elif "burkhart" in s.lower() and self.year == 2003:
                    case_names.append("Burkhart v. Lillehaug and Lillihaug")
                elif "bennett" in s.lower() and self.year == 2003:
                    case_names.append(
                        "State of South Dakota, ex rel., Megan Bennett v. Thomas G. Peterson"
                    )
                elif "duane" in s.lower() and self.year == 2004:
                    case_names.append(
                        "State of South Dakota v. Duane J. St. John"
                    )
                elif "square" in s.lower() and self.year == 2005:
                    case_names.append(
                        "Town Square Limited Partnership v. Clay County Board of Equalization"
                    )
                elif "toft" in s.lower() and self.year == 2006:
                    case_names.append("Toft v. Toft & Stratmeyer")
                elif "masteller" in s.lower() and self.year == 2006:
                    case_names.append("Masteller v. Champion Home")
                elif "nuzum" in s.lower() and self.year == 2006:
                    case_names.append("State v. Nuzum")
                elif "aaberg" in s.lower() and self.year == 2006:
                    case_names.append("State v. Aaberg")
                elif "bryan" in s.lower() and self.year == 2006:
                    case_names.append("O'Bryan v. Ashland")
                elif "j.d.m.c." in s.lower() and self.year == 2007:
                    case_names.append("In Re the Matter of J.D.M.C.")
                elif "argus" in s.lower() and self.year == 2007:
                    case_names.append("Argus Leader v. Hagen")
                elif "nedved" in s.lower() and self.year == 2007:
                    case_names.append(
                        "Countryside S. Homeowners Assoc. v. Nedved"
                    )
                elif "gisi" in s.lower() and self.year == 2007:
                    case_names.append("Gisi v. Gisi")
                elif "western" in s.lower() and self.year == 2007:
                    case_names.append("Great Western Bank v. H&E Enterprises")
                elif "canyon" in s.lower() and self.year == 2007:
                    case_names.append("Jackson v. Canyon Place Homeowners")
                elif "vansteenwyk" in s.lower() and self.year == 2007:
                    case_names.append("Vanteenwyk v. Baumgartner Trees")
                elif "jewett" in s.lower() and self.year == 2011:
                    case_names.append("Jewett v. Real Tuff")
                elif "jensen" in s.lower() and self.year == 2011:
                    case_names.append("State v. Jensen")
                elif "cook" in s.lower() and self.year == 2011:
                    case_names.append("Orr v. Cook")
                elif "living" in s.lower() and self.year == 2011:
                    case_names.append("Benson Living Trust")
                else:
                    raise AttributeError
        return case_names

    def _get_case_dates(self):
        path = '//tr[contains(@id, "ctl00xmainCopyxWGOpinions_r")]/td[1]/@uv'
        return [
            datetime.strptime(date_string, "%m/%d/%Y").date()
            for date_string in self.html.xpath(path)
        ]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '//tr[contains(@id, "ctl00xmainCopyxWGOpinions_r")]//a[2]/@href'
        docket_numbers = []
        for url in self.html.xpath(path):
            try:
                # New style: easy
                docket_numbers.append(re.search(r"(\d+).pdf", url).group(1))
            except AttributeError:
                docket_numbers.append(None)
        return docket_numbers

    def _get_citations(self):
        if self.year == 2005:
            strings = []
            path = '//tr[contains(@id, "ctl00xmainCopyxWGOpinions_r")]/td[2]'
            for e in self.html.xpath(path):
                strings.append(
                    html.tostring(e, method="text", encoding="unicode")
                )
        else:
            path = '//tr[contains(@id, "ctl00xmainCopyxWGOpinions_r")]/td[2]/text()'
            strings = list(self.html.xpath(path))
        neutral_cites = []
        for s in strings:
            try:
                neutral_cite = re.search(
                    r"(.*)(\d{4} S\.?D\.? \d{1,4})", s, re.MULTILINE
                ).group(2)
                neutral_cites.append(titlecase(neutral_cite))
            except AttributeError:
                if "myrl" in s.lower() and self.year == 2000:
                    neutral_cites.append("2000 SD 146")
                elif "springer" in s.lower() and self.year == 2000:
                    neutral_cites.append("2000 SD 56")
                elif (
                    "formatting provided courtesy" in s.lower()
                    and self.year == 2000
                ):
                    neutral_cites.append("2000 SD 4")
                elif "spec. v. avera" in s.lower() and self.year == 2001:
                    neutral_cites.append("2001 SD 9")
                elif "clausen" in s.lower() and self.year == 2003:
                    neutral_cites.append("2003 SD 63")
                elif "burkhart" in s.lower() and self.year == 2003:
                    neutral_cites.append("2003 SD 62")
                elif "bennett" in s.lower() and self.year == 2003:
                    neutral_cites.append("2003 SD 16")
                elif "duane" in s.lower() and self.year == 2004:
                    neutral_cites.append("2004 SD 15")
                elif "square" in s.lower() and self.year == 2005:
                    neutral_cites.append("2005 SD 99")
                elif "toft" in s.lower() and self.year == 2006:
                    neutral_cites.append("2006 SD 91")
                elif "masteller" in s.lower() and self.year == 2006:
                    neutral_cites.append("2006 SD 90")
                elif "nuzum" in s.lower() and self.year == 2006:
                    neutral_cites.append("2006 SD 89")
                elif "aaberg" in s.lower() and self.year == 2006:
                    neutral_cites.append("2006 SD 58")
                elif "bryan" in s.lower() and self.year == 2006:
                    neutral_cites.append("2006 SD 56")
                elif "j.d.m.c." in s.lower() and self.year == 2007:
                    neutral_cites.append("2007 SD 97")
                elif "argus" in s.lower() and self.year == 2007:
                    neutral_cites.append("2007 SD 96")
                elif "nedved" in s.lower() and self.year == 2007:
                    neutral_cites.append("2007 SD 70")
                elif "gisi" in s.lower() and self.year == 2007:
                    neutral_cites.append("2007 SD 39")
                elif "western" in s.lower() and self.year == 2007:
                    neutral_cites.append("2007 SD 38")
                elif "canyon" in s.lower() and self.year == 2007:
                    neutral_cites.append("2007 SD 37")
                elif "vansteenwyk" in s.lower() and self.year == 2007:
                    neutral_cites.append("2007 SD 36")
                elif "jewett" in s.lower() and self.year == 2011:
                    neutral_cites.append("2011 S.D.33")
                elif "jensen" in s.lower() and self.year == 2011:
                    neutral_cites.append("2011 S.D.32")
                elif "cook" in s.lower() and self.year == 2011:
                    neutral_cites.append("2011 S.D.31")
                elif "living" in s.lower() and self.year == 2011:
                    neutral_cites.append("2011 S.D.30")
                else:
                    raise AttributeError
        return neutral_cites

    def _download_backwards(self, year):
        self.year = year
        self.initiate_webdriven_session()
        elems = self.webdriver.find_elements_by_class_name("igeb_ItemLabel")
        elem = [elem for elem in elems if elem.text == str(year)][0]
        elem.click()
        sleep(5)

        text = self.webdriver.page_source
        html_tree = html.fromstring(text)
        html_tree.make_links_absolute(self.url)

        remove_anchors = lambda url: url.split("#")[0]
        html_tree.rewrite_links(remove_anchors)

        self.html = html_tree
        self.status = 200
        self.webdriver.quit()
