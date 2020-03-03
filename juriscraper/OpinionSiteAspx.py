from lxml import html
from juriscraper.OpinionSite import OpinionSite


class OpinionSiteAspx(OpinionSite):
    def _get_soup(self, url):
        """Download a page of the site. Can be called multiple times.

        Either the first page of the site with GET, if self.data is empty, or
        a subsequent page with POST, if it is filled.
        """
        if not self.data:
            r = self.request["session"].get(url)
        else:
            r = self.request["session"].post(url, data=self.data)
        self.soup = html.fromstring(r.text)

    def _update_data(self):
        """Create a new copy of self.data from self.data_tmpl.

        Fill it in with standard ASPX parameters.
        """
        self.data = dict(self.data_tmpl)
        self._update_aspx_params()

    def _update_aspx_params(self):
        """Update the standard ASPX parameters in the self.data dictionary.

        To be useful, this method requires that a page has already been
        downloaded, in order to extract the values. This means that self.soup
        should be populated.
        """
        if "__VIEWSTATE" in self.data and self.soup is not None:
            self.data["__VIEWSTATE"] = self.soup.xpath(
                '//*[@id="__VIEWSTATE"]/@value'
            )[0]

        if "__EVENTTARGET" in self.data and self.soup is not None:
            self.data["__EVENTTARGET"] = self._get_event_target()
