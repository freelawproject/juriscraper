# Scraper for US Coast Guard Court of Criminal Appeals

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite
from re import IGNORECASE
from re import search
from requests.utils import requote_uri


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.mj_cite_regex = r"\d+ *M\.?J\.? *\d+"
        self.wl_cite_regex = r"\d+ *W\.?L\.? *\d+"
        self.current_page = 1
        self.base_url = (
            "https://www.uscg.mil/Resources/Legal/"
            "Court-of-Criminal-Appeals/"
            "CGCCA-Opinions/smdpage15701/{}"
        )
        special_words = (
            "ORDER|JUDGE ORDER|OPINION|PER "
            "CURIAM|RECONSIDERATION|WRIT|EXT WRIT|WRIT ORDER "
        )
        look_behind = r"".join(
            [rf"(?<!{word})" for word in special_words.split("|")]
        )
        self.names_regex = (
            rf"((([a-z][.a-z-]*){look_behind} +)+"
            rf"v\.?( +(?!{special_words})[a-z][.a-z-]+)+)"
            rf"|(in re( +(?!{special_words})[a-z][.a-z-]*)+)"
        )
        self._format_url()

    def _format_url(self):
        self.url = self.base_url.format(self.current_page)

    def _process_html(self):
        table_xpath = "//table[@class='Dashboard']//tbody[1]"
        self.html = self.html.xpath(table_xpath)[0]

    def _get_case_dates(self):
        dates_xpath = "//tr//td[3]"
        return [
            convert_date_string(date.text_content())
            for date in self.html.xpath(dates_xpath)
        ]

    def _get_case_names(self):
        names_xpath = "//tr//td[1]"
        # Matches 'party name' v (or V) 'party name' or "in re 'name'"
        # Handles multiple whitespaces and excludes any special words not
        # appropriately delimited. Ex:'ORDER IN RE C. P-B PETITION 78 M.J. 824'
        names = []
        for name in self.html.xpath(names_xpath):
            text = name.text_content()
            m = search(self.names_regex, text, flags=IGNORECASE)
            names.append(m.group(0) if m else "Unknown")
        return names

    def _get_case_name_shorts(self):
        # Since these names are not auto-shortened and per guidance,
        # this will return the full casename to populate the field.
        return self._get_case_names()

    def _get_precedential_statuses(self):
        title_xpath = "//tr//td[1]"
        opinion_regex = r".+opinion.+"
        unknown_regex = r".+order.+"
        statuses = []
        # If a case has a MJ citation, it is published.
        # Cases with a MJ citation but are noted as opinions are unpublished.
        # Cases with a MJ citation but are noted as orders are unknown.
        for title in self.html.xpath(title_xpath):
            m = search(self.mj_cite_regex, title.text_content())
            text = title.text_content()
            if m:
                if search(opinion_regex, text, IGNORECASE):
                    statuses.append("Unpublished")
                    continue
                if search(unknown_regex, text, IGNORECASE):
                    statuses.append("Unknown")
                    continue
                statuses.append("Published")
            else:
                statuses.append("Unpublished")
        return statuses

    def _get_download_urls(self):
        # All of the case urls contain spaces,
        # encoding them to be a good citizen.
        url_xpath = "//tr//td[1]/a/@href"
        return [requote_uri(url) for url in self.html.xpath(url_xpath)]

    def _get_west_citations(self):
        return self._parse_citations(self.wl_cite_regex)

    def _get_neutral_citations(self):
        return self._parse_citations(self.mj_cite_regex)

    def _parse_citations(self, regex):
        title_xpath = "//tr//td[1]"
        cite_list = []
        for title in self.html.xpath(title_xpath):
            m = search(regex, title.text_content())
            cite_list.append(m.group(0) if m else None)
        return cite_list
