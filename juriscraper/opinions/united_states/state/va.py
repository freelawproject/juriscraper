from datetime import date, datetime, timedelta

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.courts.state.va.us/scndex.htm"
        self.status = "Published"
        self.from_date = None

    def _process_html(self):
        # if self.test_mode_enabled():
        #     today = datetime.strptime("11/20/2023", "%m/%d/%Y").date()
        # else:
        #     today = date.today()
        target_date=self.from_date.date()
        for row in self.html.xpath("//p"):
            links = row.xpath(".//a")
            if len(links) != 2:
                continue
            name = row.xpath(".//b/text()")[0].strip()
            summary = row.text_content().split(name)[1].strip()
            date_str = summary.split("\n")[0].strip()
            if "Revised" in date_str:
                date_str = date_str.split("Revised")[1].strip().strip(")")
            date_object = datetime.strptime(date_str, "%m/%d/%Y").date()
            if date_object < target_date:
                # Stop after two months
                break

            self.cases.append(
                {
                    "name": row.xpath(".//b/text()")[0].strip(),
                    "docket": [links[1].text],
                    "url": links[1].get("href"),
                    "summary": summary,
                    "date": date_str,
                }
            )

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.from_date = start_date
        self.parse()
        return 0

    def get_court_type(self):
        return "state"

    def get_court_name(self):
        return "Supreme Court of Virginia"

    def get_state_name(self):
        return "Virginia"

    def get_class_name(self):
        return "va"

