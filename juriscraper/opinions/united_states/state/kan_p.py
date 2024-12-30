# Scraper for Kansas Supreme Court (published)
# CourtID: kan_p

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_filter = "Supreme Court"
    status_filter = "Published"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.kscourts.gov/Cases-Decisions/Decisions"
        self.request["verify"] = False
        self.request["headers"].update(
            {
                "Referer": "https://kscourts.gov/Cases-Decisions/Decisions",
                "Host": "kscourts.gov",
                "Origin": "https://kscourts.gov",
            }
        )

    def _process_html(self):
        if not self.test_mode_enabled():
            # Loading from a fresh session causes an error page
            self.html = self._download()
            self._update_parameters()
            self.html = self._download()

        for row in self.html.xpath(".//tr"):
            date_filed, docket_number, case_name, court, status = row.xpath(
                ".//td/a/text()"
            )
            if court != self.court_filter or status != self.status_filter:
                # Check for bug seen on #1222
                logger.error(
                    "Filters are not working, we got an opinion from %s", court
                )
                continue

            url = row.xpath(".//td/a")[0].get("href")
            self.cases.append(
                {
                    "status": status,
                    "date": date_filed,
                    "docket": docket_number,
                    "name": case_name,
                    "url": url,
                }
            )

    def _update_parameters(self):
        """Apply filters through a form data POST request"""
        self.method = "POST"
        view_state = self.html.xpath("//input[@id='__VIEWSTATE']")[0].get(
            "value"
        )
        view_state_generator = self.html.xpath(
            "//input[@id='__VIEWSTATEGENERATOR']"
        )[0].get("value")
        cms_csrf_token = self.html.xpath("//input[@id='__CMSCsrfToken']")[
            0
        ].get("value")
        self.parameters = {
            "__CMSCsrfToken": cms_csrf_token,
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "lng": "en-US",
            "__VIEWSTATEGENERATOR": view_state_generator,
            "__SCROLLPOSITIONX": "0",
            "__SCROLLPOSITIONY": "0",
            "p$lt$ctl01$SmartSearchBox3$txtWord_exWatermark_ClientState": "",
            "p$lt$ctl01$SmartSearchBox3$txtWord": "",
            "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl02$OpinionFilter1$filterControl$txtSearch": "",
            "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl02$OpinionFilter1$filterControl$drpPublished": self.status_filter,
            "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl02$OpinionFilter1$filterControl$drpCourt": self.court_filter,
            "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl02$OpinionFilter1$filterControl$drpSortBy": "Sort By",
            "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl02$OpinionFilter1$filterControl$btnFilter": "Apply Filters",
            "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl03$AccordionLayout1$acc_AccordionExtender_ClientState": "-1",
            "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl07$AccordionLayout$acc_AccordionExtender_ClientState": "-1",
            "p$lt$ctl09$SmartSearchBox1$txtWord_exWatermark_ClientState": "",
            "p$lt$ctl09$SmartSearchBox1$txtWord": "",
            "__VIEWSTATE": view_state,
        }
