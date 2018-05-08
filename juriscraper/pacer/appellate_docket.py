from .docket_report import BaseDocketReport
from .reports import BaseReport
from .utils import clean_pacer_object


class AppellateDocketReport(BaseDocketReport, BaseReport):
    PATH = 'xxx'  # xxx for self.query
    ERROR_STRINGS = []

    def query(self, *args, **kwargs):
        raise NotImplementedError("We currently do not support querying "
                                  "appellate docket reports.")

    def __init__(self, court_id, pacer_session=None):
        pass

    def download_pdf(self, pacer_case_id, pacer_document_number):
        # xxx this is likely to need to be overridden.
        pass

    @property
    def metadata(self):
        if self._metadata is not None:
            return self._metadata

        data = {
            u'court_id': '',
            u'docket_number': '',
            u'case_name': '',
            u'date_filed': self._get_value(regex, strings, caast_to_date=True),
            u'date_terminated': self._get_value(regex, strings,
                                                caast_to_date=True),
            u'date_converted': self._get_value(regex, strings,
                                               caast_to_date=True),
            u'date_discharged': self._get_value(regex, strings,
                                                caast_to_date=True),
            u'assigned_to_str': self._get_judge(self.assigned_to_regex),
            u'referred_to_str': self._get_judge(self.referred_to_regex),
            u'cause': self._get_value(self.cause_regex, self.metadata_values),
            u'nature_of_suit': self._get_nature_of_suit(),
            u'jury_demand': self._get_value(self.jury_demand_regex,
                                            self.metadata_values),
            u'demand': self._get_value(self.demand_regex,
                                       self.metadata_values),
            u'jurisdiction': self._get_value(self.jurisdiction_regex,
                                             self.metadata_values),
        }
        data = clean_pacer_object(data)
        self._metadata = data
        return data

    @property
    def parties(self):
        """Get the party info from the HTML or return it if it's cached.

        The data here will look like this:

            parties = [{
                'name': 'NATIONAL VETERANS LEGAL SERVICES PROGRAM',
                'type': 'Plaintiff',
                'date_terminated': '2018-03-12',
                'extra_info': ("1600 K Street, NW\n"
                               "Washington, DC 20006"),
                'attorneys': [{
                    'name': 'William H. Narwold',
                    'contact': ("1 Corporate Center\n",
                                "20 Church Street\n",
                                "17th Floor\n",
                                "Hartford, CT 06103\n",
                                "860-882-1676\n",
                                "Fax: 860-882-1682\n",
                                "Email: bnarwold@motleyrice.com"),
                    'roles': ['LEAD ATTORNEY',
                              'PRO HAC VICE',
                              'ATTORNEY TO BE NOTICED'],
                }, {
                    ...more attorneys here...
                }]
            }, {
                ...more parties (and their attorneys) here...
            }]
        """
        if self._parties is not None:
            return self._parties

        party_rows = self.tree.xpath(path)

        parties = []
        party = {}
        for prev, row, nxt in previous_and_next(party_rows):
            # xxx get party metadata here

            if len(cells) == 3 and party != {}:
                party[u'attorneys'] = self._get_attorneys(cells[2])

            if party not in parties and party != {}:
                # Sometimes there are dups in the docket. Avoid them.
                parties.append(party)

        parties = self._normalize_see_above_attorneys(parties)
        self._parties = parties
        return parties

    def _get_attorneys(self, cell):
        # Get the attorneys here.
        pass

    @property
    def docket_entries(self):
        """Get the docket entries"""
        if self._docket_entries is not None:
            return self._docket_entries

        docket_entries = []
        for row in docket_entry_rows:
            de = {}

        docket_entries = clean_pacer_object(docket_entries)
        self._docket_entries = docket_entries
        return docket_entries

