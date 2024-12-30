from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import fix_links_in_lxml_tree
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://supremecourt.nebraska.gov/courts/supreme-court/opinions"
        )

    def _return_response_text_object(self):
        """Remove faulty URLs from HTML

        Override _return_response_text_object in Abstract Site to remove any
        url to [site:url-brief] which causes lxml/ipaddress to explode.

        This bug only exists in 3.11 and 3.12

        <a href="https://[site:url-brief]/node/19063" ... >District Map</a>

        :return: The cleaned html tree of the site
        """
        if self.request["response"]:
            payload = self.request["response"].text
            text = self._clean_text(payload)
            html_tree = self._make_html_tree(text)

            for tag in html_tree.xpath(
                "//a[contains(@href, 'site:url-brief')]"
            ):
                parent = tag.getparent()
                if parent is not None:
                    parent.remove(tag)

            if hasattr(html_tree, "rewrite_links"):
                html_tree.rewrite_links(
                    fix_links_in_lxml_tree, base_href=self.request["url"]
                )
            return html_tree

    def _process_html(self):
        for table in self.html.xpath(".//table"):
            date_tags = table.xpath("preceding::time[1]/text()")
            if not date_tags:
                continue
            date = date_tags[0]

            for row in table.xpath(".//tr[td]"):
                c1, c2, c3 = row.xpath(".//td")
                docket = c1.xpath(".//text()")[0].strip()
                if "A-XX-XXXX" in docket or not c3.xpath(".//a"):
                    logger.info("Skip row %s", row.text_content())
                    continue

                citation = c2.xpath(".//text()")[0].strip()
                name = c3.xpath(".//a/text()")[0].strip()
                url = c3.xpath(".//a")[0].get("href")
                # This URL location is used for unpublished opinions
                if "/sites/default/files" in url:
                    status = "Unpublished"
                else:
                    status = "Published"

                self.cases.append(
                    {
                        "date": date,
                        "docket": docket,
                        "name": name,
                        "citation": citation,
                        "url": url,
                        "status": status,
                    }
                )
