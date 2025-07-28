import os
import re
import sys

from juriscraper.pacer import ACMSDocketReport
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase


class PacerParseAppellateDocketTest(PacerParseTestCase):
    """Can we parse the appellate dockets effectively?"""

    def setUp(self):
        self.maxDiff = 200000

    def test_parsing_appellate_dockets(self):
        path_root = os.path.join(TESTS_ROOT_EXAMPLES_PACER, "dockets", "acms")
        self.parse_files(path_root, "*.acms_json", ACMSDocketReport)

    def test_acms_datatypes(self):
        """Ensure the proper types are returned for a faked-up docket.

        In particular, the standard tests compare JSON output but do
        not validate datetime types.
        """

        faked_input = """
        {
          "caseDetails": {
            "caseId": "49d55502-744d-11ee-b5fa-e38eb4ba6cd2",
            "caseNumber": "23-1",
            "name": "Free Law Project v. People",
            "caseOpened": "2023-10-26",
            "aNumber": "46-3342480",
            "receivedDate": "2023-10-26T22:18:31Z",
            "partyAttorneyList":
              "<table><tr><td>FREE LAW PARTY<br>Intervenor<td>pro se</table>",
            "court": {
              "name": "Originating court name",
              "identifier": "OGC ID"
            },
            "caseType": "Typical",
            "caseSubType": "Subtypical",
            "caseSubSubType": "Subsubtypical",
            "districtCourtName": "FLP",
            "feeStatus": "FLP"
          },
          "docketInfo": {
            "docketEntries": [
              {
                "endDate": "2023-10-28",
                "endDateFormatted": "10/28/2023",
                "entryNumber": 1,
                "docketEntryText": "<p>NEW PARTY, Intervenor, Free Law Project. [Entered: 10/26/2023 6:18 PM]</p>",
                "docketEntryId": "19b65316-744e-11ee-a0a4-13890013fe63",
                "pageCount": 1
              }
            ]
          }
        }
"""  # noqa

        indented_padded_correct_repr_old = """
        {'court_id': 'flp',
          'pacer_case_id': '49d55502-744d-11ee-b5fa-e38eb4ba6cd2',
          'docket_number': '23-1',
          'case_name': 'Free Law Project v. People',
          'date_filed': datetime.date(2023, 10, 26),
          'appeal_from': 'Originating court name',
          'fee_status': 'FLP',
          'originating_court_information':
            {'name': 'FLP',
             'identifier': 'OGC ID',
             'RESTRICTED_ALIEN_NUMBER': '46-3342480'},
         'case_type_information': 'Typical, Subtypical, Subsubtypical',
         'parties': [OrderedDict([('name',
         'FREE LAW PARTY'), ('type',
         'Intervenor'), ('attorneys', [])])],
         'docket_entries': [{'document_number': 1,
             'description_html': '<p>NEW PARTY, Intervenor, Free Law Project. [Entered: 10/26/2023 6:18 PM]</p>',
             'description': 'NEW PARTY, Intervenor, Free Law Project. [Entered: 10/26/2023 6:18 PM]',
             'date_entered': datetime.datetime(2023, 10, 26, 18, 18),
             'date_filed': datetime.datetime(2023, 10, 28, 0, 0),
             'pacer_doc_id': '19b65316-744e-11ee-a0a4-13890013fe63',
             'page_count': 1}]}"""  # noqa

        indented_padded_correct_repr = """
        {'court_id': 'flp',
          'pacer_case_id': '49d55502-744d-11ee-b5fa-e38eb4ba6cd2',
          'docket_number': '23-1',
          'case_name': 'Free Law Project v. People',
          'date_filed': datetime.date(2023, 10, 26),
          'appeal_from': 'Originating court name',
          'fee_status': 'FLP',
          'originating_court_information':
            {'name': 'FLP',
             'identifier': 'OGC ID',
             'RESTRICTED_ALIEN_NUMBER': '46-3342480'},
         'case_type_information': 'Typical, Subtypical, Subsubtypical',
         'parties': [OrderedDict({'name':
         'FREE LAW PARTY', 'type':
         'Intervenor', 'attorneys': []})],
         'docket_entries': [{'document_number': 1,
             'description_html': '<p>NEW PARTY, Intervenor, Free Law Project. [Entered: 10/26/2023 6:18 PM]</p>',
             'description': 'NEW PARTY, Intervenor, Free Law Project. [Entered: 10/26/2023 6:18 PM]',
             'date_entered': datetime.datetime(2023, 10, 26, 18, 18),
             'date_filed': datetime.datetime(2023, 10, 28, 0, 0),
             'pacer_doc_id': '19b65316-744e-11ee-a0a4-13890013fe63',
             'page_count': 1}]}"""  # noqa

        # Python 3.12 changed the format of OrderedDict so pick the appropriate
        # repr here.
        if sys.version_info >= (3, 12, 0):
            _ = indented_padded_correct_repr
        else:
            _ = indented_padded_correct_repr_old
        _ = re.sub(r"(?m)^\s*", "", _)
        correct_repr = _.replace("\n", " ")

        report = ACMSDocketReport("flp")
        report._parse_text(faked_input)

        self.assertEqual(repr(report.data), correct_repr)
