from typing import Dict

from requests.exceptions import ChunkedEncodingError

from juriscraper.lib.html_utils import (
    get_row_column_links,
    get_row_column_text,
)
from juriscraper.NewOpinionSite import NewOpinionSite, logger


class Site(NewOpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://appellate-records.courts.alaska.gov/CMSPublic/Home/Opinions?isCOA=False"
        self.status = "Published"
        # juriscraper in the user agent crashes it
        # it appears to be just straight up blocked.
        self.request["headers"]["user-agent"] = "Free Law Project"

    def _download(self, request_dict={}):
        """
        Unfortunately, about 2/3 of calls are rejected by alaska but
        if we just ignore those encoding errors we can live with it
        """
        try:
            return super()._download(request_dict)
        except ChunkedEncodingError:
            return None

    def _process_html(self) -> None:
        """
        Have only seen combined opinions in this source
        See for example: S17910 - State of Alaska v. John William McKelvey III
        with opinion 7690 published on 3/8/2024. After the conclusion, it has a concurring opinion
        Case link:
        https://appellate-records.courts.alaska.gov/CMSPublic/Case/General?q=w6sobc/DATfJtIRGLf4mqQ==%27
        """
        if not self.html:
            logger.warning("Unable to load page from Alaska")
            return

        for table in self.html.xpath("//table"):
            date = table.xpath("./preceding-sibling::h5")[0].text_content()
            for row in table.xpath(".//tr"):
                if not row.text_content().strip():
                    continue
                case = {}

                # rows without PDF links in first column have the opinion
                # link inside the case page
                try:
                    url = get_row_column_links(row, 1)
                except IndexError:
                    url = self.placeholder_url
                    case["case_page_link"] = get_row_column_links(row, 3)

                # Have only seen combined opinions in this source
                case.update(
                    {
                        "oc.date_filed": date,
                        "d.docket_number": get_row_column_text(row, 3),
                        "d.case_name": get_row_column_text(row, 4),
                        "oc.citation_strings": [get_row_column_text(row, 5)],
                        "opinions": [{"download_url": url}],
                    }
                )
                self.cases.append(case)

    def get_deferred_download_url(self, case: Dict) -> bool:
        """ """
        # No need to go into case page, we already have the URL
        if not case.get("case_page_link"):
            return False

        link = case["case_page_link"]

        if self.test_mode_enabled():
            self.url = link
            self._request_url_mock(link)
            html = self._return_response_text_object()
        else:
            html = self._get_html_tree_by_url(link)

        nos, case["d.date_filed"] = html.xpath(
            "//dl[dt[text()='Case Type:']]/dd/text()"
        )
        case["oc.nature_of_suit"] = nos.split(" ", 1)[-1]

        # Parse opinion table
        opinion_row = html.xpath("//tr[td[@title='Document Download']]")[0]
        case["opinions"][0]["download_url"] = opinion_row.xpath("td/a/@href")[
            0
        ]
        case["oc.disposition"] = opinion_row.xpath("td[3]/text()")[0]

        # Parse lower court table
        oci_row = html.xpath(
            "//h5[text()='Lower Court or Agency Information']/following-sibling::table/tbody/tr"
        )
        if oci_row:
            oci_row = oci_row[0]
            oci = {
                "docket_number": oci_row.xpath("td[1]/text()")[0],
                "date_judgment": oci_row.xpath("td[2]/text()")[0],
                "assigned_to_str": oci_row.xpath("td[5]/text()")[0],
            }
            case["oci"] = oci
            case["d.appeal_from_str"] = oci_row.xpath("td[4]/text()")[0]

        return True
