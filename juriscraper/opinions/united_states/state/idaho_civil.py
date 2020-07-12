# -*- coding: utf-8 -*-

"""
Contact: Sara Velasquez, svelasquez@idcourts.net, 208-947-7501
History:
 - 2014-08-05, mlr: Updated.
 - 2015-06-19, mlr: Updated to simply the XPath expressions and to fix an OB1
   problem that was causing an InsanityError. The cause was nasty HTML in their
   page.
 - 2015-10-20, mlr: Updated due to new page in use.
 - 2015-10-23, mlr: Updated to handle annoying situation.
 - 2016-02-25 arderyp: Updated to catch "ORDER" (in addition to "Order") in download url text
"""
import six
from lxml import html
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string, clean_if_py3


class Site(OpinionSite):
    # Skip first row of table, it's a header
    path_table_row_start = "//table//tr[position() > 1]"
    # Skip rows that don't have  link in 4th cell with
    # either 'Opinion', 'Order', 'ORDER', or 'Amend' in
    # the link text
    path_conditional_anchor = (
        "a["
        'contains(.//text(), "Opinion") or '
        'contains(.//text(), "Order") or '
        'contains(.//text(), "ORDER") or '
        'contains(.//text(), "Amended")'
        "]"
    )
    path_conditional_row = "/td[4]//%s" % path_conditional_anchor
    path_base = "%s[./%s]" % (path_table_row_start, path_conditional_row)

    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = "https://www.isc.idaho.gov/appeals-court/isc_civil"
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        path = "%s/td[3]" % self.path_base
        for cell in self.html.xpath(path):
            name_string = html.tostring(
                cell, method="text", encoding="unicode"
            )
            name_string = clean_if_py3(name_string).strip()
            if name_string:
                case_names.append(name_string)
        return case_names

    def _get_download_urls(self):
        # We'll accept an order document if the opinion document
        # is missing. But we obviously prefer the opinion doc,
        # as indicated in the algorithm below. Since each row
        # can list multiple valid links, we will parse all
        # acceptable links, take the opinion link if present,
        # otherwise take the first acceptable link.
        opinion_urls = []
        path = "%s/td[4]" % self.path_base
        path_link = ".//%s" % self.path_conditional_anchor
        for cell in self.html.xpath(path):
            urls = []
            url_opinion = False
            for link in cell.xpath(path_link):
                text = link.text_content().strip()
                url = link.attrib["href"]
                urls.append(url)
                if "Opinion" in text:
                    url_opinion = url
            opinion_urls.append(url_opinion if url_opinion else urls[0])
        return opinion_urls

    def _get_case_dates(self):
        case_dates = []
        path = "%s/td[1]" % self.path_base
        for cell in self.html.xpath(path):
            date_string = html.tostring(
                cell, method="text", encoding="unicode"
            )
            date_string = clean_if_py3(date_string).strip()
            if date_string:
                if six.PY2:
                    date_string = date_string.encode("ascii", "ignore")
                date_string = date_string.replace(
                    "Sept ", "Sep "
                )  # GIGO!  (+1 by arderyp)
                case_dates.append(convert_date_string(date_string))
        return case_dates

    def _get_docket_numbers(self):
        path = "%s/td[2]//text()" % self.path_base
        return [text.strip() for text in self.html.xpath(path) if text.strip()]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
