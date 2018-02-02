# coding=utf-8
import re

from juriscraper.lib.utils import previous_and_next
from .docket_report import DocketReport
from .utils import clean_pacer_object, get_nonce_from_form
from ..lib.judge_parsers import normalize_judge_string
from ..lib.log_tools import make_default_logger
from ..lib.string_utils import force_unicode, harmonize, \
    clean_string

logger = make_default_logger()

date_regex = r'[—\d\-–/]*'


class DocketHistoryReport(DocketReport):
    assigned_to_regex = re.compile(r'(.*),\s+presiding', flags=re.IGNORECASE)
    referred_to_regex = re.compile(r'(.*),\s+referral', flags=re.IGNORECASE)

    PATH = 'cgi-bin/HistDocQry.pl'

    def __init__(self, court_id, pacer_session=None):
        super(DocketHistoryReport, self).__init__(court_id, pacer_session)

        if self.court_id.endswith('b'):
            self.is_bankruptcy = True
        else:
            self.is_bankruptcy = False

    @property
    def data(self):
        """Get all the data back from this endpoint."""
        data = self.metadata.copy()
        #data[u'docket_entries'] = self.docket_entries
        return data

    @property
    def metadata(self):
        self._set_metadata_values()
        data = {
            u'court_id': self.court_id,
            u'docket_number': self._get_docket_number(),
            u'case_name': self._get_case_name(),
            u'date_filed': self._get_value(self.date_filed_regex,
                                           cast_to_date=True),
            u'date_terminated': self._get_value(self.date_terminated_regex,
                                                cast_to_date=True),
            u'date_discharged': self._get_value(self.date_discharged_regex,
                                                cast_to_date=True),
            u'assigned_to_str': self._get_assigned_judge(),
            u'referred_to_str': self._get_judge(self.referred_to_regex),
        }

        data = clean_pacer_object(data)
        return data

    def query(self, pacer_case_id, query_type="History", order_by='asc',
              show_de_descriptions=False):
        """Query the docket history report and return the results. Because of
        the way this works, you have to hit PACER twice. Once to get a nonce,
        and a second time to make your query.

        :param pacer_case_id: The internal PACER case ID for a case.
        :param query_type: The type of query placed. Either "History" or
        "Documents".
        :param show_de_descriptions: Whether to show docket entry descriptions
        in the report.
        :param order_by: The ordering desired for the results, either 'asc' or
        'desc'.
        :return: request response object
        """
        # Set up and sanity tests
        assert self.session is not None, \
            "session attribute of DocketHistoryReport cannot be None."

        if query_type not in [u'History', u'Documents']:
            raise ValueError(u"Invalid value for 'query_type' parameter.")
        if show_de_descriptions is not True and show_de_descriptions is not False:
            raise ValueError(u"")
        if order_by not in ['asc', 'desc']:
            raise ValueError(u"Invalid value for 'order_by' parameter.")

        logger.info(u'Getting nonce for docket history report with '
                    u'pacer_case_id: %s' % pacer_case_id)
        r = self.session.get('%s?%s' % (self.url, pacer_case_id))
        nonce = get_nonce_from_form(r)

        query_params = {
            u'QueryType': query_type,
            u'sort1': order_by,
        }
        if show_de_descriptions:
            query_params['DisplayDktText'] = u'DisplayDktText'

        logger.info(u"Querying docket history report for case ID '%s' with "
                    u"params %s and nonce %s" % (pacer_case_id, query_params,
                                                 nonce))

        self.response = self.session.post(self.url + '?' + nonce,
                                          data=query_params)
        self.parse()

    def _set_metadata_values(self):
        text_nodes = self.tree.xpath('//center[not(.//table)]//text()')
        values = []
        for s in text_nodes:
            s = clean_string(force_unicode(s))
            if s:
                values.append(s)
        values.append(' '.join(values))
        self.metadata_values = values

    def _get_case_name(self):
        if self.is_bankruptcy:
            # Uses both b/c sometimes the bankr. cases have a dist-style docket
            # number.
            regexes = [self.docket_number_dist_regex,
                       self.docket_number_bankr_regex]
        else:
            regexes = [self.docket_number_dist_regex]

        matches = []
        # Skip the last value, it's a concat of all previous values and
        # isn't needed for case name matching.
        for prev, v, nxt in previous_and_next(self.metadata_values[:-1]):
            if prev is None:
                continue
            for regex in regexes:
                match = regex.search(prev)
                if match:
                    if self.is_bankruptcy:
                        return harmonize(v)
                    for cn_regex in [self.case_name_regex, self.in_re_regex]:
                        cn_match = cn_regex.match(v)
                        if cn_match:
                            matches.append(cn_match)
        if len(matches) == 1:
            case_name = matches[0].group(1)
        else:
            case_name = u"Unknown Case Title"
        return harmonize(case_name)

    def _get_docket_number(self):
        if self.is_bankruptcy:
            # Uses both b/c sometimes the bankr. cases have a dist-style docket
            # number.
            regexes = [self.docket_number_dist_regex,
                       self.docket_number_bankr_regex]
        else:
            regexes = [self.docket_number_dist_regex]
        nodes = self.tree.xpath('//center//font[@size="+1"]')
        string_nodes = [s.text_content() for s in nodes]
        for regex in regexes:
            for s in string_nodes:
                match = regex.search(s)
                if match:
                    return match.group(1)

    def _get_assigned_judge(self):
        if self.is_bankruptcy:
            # Look for string like "Judge: Michael J. Fox"
            for prev, v, nxt in previous_and_next(self.metadata_values[:-1]):
                if prev is not None and re.search('Judge:', prev, flags=re.I):
                    return normalize_judge_string(v)[0]
        else:
            # Look for string like "Michael J. Fox, presiding"
            return self._get_judge(self.assigned_to_regex)
