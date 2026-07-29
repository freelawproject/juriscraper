"""Scraper for Third Circuit of Appeals
CourtID: ca3
Court Short Name: ca3
Author: Andrei Chelaru
Reviewer: mlr
Date created: 18 July 2014
History:
    - 2026-07-29: The RSS/podcast feed at
      /oralargument/OralArguments.xml was retired (404); switched to the
      "Oral Argument Files within last 30 days" HTML listing, which only
      exposes the audio file name and its upload timestamp.
"""

import re
from urllib.parse import quote

from juriscraper.lib.string_utils import fix_camel_case
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    base_url = "https://www2.ca3.uscourts.gov/oralarg/"
    # Audio file names bundle the docket number(s) and the case name
    # together, in a handful of shapes:
    #   14-2042_USAv.Noel.mp3
    #   10-4188USAv.Swan.mp3
    #   25_1497USAv.KevinChristmas.mp3
    #   26-1444_26-1445_InReLigadoNetworks.mp3
    #   26-2184 Mejia-Henriquez v. Attorney General USA.mp3
    docket_prefix_regex = re.compile(r"^\s*((?:\d{2}[-_]+\d{3,4}[-_ ]*)+)")
    docket_regex = re.compile(r"\d{2}[-_]+\d{3,4}")
    # Multi part arguments get a "_a", "_b", ... suffix
    part_regex = re.compile(r"_[a-z0-9]$", re.I)
    et_al_regex = re.compile(r"[,\s]*et\.?\s?al\.?", re.I)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www2.ca3.uscourts.gov/OralArgContents30.html"

    def _process_html(self):
        for row in self.html.xpath("//table//tr[td]"):
            # Build the URL from the file name rather than the anchor's
            # href: names containing an apostrophe ("Kelleyv.O'Malley.mp3")
            # close the court's single quoted href early, so lxml sees a
            # truncated URL. The cell's text is intact either way.
            file_name = row.xpath("td[1]")[0].text_content().strip()
            docket, name = self.parse_file_name(file_name)
            if not name:
                continue
            self.cases.append(
                {
                    "url": self.base_url + quote(file_name),
                    "docket": docket,
                    "name": name,
                    # The listing's second column is the file's upload
                    # timestamp; it is the only date the court exposes here
                    "date": row.xpath("td[2]/text()")[0].split()[0],
                }
            )

    def parse_file_name(self, file_name: str) -> tuple[str, str]:
        """Extract the docket number(s) and case name from an audio file name

        :param file_name: the audio file's name, extension included
        :return: a (docket numbers, case name) tuple
        """
        file_name = file_name.removesuffix(".mp3")

        match = self.docket_prefix_regex.match(file_name)
        if match:
            docket = ", ".join(
                re.sub(r"[-_]+", "-", d)
                for d in self.docket_regex.findall(match.group(1))
            )
            name = file_name[match.end() :]
        else:
            docket, name = "", file_name

        name = self.et_al_regex.sub(" ", self.part_regex.sub("", name))
        # `fix_camel_case` is a no-op on strings that already contain a
        # space, so feed it each underscore delimited chunk separately
        name = " ".join(
            fix_camel_case(chunk)
            for chunk in re.split(r"[_\s]+", name)
            if chunk
        )
        return docket, re.sub(r"\s*,\s*", ", ", name).strip(" .,;-")
