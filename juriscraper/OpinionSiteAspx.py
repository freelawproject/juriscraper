from lxml import html
from juriscraper.OpinionSite import OpinionSite


class OpinionSiteAspx(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(OpinionSiteAspx, self).__init__(*args, **kwargs)
        self.spoof_user_agent = False

    def _update_html(self, url=None):
        """Download a page of the site and store the result in self.html.

        Can be called multiple times.

        Defaults to downloading self.url if no url is passed, or a custom url
        can be given.

        Either the first page of the site with GET, if self.data is empty, or
        a subsequent page with POST, if it is filled.
        """
        if url is None:
            url = self.url

        if self.spoof_user_agent:
            self.request["headers"] = {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 "
                    "Safari/537.36"
                ),
            }

        if self.method == "GET":
            r = self.request["session"].get(url)
        elif self.method == "POST":
            r = self.request["session"].post(url, data=self.data)
        self.html = html.fromstring(r.text)

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
        downloaded, in order to extract the values. This means that self.html
        should be populated.
        """
        assert (
            self.html is not None
        ), "self.html needs to be set before updating"

        if "__VIEWSTATE" in self.data:
            self.data["__VIEWSTATE"] = self.html.xpath(
                '//*[@id="__VIEWSTATE"]/@value'
            )[0]

        if "__EVENTTARGET" in self.data:
            self.data["__EVENTTARGET"] = self._get_event_target()

        if "__EVENTVALIDATION" in self.data:
            self.data["__EVENTVALIDATION"] = self.html.xpath(
                '//*[@id="__EVENTVALIDATION"]/@value'
            )[0]
