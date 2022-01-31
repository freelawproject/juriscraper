"""Scraper for Connecticut Supreme Court
CourtID: conn
Court Short Name: Conn.
Author: Asadullah Baig <asadullahbeg@outlook.com>
History:
- 2014-07-11: created
- 2014-08-08, mlr: updated to fix InsanityError on case_dates
- 2014-09-18, mlr: updated XPath to fix InsanityError on docket_numbers
- 2015-06-17, mlr: made it more lenient about date formatting
- 2016-07-21, arderyp: fixed to handle altered site format
- 2017-01-10, arderyp: restructured to handle new format use case that includes
        opinions without dates and flagged for 'future' publication
- 2022-02-02, satsuki-chan: Fixed docket and name separator, changed super
    class to OpinionSiteLinear
"""

from datetime import date

from lxml import etree

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import convert_date_string, normalize_dashes
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        current_year = date.today().strftime("%y")
        self.url = f"http://www.jud.ct.gov/external/supapp/archiveAROsup{current_year}.htm"
        self.status = "Published"
        self.cases = []

    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        # Strip inconsistently placed <font> and <br>
        # tags that make stable coverage almost impossible
        etree.strip_tags(self.html, "font", "br")
        path = '//table[@id="AutoNumber1"]//ul'
        for ul in self.html.xpath(path):
            preceding = ul.xpath("./preceding::*[1]")[0]
            preceding_text = " ".join(preceding.text_content().split()).strip(
                ":"
            )
            # Skip sections that are marked to be published at future date
            if preceding_text and not preceding_text.lower().endswith(" date"):
                # Below will fail if they change up string format
                date_string = preceding_text.split()[-1]
                for element in ul.xpath("./li | ./a"):
                    if element.tag == "li":
                        text = normalize_dashes(
                            " ".join(element.text_content().split())
                        )
                        if not text:
                            continue
                        anchor = element.xpath(".//a")[0]
                    elif element.tag == "a":
                        # Malformed html, see connappct_example.html
                        anchor = element
                        glued = f"{anchor.text_content()} {anchor.tail}"
                        text = normalize_dashes(" ".join(glued.split()))
                    docket = (
                        text.split("-")[0]
                        .split("Concurrence")[0]
                        .split("Dissent")[0]
                        .split("Appendix")[0]
                    )
                    try:
                        name = text.split("-", 1)[1]
                    except IndexError:
                        # Expected link text:
                        # - "AC44191 Dissent Marshall v. Commissioner of Motor Vehicles"
                        try:
                            name = text.split("Dissent", 1)[1]
                        except IndexError:
                            try:
                                name = text.split("Concurrence", 1)[1]
                            except IndexError:
                                try:
                                    name = text.split("Appendix", 1)[1]
                                except:
                                    logger.info(
                                        f"Name not found for case: '{text}'"
                                    )
                                    continue
                    self.cases.append(
                        {
                            "date": date_string,
                            "url": anchor.xpath("./@href")[0],
                            "docket": docket,
                            "name": name,
                        }
                    )
