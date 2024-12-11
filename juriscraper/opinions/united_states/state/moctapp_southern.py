from juriscraper.opinions.united_states.state import mo


class Site(mo.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court = "Southern"
        self.url = self.build_url()

    def _process_html(self):
        for row in self.html.xpath("//div[@class='margin-bottom-15']"):
            date = row.xpath(".//input")[0].value
            for opinion in row.xpath(".//div[@class='list-group-item-text']"):
                url = opinion.xpath("a")[0].get("href")
                all_text = opinion.xpath(".//text()")
                case_metadata = [t.strip() for t in all_text if t.strip()]
                if len(case_metadata) != 6:
                    continue
                docket, name, _, author, _, vote = case_metadata
                self.cases.append(
                    {
                        "name": name,
                        "docket": docket[:-1],
                        "url": url,
                        "date": date,
                        "disposition": vote.split(".")[0].strip(),
                        "author": author,
                        "judge": vote.split(".", 1)[1].strip(),
                    }
                )
