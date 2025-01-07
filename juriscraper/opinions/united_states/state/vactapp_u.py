from datetime import datetime

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.vacourts.gov/wpcau.htm"
        self.status = "Unpublished"
        self.from_date = None

    def _process_html(self):
        target_date = self.from_date.date()
        for row in self.html.xpath("//p"):
            links = row.xpath(".//a")
            name = row.xpath(".//b/text()")
            if not name:
                continue
            date, disposition, *_ = row.text_content().splitlines()
            date = date.split(name[0])[1]
            date_object = datetime.strptime(date.strip(), "%m/%d/%Y").date()
            if date_object < target_date:
                break
            self.cases.append(
                {
                    "name": name[0].strip(),
                    "docket": [links[0].get("href").split("/")[-1][:-4]],
                    "url": links[0].get("href"),
                    "disposition": disposition,
                    "date": date.strip(),
                }
            )

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.from_date=start_date
        self.parse()
        return 0

    def get_court_type(self):
        return "state"

    def get_court_name(self):
        return "Virginia Court of Appeals"

    def get_state_name(self):
        return "Virginia"

    def get_class_name(self):
        return "vactapp_u"
