from datetime import date, datetime, timedelta

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.courts.state.va.us/scndex.htm"
        self.status = "Published"
        self.should_have_results = True

    def _process_html(self) -> None:
        """Parses the HTML content to extract case information.

        :return: None
        """
        if self.test_mode_enabled():
            today = datetime.strptime("11/20/2023", "%m/%d/%Y").date()
        else:
            today = date.today()

        for row in self.html.xpath("//p"):
            links = row.xpath(".//a")
            if len(links) != 2:
                continue
            name = row.xpath(".//b/text()")[0].strip()

            text = row.text_content().split(name)[1].strip()
            split_test = text.split("\n")

            date_str = split_test[0].strip()
            summary = split_test[1].strip()

            if "Revised" in date_str:
                date_str = date_str.split("Revised")[1].strip().strip(")")
            date_object = datetime.strptime(date_str, "%m/%d/%Y").date()
            if date_object < today - timedelta(days=60):
                # Stop after two months
                break

            self.cases.append(
                {
                    "name": row.xpath(".//b/text()")[0].strip(),
                    "docket": links[1].text.strip(" '\""),
                    "url": links[1].get("href"),
                    "summary": summary,
                    "date": date_str,
                }
            )
