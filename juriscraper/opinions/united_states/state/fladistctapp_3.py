"""
Scraper for Florida 3rd District Court of Appeal
CourtID: flaapp3
Court Short Name: flaapp3
Contact: 3dca@flcourts.org, Angel Falero <faleroa@flcourts.org> (305-229-6743)

History:
 - 2014-07-21: Written by Andrei Chelaru
 - 2014-07-24: Reviewed by mlr
 - 2015-07-28: Updated by m4h7
"""

from datetime import date

from juriscraper.lib.string_utils import titlecase, convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "http://www.3dca.flcourts.org/Opinions/ArchivedOpinions.shtml"
        )
        self.base_path = (
            "//h3/following::text()[.='OPINIONS']/following::table[1]//tr"
        )

    def _download(self, request_dict={}):
        html_l = super(Site, self)._download(request_dict)
        if self.test_mode_enabled():
            return [html_l]
        html_trees = []
        # this path reads the row for the last month in that year
        path_format = "//th[contains(., '{year}')]/following::tr[1]/td[position()>1]/a[contains(., '/')]/@href"
        path = path_format.format(year=date.today().year)
        for url in html_l.xpath(path):
            html_tree = self._get_html_tree_by_url(url, request_dict)
            html_trees.append(html_tree)
        return html_trees

    def _get_case_names(self):
        case_names = []  # return html_l
        for html_tree in self.html:
            case_names.extend(self._return_case_names(html_tree))
        return case_names

    def _return_case_names(self, html_tree):
        path = "%s/td[2]" % self.base_path
        cells = html_tree.xpath(path)
        names = [c.text_content().strip() for c in cells]

        # Return formatted text for non-empty cells
        return [titlecase(n.lower()) for n in names if n]

    def _get_download_urls(self):
        download_urls = []
        for html_tree in self.html:
            download_urls.extend(self._return_download_urls(html_tree))
        return download_urls

    def _return_download_urls(self, html_tree):
        path = "%s/td[1]//a/@href" % self.base_path
        return html_tree.xpath(path)

    def _get_case_dates(self):
        case_dates = []
        for html_tree in self.html:
            case_dates.extend(self._return_dates(html_tree))
        return case_dates

    def _return_dates(self, html_tree):
        path_date_string = "//h3/text()"
        text = html_tree.xpath(path_date_string)[0]
        date_string = text.split()[0]
        case_date = convert_date_string(date_string)

        # Count rows with non-empty first cells
        path_first_cell = "%s/td[1]" % self.base_path
        first_cells = html_tree.xpath(path_first_cell)
        opinion_count = sum(1 for r in first_cells if r.text_content().strip())

        return [case_date] * opinion_count

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_dates)

    def _get_docket_numbers(self):
        docket_numbers = []
        for html_tree in self.html:
            docket_numbers.extend(self._return_docket_numbers(html_tree))
        return docket_numbers

    def _return_docket_numbers(self, html_tree):
        path = "%s/td[1]//a" % self.base_path
        return [a.text_content().strip() for a in html_tree.xpath(path)]
