"""
CourtID: illappct
Court Short Name: Ill. App. Ct.
Author: Rebecca Fordon
Reviewer: Mike Lissner
History:
* 2016-06-23: Created by Rebecca Fordon
* 2022-05-18: Updated by William E. Palin
"""
from datetime import timedelta

from dateutil.utils import today

from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.illinoiscourts.gov/courts/appellate-court/oral-argument-audio/"
        self.method = "POST"
        self.today = today().strftime("%m/%d/%Y")
        self.earlier = (today() - timedelta(days=30)).strftime("%m/%d/%Y")
        self.district = "1st"
        self._set_parameters()

    def _set_parameters(self):
        self.parameters = {
            "__EVENTTARGET": "ctl00$ctl04$ddlFilterDistrict",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATEGENERATOR": "66677877",
            "ctl00$header$search$txtSearch": "",
            "ctl00$ctl04$txtFilterName": "",
            "ctl00$ctl04$ddlFilterDate": "Custom Date Range",
            "ctl00$ctl04$txtFilterDateFrom": self.earlier,
            "ctl00$ctl04$txtFilterDateTo": self.today,
            "ctl00$ctl04$ddlFilterDistrict": self.district,
            "ctl00$ctl04$hdnSortField": "ArgumentDate",
            "ctl00$ctl04$hdnSortDirection": "DESC",
        }

    def _process_html(self):
        for row in self.html.xpath('.//table[@id="ctl04_gvArguments"]/tr')[2:]:
            url = row.xpath(".//a/@data-audio")[0].replace(" ", "%20")
            date, district, docket, name, *others = row.xpath(".//span/text()")
            if others:
                docket, name = name, others[0]
            self.cases.append(
                {
                    "date": date,
                    "docket": docket,
                    "name": name,
                    "district": district,
                    "url": url,
                }
            )
