# Scraper for Kansas Supreme Court (published)
# CourtID: kan_p

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.kscourts.org/Cases-Decisions/Decisions"
        self.request["verify"] = False
        self.status = "Published"
        self.court = "Supreme Court"

    def _update_parameters(self):
        """"""
        view_state = self.html.xpath("//input[@id='__VIEWSTATE']")[0].get(
            "value"
        )
        VIEWSTATEGENERATOR = self.html.xpath(
            "//input[@id='__VIEWSTATEGENERATOR']"
        )[0].get("value")
        CMSCsrfToken = self.html.xpath("//input[@id='__CMSCsrfToken']")[0].get(
            "value"
        )
        data = {
            "__CMSCsrfToken": CMSCsrfToken,
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "lng": "en-US",
            "__VIEWSTATEGENERATOR": VIEWSTATEGENERATOR,
            "__SCROLLPOSITIONX": "0",
            "__SCROLLPOSITIONY": "239",
            "p$lt$ctl01$SmartSearchBox3$txtWord_exWatermark_ClientState": "",
            "p$lt$ctl01$SmartSearchBox3$txtWord": "",
            "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl02$OpinionFilter1$filterControl$txtSearch": "",
            "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl02$OpinionFilter1$filterControl$drpPublished": self.status,
            "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl02$OpinionFilter1$filterControl$drpCourt": self.court,
            "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl02$OpinionFilter1$filterControl$drpSortBy": "Sort By",
            "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl02$OpinionFilter1$filterControl$btnFilter": "Apply Filters",
            "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl03$AccordionLayout1$acc_AccordionExtender_ClientState": "-1",
            "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl07$AccordionLayout$acc_AccordionExtender_ClientState": "-1",
            "p$lt$ctl09$SmartSearchBox1$txtWord_exWatermark_ClientState": "",
            "p$lt$ctl09$SmartSearchBox1$txtWord": "",
            "__VIEWSTATE": view_state,
        }
        self.parameters = data
        self.method = "POST"
        self.request["verify"] = False

    def _process_html(self):
        self.method = "POST"
        if not self.test_mode_enabled():
            if (
                self.url
                == "https://www.kscourts.org/Cases-Decisions/Decisions"
            ):
                self._update_parameters()
                self.html = super()._download()
        for row in self.html.xpath(".//tr"):
            date_filed, docket_number, case_name, court, status = row.xpath(
                ".//td/a/text()"
            )
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
