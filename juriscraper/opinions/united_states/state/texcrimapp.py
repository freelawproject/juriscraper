# Scraper for Texas Criminal Court of Appeals
# CourtID: texcrimapp
# Court Short Name: TX
# Author: Michael Lissner
# Reviewer: None
# Date: 2015-09-02


from juriscraper.opinions.united_states.state import tex


class Site(tex.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_name = "ccrimapp"
        self.checkbox = 1

    def get_opinions(self, html):
        """
        Cluster with 3 opinions (texcrimapp)
        https://search.txcourts.gov/Case.aspx?cn=PD-0037-22&coa=coscca

        2 Opinions: main and concurring
        https://search.txcourts.gov/Case.aspx?cn=PD-0984-19&coa=coscca
        """
        opinions = []
        opinion_xpath = "//div[contains(text(), 'Case Events')]//tr[td[text()='OPINION ISSD')]]"
        for opinion in html.xpath(opinion_xpath):
            op = {}
            link_xpath = opinion.xpath(".//td//a/@href")
            if not link_xpath:
                continue

            op["download_url"] = link_xpath[0]
            op["disposition"] = opinion.xpath(".//td[3]/text()")[0]

            op_type = opinion.xpath(".//td//tr[a]/td[2]/text()")[0]
            if op_type == "Original":
                op["type"] = "010combined"
            elif op_type == "Dissenting":
                op_type["type"] = "040dissent"
            elif op_type == "Concurring":
                op_type["type"] = "030concurrence"

            opinions.append(op)

        return opinions
