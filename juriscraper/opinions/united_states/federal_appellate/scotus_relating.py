from juriscraper.opinions.united_states.federal_appellate import (
    scotus_slip,
)


class Site(scotus_slip.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.precedential = "Relating-to"
        self.court = "relatingtoorders"

    @staticmethod
    def get_fields(cells, row):
        if len(cells) != 5:
            return None
        date, docket, link, justice, citation = row.xpath(".//td")
        return date, docket, link, None, justice, citation
