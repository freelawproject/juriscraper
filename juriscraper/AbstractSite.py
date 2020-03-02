import os
import hashlib
import json
from datetime import date, datetime
import warnings

import certifi
import requests
import six
from requests.adapters import HTTPAdapter

from juriscraper.lib.date_utils import fix_future_year_typo, json_date_handler
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.html_utils import (
    clean_html,
    fix_links_in_lxml_tree,
    get_html_parsed_text,
    get_html_from_element,
    set_response_encoding,
)
from juriscraper.lib.log_tools import make_default_logger
from juriscraper.lib.string_utils import (
    CaseNameTweaker,
    clean_string,
    harmonize,
    trunc,
)
from juriscraper.lib.test_utils import MockRequest

logger = make_default_logger()
phantomjs_executable_path = "/usr/local/bin/phantomjs"
_legacy_path = "/usr/local/phantomjs/phantomjs"
if os.path.isfile(_legacy_path) and os.access(_legacy_path, os.X_OK):
    phantomjs_executable_path = _legacy_path
    msg = """Please place phantomjs executable in /usr/local/bin.
    See https://github.com/freelawproject/juriscraper/pull/241"""
    warnings.warn(msg, DeprecationWarning)


class AbstractSite(object):
    """Contains generic methods for scraping data. Should be extended by all
    scrapers.

    Should not contain lists that can't be sorted by the _date_sort function."""

    def __init__(self, cnt=None):
        super(AbstractSite, self).__init__()

        # Computed metadata
        self.hash = None
        self.html = None
        self.method = "GET"
        self.back_scrape_iterable = None
        self.downloader_executed = False
        self.cookies = {}
        self.cnt = cnt or CaseNameTweaker()
        self.request = {
            "verify": certifi.where(),
            "session": requests.session(),
            "headers": {"User-Agent": "Juriscraper"},
            # Disable CDN caching on sites like SCOTUS (ahem)
            "cache-control": "no-cache, no-store, max-age=1",
            "parameters": {},
            "request": None,
            "status": None,
            "url": None,
        }

        # Sub-classed metadata
        self.court_id = None
        self.url = None
        self.parameters = None
        self.uses_selenium = None
        self._opt_attrs = []
        self._req_attrs = []
        self._all_attrs = []

    def __str__(self):
        out = []
        for attr, val in self.__dict__.items():
            out.append("%s: %s" % (attr, val))
        return "\n".join(out)

    def __iter__(self):
        for i in range(0, len(self.case_names)):
            yield self._make_item(i)

    def __getitem__(self, i):
        return self._make_item(i)

    def __len__(self):
        return len(self.case_names)

    def _make_item(self, i):
        """Using i, convert a single item into a dict. This is effectively a
        different view of the data.
        """
        item = {}
        for attr_name in self._all_attrs:
            attr_value = getattr(self, attr_name)
            if attr_value is not None:
                item[attr_name] = attr_value[i]
        return item

    def enable_test_mode(self):
        self.method = "LOCAL"

    def dump_html(self, element):
        """Use this dor debuging purposes"""
        print(get_html_from_element(element))

    def disable_certificate_verification(self):
        """Scrapers that require this due to website misconfiguration
        should be checked periodically--calls to this method from
         site scrapers should be removed when no longer necessary.
         """
        self.request["verify"] = False

    def test_mode_enabled(self):
        return self.method == "LOCAL"

    def to_json(self):
        return json.dumps([item for item in self], default=json_date_handler,)

    def parse(self):
        if not self.downloader_executed:
            # Run the downloader if it hasn't been run already
            self.html = self._download()

            # Process the available html (optional)
            self._process_html()

        # Set the attribute to the return value from _get_foo()
        # e.g., this does self.case_names = _get_case_names()
        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, "_get_%s" % attr)())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            # This needs to be done *after* _clean_attributes() has been run.
            # The current architecture means this gets run twice. Once when we
            # iterate over _all_attrs, and again here. It's pretty cheap though.
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return self

    def tweak_response_object(self):
        """
        Does nothing, but provides a hook that allows inheriting objects to
        tweak the requests object if necessary.
        """
        pass

    def _clean_text(self, text):
        """A hook for subclasses to override if needed."""
        return clean_html(text)

    def _clean_attributes(self):
        """Iterate over attribute values and clean them"""
        for attr in self._all_attrs:
            item = getattr(self, attr)
            if item is not None:
                cleaned_item = []
                for sub_item in item:
                    if attr == "download_urls":
                        sub_item = sub_item.strip()
                    else:
                        if isinstance(sub_item, six.string_types):
                            sub_item = clean_string(sub_item)
                        elif isinstance(sub_item, datetime):
                            sub_item = sub_item.date()
                        if attr in ["case_names", "docket_numbers"]:
                            sub_item = harmonize(sub_item)
                    cleaned_item.append(sub_item)
                self.__setattr__(attr, cleaned_item)

    def _post_parse(self):
        """This provides an hook for subclasses to do custom work on the data
        after the parsing is complete.
        """
        pass

    def _check_sanity(self):
        """Check that the objects attributes make sense:
            1. Do all the attributes have the same length?
            1. Do we have any content at all?
            1. Is there a bare minimum of meta data?
            1. Are the dates datetime objects, not strings?
            1. Are any dates from the 22nd century? (01-01-2104)
            1. Are case_names more than just empty whitespace?
            1. Has the `cookies` attribute been normalized to a dict?
            1. ?

        The signature of this method is subject to change as additional checks
        become convenient.

        Inheriting classes should override this method calling super to give it
        the necessary parameters.

        If sanity is OK, no return value. If not, throw InsanityException or
        warnings, as appropriate.
        """
        lengths = {}
        for attr in self._all_attrs:
            if self.__getattribute__(attr) is not None:
                lengths[attr] = len(self.__getattribute__(attr))
        values = list(lengths.values())
        if values.count(values[0]) != len(values):
            # Are all elements equal?
            raise InsanityException(
                "%s: Scraped meta data fields have differing"
                " lengths: %s" % (self.court_id, lengths)
            )
        if len(self.case_names) == 0:
            logger.warning("%s: Returned with zero items." % self.court_id)
        else:
            for field in self._req_attrs:
                if self.__getattribute__(field) is None:
                    raise InsanityException(
                        "%s: Required fields do not contain any data: %s"
                        % (self.court_id, field)
                    )
            i = 0
            prior_case_name = None
            for name in self.case_names:
                if not name.strip():
                    raise InsanityException(
                        "Item with index %s has an empty case name. The prior "
                        "item had case name of: %s" % (i, prior_case_name)
                    )
                prior_case_name = name
                i += 1

        for index, case_date in enumerate(self.case_dates):
            if not isinstance(case_date, date):
                raise InsanityException(
                    "%s: member of case_dates list not a valid date object. "
                    "Instead it is: %s with value: %s"
                    % (self.court_id, type(case_date), case_date)
                )
            # Sanitize case date, fix typo of current year if present
            fixed_date = fix_future_year_typo(case_date)
            if fixed_date != case_date:
                logger.info(
                    "Date year typo detected. Converting %s to %s "
                    "for case '%s' in %s"
                    % (
                        case_date,
                        fixed_date,
                        self.case_names[index],
                        self.court_id,
                    )
                )
                case_date = fixed_date
                self.case_dates[index] = fixed_date
            if case_date.year > 2025:
                raise InsanityException(
                    "%s: member of case_dates list is from way in the future, "
                    "with value %s" % (self.court_id, case_date.year)
                )

        # Is cookies a dict?
        if type(self.cookies) != dict:
            raise InsanityException(
                "self.cookies not set to be a dict by " "scraper."
            )
        logger.info(
            "%s: Successfully found %s items."
            % (self.court_id, len(self.case_names))
        )

    def _date_sort(self):
        """ Sort the object by date.
        """
        if len(self.case_names) > 0:
            obj_list_attrs = [
                self.__getattribute__(attr)
                for attr in self._all_attrs
                if isinstance(self.__getattribute__(attr), list)
            ]
            zipped = list(zip(*obj_list_attrs))
            zipped.sort(reverse=True)
            i = 0
            obj_list_attrs = list(zip(*zipped))
            for attr in self._all_attrs:
                if isinstance(self.__getattribute__(attr), list):
                    self.__setattr__(attr, obj_list_attrs[i][:])
                    i += 1

    def _make_hash(self):
        """Make a unique ID. ETag and Last-Modified from courts cannot be
        trusted
        """
        self.hash = hashlib.sha1(str(self.case_names).encode()).hexdigest()

    def _get_adapter_instance(self):
        """Hook for returning a custom HTTPAdapter

        This function allows subclasses to do things like explicitly set
        specific SSL configurations when being called. Certain courts don't work
        unless you specify older versions of SSL.
        """
        return HTTPAdapter()

    def _make_html_tree(self, text):
        """Hook for custom HTML parsers

        By default, the etree.html parser is used, but this allows support for
        other parsers like the html5parser or even BeautifulSoup, if it's called
        for (example: return get_html5_parsed_text(text)). Otherwise, this method
        can be overwritten to execute custom parsing logic.
        """
        return get_html_parsed_text(text)

    def _download(self, request_dict={}):
        """Download the latest version of Site"""
        self.downloader_executed = True
        if self.method == "POST":
            truncated_params = {}
            for k, v in self.parameters.items():
                truncated_params[k] = trunc(v, 50, ellipsis="...[truncated]")
            logger.info(
                "Now downloading case page at: %s (params: %s)"
                % (self.url, truncated_params)
            )
        else:
            logger.info("Now downloading case page at: %s" % self.url)
        self._process_request_parameters(request_dict)
        if self.method == "GET":
            self._request_url_get(self.url)
        elif self.method == "POST":
            self._request_url_post(self.url)
        elif self.test_mode_enabled():
            self._request_url_mock(self.url)
        self._post_process_response()
        return self._return_response_text_object()

    def _process_html(self):
        """Hook for processing available self.html after it's been downloaded.
        This step is completely optional, but is useful if you want to transform
        the html before running the data getters (_get_*), or if its easier to
        extract the cases form the html in a linear function (here) as opposed
        to using separate data getters.  See sc.py for example.
        """
        pass

    def _process_request_parameters(self, parameters={}):
        """Hook for processing injected parameter overrides"""
        if parameters.get("verify") is not None:
            self.request["verify"] = parameters["verify"]
            del parameters["verify"]
        self.request["parameters"] = parameters
        self.request["session"].mount("https://", self._get_adapter_instance())

    def _request_url_get(self, url):
        """Execute GET request and assign appropriate request dictionary
        values
        """
        self.request["url"] = url
        self.request["response"] = self.request["session"].get(
            url,
            headers=self.request["headers"],
            verify=self.request["verify"],
            timeout=60,
            **self.request["parameters"]
        )

    def _request_url_post(self, url):
        """Execute POST request and assign appropriate request dictionary values"""
        self.request["url"] = url
        self.request["response"] = self.request["session"].post(
            url,
            headers=self.request["headers"],
            verify=self.request["verify"],
            data=self.parameters,
            timeout=60,
            **self.request["parameters"]
        )

    def _request_url_mock(self, url):
        """Execute mock request, used for testing"""
        self.request["url"] = url
        self.request["response"] = MockRequest(url=self.url).get()

    def _post_process_response(self):
        """Cleanup to response object"""
        self.tweak_response_object()
        self.request["response"].raise_for_status()
        set_response_encoding(self.request["response"])

    def _return_response_text_object(self):
        if self.request["response"]:
            if "json" in self.request["response"].headers.get(
                "content-type", ""
            ):
                return self.request["response"].json()
            else:
                if six.PY2:
                    payload = self.request["response"].text
                else:
                    payload = str(self.request["response"].content)

                text = self._clean_text(payload)
                html_tree = self._make_html_tree(text)
                html_tree.rewrite_links(
                    fix_links_in_lxml_tree, base_href=self.request["url"]
                )
                return html_tree

    def _get_html_tree_by_url(self, url, parameters={}):
        self._process_request_parameters(parameters)
        self._request_url_get(url)
        self._post_process_response()
        tree = self._return_response_text_object()
        tree.make_links_absolute(url)
        return tree

    def _download_backwards(self):
        # methods for downloading the entire Site
        pass

    @staticmethod
    def cleanup_content(content):
        """
          Given the HTML from a page, the binary PDF file, or similar, do any
          last-minute cleaning.

          This method should be called as the last step by any caller and works
          to do any cleanup that is necessary. Usually, this is needed on HTML
          pages, in jurisdictions that post their content in an HTML page with
          headers, footers and other content must be stripped after the page
          has been downloaded by the caller.
        """
        return content

    def _get_cookies(self):
        """
          Some websites require cookies in order to be scraped. This method
          provides a hook where cookies can be retrieved by calling functions.
          Generally the cookies will be set by the _download() method.

          self.cookies is a list of dicts of the form:
          [
              {
                  u'domain':   u'www.search.txcourts.gov',
                  u'httponly': True,
                  u'name':     u'ASP.NET_SessionId',
                  u'path':     u'/',
                  u'secure':   False,
                  u'value':    u'hryku05534xhgr45yxvusuux'
              },
          ]
        """
        return self._cookies

    def _get_case_name_shorts(self):
        """Generates short case names for all the case names that we scrape."""
        case_name_shorts = []
        for case_name in self.case_names:
            case_name_shorts.append(self.cnt.make_case_name_short(case_name))
        return case_name_shorts

    def _get_blocked_statuses(self):
        """Should these items be blocked by search engines? Default is False for
        all subclasses, indicating that the items should not be blocked.

        This method is important because some courts (like family or asylum
        courts) should choose privacy over openness. Note that we consider
        these functions to be a hint to callers, so following these guidelines
        is not guaranteed.
        """
        return [False] * len(self.case_names)
