
from datetime import datetime

from lxml import html

from juriscraper.lib.html_utils import fix_links_in_lxml_tree
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://supremecourt.nebraska.gov/courts/supreme-court/opinions"
        )

    def _fetch_duplicate(self, data):
        # Create query for duplication
        query_for_duplication = {"docket": data.get("docket"), "citation": data.get("citation")}
        # Find the document
        duplicate = self.judgements_collection.find_one(query_for_duplication)
        object_id = None
        if duplicate is None:
            # Insert the new document
            self.judgements_collection.insert_one(data)

            # Retrieve the document just inserted
            updated_data = self.judgements_collection.find_one(query_for_duplication)
            object_id = updated_data.get("_id")  # Get the ObjectId from the document
            self.flag = True
        else:
            # Check if the document already exists and has been processed
            processed = duplicate.get("processed")
            if processed == 10:
                raise Exception("Judgment already Exists!")  # Replace with your custom DuplicateRecordException
            else:
                object_id = duplicate.get("_id")  # Get the ObjectId from the existing document
        return object_id

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
                if "S-XX-XXXX" in docket or "A-XX-XXXX" in docket:
                    continue
                dockets = docket.split(', ')[::-1]
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
                        "docket": dockets,
                        "name": name,
                        "citation": [citation],
                        "url": url,
                        "status": status,
                    }
                )

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
         self.parse()
         return 0


    def get_court_type(self):
        return "state"

    def get_class_name(self):
        return "neb"

    def get_state_name(self):
        return "Nebraska"

    def get_court_name(self):
        return "Supreme Court of Nebraska"
