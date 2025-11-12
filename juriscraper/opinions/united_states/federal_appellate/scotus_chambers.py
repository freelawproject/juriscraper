from juriscraper.opinions.united_states.federal_appellate import (
    scotus_slip,
)


class Site(scotus_slip.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.precedential = "In-chambers"
        self.court = "in-chambers"

    @staticmethod
    def get_fields(cells, row):
        if len(cells) != 7:
            return None
        _, date, docket, link, revised, justice, citation = row.xpath(".//td")

        return date, docket, link, revised, justice, citation
