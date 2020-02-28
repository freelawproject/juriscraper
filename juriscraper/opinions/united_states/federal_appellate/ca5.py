# History:
# - Long ago: Created by mlr
# - 2014-11-07: Updated by mlr to use new website.

from datetime import datetime

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = "http://www.ca5.uscourts.gov/rss.aspx?Feed=Opinions&Which=All&Style=Detail"
        self.court_id = self.__module__

    def _get_case_names(self):
        path = "//item/description/text()[2]"
        return [s for s in self.html.xpath(path)]

    def _get_download_urls(self):
        path = "//item/link"
        return [e.tail for e in self.html.xpath(path)]

    def _get_case_dates(self):
        path = "//item/description/text()[5]"
        return [
            datetime.strptime(date_string, "%m/%d/%Y").date()
            for date_string in self.html.xpath(path)
        ]

    def _get_docket_numbers(self):
        path = "//item/description/text()[1]"
        return [s for s in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        path = "//item/description/text()[3]"
        statuses = []
        for status in self.html.xpath(path):
            if status == "pub":
                statuses.append("Published")
            elif status == "unpub":
                statuses.append("Unpublished")
            else:
                statuses.append("Unknown")
        return statuses

    def _get_nature_of_suit(self):
        path = "//item/description/text()[4]"
        return [s for s in self.html.xpath(path)]
