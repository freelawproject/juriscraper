from datetime import datetime
from urllib.parse import quote


# from juriscraper.OpinionSite import OpinionSite
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://www.utcourts.gov/opinions/supopin/index.php"
        self.base_url = "http://www.utcourts.gov/opinions/supopin/"
        self.court_id = self.__module__
        self.status= "Published"

    def _process_html(self):
        for row in self.html.xpath("/html/body//div[@class='w-75 pb-4']/p"):
            docket , date , citation= None, None, None
            name=row.xpath("./a/text()")[0]
            if name == "Back to Appellate Court Opinions":
                continue
            text = row.xpath("./text()")[0]
            parts = text.strip().split(", ")
            if parts[0] != "":
                name=parts[0]
                docket = parts[1][-8:]
                date = f"{parts[2]}, {parts[3]}"
                citation = parts[4]
            else:
                docket=parts[1][-8:]
                date= f"{parts[2]}, {parts[3]}"
                citation=parts[4]

            url = row.xpath(".//a/@href")[0]
            pdf_url = quote(url, safe="/:")
            dt = datetime.strptime(date, "Filed %B %d, %Y")

            self.cases.append(
                {
                    "date": str(dt),
                    "name": name,
                    "docket": [docket],
                    "citation": [citation],
                    "url": pdf_url,
                }
            )

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        if not self.downloader_executed:
            self.html = self._download()
            self._process_html()

        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return len(self.cases)

    def get_court_type(self):
        return "state"

    def get_class_name(self):
        return "utah"

    def get_state_name(self):
        return "Utah"

    def get_court_name(self):
        return "Supreme Court of Utah"
