"""Scraper for South Carolina Supreme Court
CourtID: sc
Court Short Name: S.C.
Author: TBM <-- Who art thou TBM? ONLY MLR gets to be initials!
History:
 - 04-18-2014: Created.
 - 09-18-2014: Updated by mlr.
 - 10-17-2014: Updated by mlr to fix InsanityError
 - 2017-10-04: Updated by mlr to deal with their anti-bot system. Crux of change
               is to ensure that we get a cookie in our session by visiting the
               homepage before we go and scrape. Dumb.
 - 2019-02-26: Restructured completely by arderyp

Contact information:
 - Help desk: (803) 734-1193, Travis
 - Security desk: 803-734-5906, Joe Hilke
 - Web Developer (who can help with firewall issues): 803-734-0373, Winkie Clark
"""

import datetime

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        today = datetime.date.today()
        self.url = (
            "http://www.sccourts.org/opinions/indexSCPub.cfm?year=%d&month=%d"
            % (today.year, today.month)
        )
        self.cases = []

    def _process_html(self):
        path = '//a[@class="blueLink2"][contains(./@href, ".pdf") or contains(./@href, "?orderNo=")]'
        for link in self.html.xpath(path):
            docket, name, url = self.extract_docket_name_url_from_link(link)
            date, summary = self.extract_date_summary_from_link(link)
            self.cases.append(
                {
                    "date": date,
                    "docket": docket,
                    "name": name,
                    "url": url,
                    "summary": summary,
                }
            )

    def extract_docket_name_url_from_link(self, link):
        url = link.attrib["href"]
        text = link.text_content().strip()
        parts = text.split("-", 1)
        name = parts[1]
        docket = parts[0].strip()
        docket = "" if "order" in docket.lower() else docket
        return docket, name, url

    def extract_date_summary_from_link(self, link):
        # Link should be within a <p> tag directly under <div id='maincontent'>, but
        # occasionally the courts forgets the wrap it in a <p>, in which case it should
        # be directly under the <div id='maincontent'>
        container_id = "maincontent"
        parent = link.getparent()
        parents_parent = parent.getparent()
        if "id" in parent.attrib and parent.attrib["id"] == container_id:
            search_root = link
        elif (
            "id" in parents_parent.attrib
            and parents_parent.attrib["id"] == container_id
        ):
            search_root = parent
        else:
            raise InsanityException(
                'Unrecognized placement of Opinion url on page: "%s"'
                % link.text_content().strip()
            )

        # Find date from bolded header element above link (ex: "5-14-2014 - Opinions" or "5-21-2014 - Orders")
        element_date = search_root.xpath("./preceding-sibling::b")[-1]
        element_date_text = element_date.text_content().strip().lower()
        try:
            date_string = element_date_text.split()[0]
        except:
            raise InsanityException(
                'Unrecognized bold (date) element: "%s"' % element_date_text
            )

        # Find summary from blockquote element below link
        element_blockquote = search_root.xpath(
            "./following-sibling::blockquote"
        )[0]
        summary = element_blockquote.text_content().strip()

        return convert_date_string(date_string), summary

    def _get_download_urls(self):
        return [case["url"] for case in self.cases]

    def _get_case_names(self):
        return [case["name"] for case in self.cases]

    def _get_case_dates(self):
        return [case["date"] for case in self.cases]

    def _get_docket_numbers(self):
        return [case["docket"] for case in self.cases]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.cases)

    def _get_summaries(self):
        return [case["summary"] for case in self.cases]
