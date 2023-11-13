from juriscraper.opinions.united_states.state import mo


class Site(mo.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court = "Southern"
        self.url = self.build_url()

    def _download(self, request_dict={}):
        # I have to do something to open up the page - but only for the southern
        # district of this verison of the court.
        if not self.test_mode_enabled():
            data = '{"sort_date_facets_by_value":true,"content_sample_length":300,"name":"default","path":"search","paging_states":[],"query_context":{"query_id":"1699132997921","prev_query_id":"1699132997873"},"user_context":{"referer":"https://www.courts.mo.gov/page.jsp?id=12086&dist=Opinions%20Southern&date=all&year=2023#all","locale":"en","service_id":"https://www.courts.mo.gov/search/apps/scripts/../../api/v2/","utc_time_zone_differential_in_seconds":-14400,"service_url":"https://www.courts.mo.gov/search/apps/scripts/../../api/v2/search"}}'
            self.request["session"].post(
                "https://www.courts.mo.gov/search/api/v2/search", data=data
            )
            self.method = "GET"
            self.request["session"].get(self.url)
        return super()._download(request_dict)

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
                        "dispostion": vote.split(".")[0].strip(),
                        "judge": author,
                        "judges": vote.split(".", 1)[1].strip(),
                    }
                )
