"""Scraper for Colorado Appeals Court
CourtID: coloctapp
Court Short Name: Colo. Ct. App.
"""

from juriscraper.opinions.united_states.state import colo


class Site(colo.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.cobar.org/For-Members/Opinions-Rules-Statutes/Colorado-Court-of-Appeals-Opinions"
        self.base_path = "//div[@id='dnn_ctr2514_ModuleContent']/ul/li/a"
        self.next_subpage_path = "//a[@id='dnn_ctr2517_DNNArticle_List_MyArticleList_MyPageNav_cmdNext']"
