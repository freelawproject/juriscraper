from lxml import html
from juriscraper.OpinionSite import OpinionSite


class OpinionSiteAspx(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(OpinionSiteAspx, self).__init__(*args, **kwargs)
        self.spoof_user_agent = False

    def _get_soup(self, url):
        """Download a page of the site. Can be called multiple times.

        Either the first page of the site with GET, if self.data is empty, or
        a subsequent page with POST, if it is filled.
        """
        if self.spoof_user_agent:
            self.request["headers"] = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36",
            }

        if not self.data:
            r = self.request["session"].get(url)
        else:
            r = self.request["session"].post(url, data=self.data)
        self.soup = html.fromstring(r.text)

    def _get_data_template(self):
        """Returns a template for data that should be POSTed to an ASPX page.

        This can include any number of key/values that are the same between
        pages. It can also contain the special keys __VIEWSTATE and __EVENTTARGET
        whose values are ignored and set to the appropriate value in the
        _update_data method.
        """
        raise NotImplementedError(
            "`_get_data_template()` must be implemented."
        )

    def _get_event_target(self):
        raise NotImplementedError(
            "`_get_event_target()` must be implemented if the __EVENTTARGET key is present in the "
            "template data."
        )

    def _update_data(self):
        """Create a new copy of self.data from self.data_tmpl.

        Fill it in with standard ASPX parameters.
        """
        self.data = self._get_data_template()
        self._update_aspx_params()

    def _update_aspx_params(self):
        """Update the standard ASPX parameters in the self.data dictionary.

        To be useful, this method requires that a page has already been
        downloaded, in order to extract the values. This means that self.soup
        should be populated.
        """
        if self.soup is None:
            return

        if "__VIEWSTATE" in self.data:
            self.data["__VIEWSTATE"] = self.soup.xpath(
                '//*[@id="__VIEWSTATE"]/@value'
            )[0]

        if "__EVENTTARGET" in self.data:
            self.data["__EVENTTARGET"] = self._get_event_target()

        if "__EVENTVALIDATION" in self.data:
            self.data["__EVENTVALIDATION"] = self.soup.xpath(
                '//*[@id="__EVENTVALIDATION"]/@value'
            )[0]
