"""Scraper for Maryland Supreme Court Oral Argument Audio

This scraper has an interesting history. It was briefly running on the live
site, but we realized shortly after starting it that the scraper was
downloading video, not audio!

Seeing that we weren't ready for video, we disabled this scraper and deleted
any traces of it on the server.

One interesting lesson though was that the OA system didn't crumble or budge
when this was running. The video converted to mp3 just fine (each item took a
few hours) and we began hosting it like nothing was different. Go figure.

Your humble editor,

Mike


CourtID: md
Court Short Name: Md.
"""

from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.courts.state.md.us/coappeals/webcasts/webcastarchive.html"

    def _process_html(self):
        # Find rows that contain valid, non-"Bar Admissions", link
        path = (
            "//tr[.//td[2]//a/@href][not(contains(.//@href, 'baradmission'))]"
        )
        rows = self.html.xpath(path)

        for row in rows:
            cell_two = row.xpath("./td[2]")[0]
            self.cases.append(
                {
                    "date": row.xpath("./td[1]")[0].text_content(),
                    "name": row.xpath("./td[3]/*[self::b or self::strong]")[
                        0
                    ].text_content(),  # sometimes they use <b> tag, other times <strong> tag
                    "docket": cell_two.text_content(),
                    "url": cell_two.xpath(".//a/@href")[0],
                }
            )
