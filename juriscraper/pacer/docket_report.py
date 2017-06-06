import re
from lxml.etree import _ElementStringResult

from juriscraper.lib.judge_parsers import normalize_judge_string
from juriscraper.lib.string_utils import convert_date_string
from lxml.html import tostring, fromstring, HtmlElement

from ..lib.exceptions import ParsingException
from ..lib.html_utils import set_response_encoding, clean_html, \
    get_html5_parsed_text, fix_links_in_lxml_tree
from ..lib.log_tools import make_default_logger
from ..lib.utils import previous_and_next

logger = make_default_logger()


class DocketReport(object):

    case_name_regex = re.compile(r"(.*\bv\.\s.*)")
    in_re_regex = re.compile(r"\bIN\s+RE:\s+.*", flags=re.IGNORECASE)
    date_filed_regex = re.compile(r'Date [fF]iled:\s+(.*)')
    date_terminated_regex = re.compile(r'Date [tT]erminated:\s+(.*)')
    date_last_filing_regex = re.compile(r"Date of last filing:\s+(.*)")
    assigned_to_regex = re.compile(r'Assigned to:\s+(.*)')
    referred_to_regex = re.compile(r'Referred to:\s+(.*)')
    cause_regex = re.compile(r'Cause:\s+(.*)')
    nature_of_suit_regex = re.compile(r'Nature of Suit:\s+(.*)')
    jury_demand_regex = re.compile(r'Jury Demand:\s+(.*)')
    jurisdiction_regex = re.compile(r'Jurisdiction:\s+(.*)')
    demand_regex = re.compile(r'^Demand:\s+(.*)')

    def __init__(self, court_id, pacer_session):
        self.court_id = court_id
        self.session = pacer_session
        self.html_tree = None

        # Cache-properties
        self._metadata = {}
        self._parties = []
        self._docket_entries = []

        if self.court_id.endswith('b'):
            self.is_bankruptcy = True
            self.docket_number_regex = re.compile(r"#:\s+((\d-)?\d\d-\d*)")
            self.docket_number_path = '//font'
        else:
            self.is_bankruptcy = False
            self.docket_number_regex = re.compile(
                r"((\d{1,2}:)?\d\d-[a-zA-Z]{1,4}-\d{1,10})")
            self.docket_number_path = '//h3'

        super(DocketReport, self).__init__()

    @property
    def url(self):
        if self.court_id == 'psc':
            return 'https://dcecf.psc.uscourts.gov/cgi-bin/DktRpt.pl'
        else:
            return 'https://ecf.%s.uscourts.gov/cgi-bin/DktRpt.pl' % self.court_id

    @property
    def data(self):
        data = self.metadata.copy()
        data['parties'] = self.parties
        data['docket_entries'] = self.docket_entries
        return data

    @property
    def metadata(self):
        if self._metadata:
            return self._metadata

        # The first ancestor table of the table cell containing "date filed"
        metadata_values = self._get_metadata_table_cell_values()
        data = {
            'court_id': self.court_id,
            'docket_number': self._get_docket_number(),
            'case_name': self._get_case_name(metadata_values),
            'date_filed': self._get_date_filed(metadata_values),
            'date_terminated': self._get_date_terminated(metadata_values),
            'date_last_filing': self._get_date_last_filing(metadata_values),
            'assigned_to_str': self._get_assigned_to(metadata_values),
            'referred_to_str': self._get_referred_to(metadata_values),
            'cause': self.__get_matching_value(
                metadata_values,
                self.cause_regex,
            ),
            'nature_of_suit': self.__get_matching_value(
                metadata_values,
                self.nature_of_suit_regex,
            ),
            'jury_demand': self.__get_matching_value(
                metadata_values,
                self.jury_demand_regex,
            ),
            'demand': self.__get_matching_value(
                metadata_values,
                self.demand_regex,
            ),
            'jurisdiction': self.__get_matching_value(
                metadata_values,
                self.jurisdiction_regex,
            ),
        }
        self._metadata = data
        return data

    @property
    def parties(self):
        """Get the party info from the HTML or return it if it's cached.
        
        The data here will look like this:
        
            parties = [{
                'name': 'NATIONAL VETERANS LEGAL SERVICES PROGRAM',
                'type': 'Plaintiff',
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
        if self._parties:
            return self._parties

        # party_identifiers = ['Defendant', 'Plaintiff', 'Petitioner',
        #                      'Respondent', 'Debtor', 'Trustee', 'Mediator',
        #                      'Creditor Committee', 'Intervenor', 'Claimant']
        # or_condition = ' or '.join(["contains(.//text(), '%s')" % s for s in
        #                            party_identifiers])
        # path = '//td[%s]' % or_condition

        # All sibling rows to the rows that identify this as a party table.
        path = ('//tr['
                '    .//i/b/text() or '  # Bankruptcy
                '    .//b/u/text() or '  # Regular district
                '    .//b/text()[contains(., "-----")]'  # Adversary proceedings
                ']/../tr')
        party_rows = self.html_tree.xpath(path)

        parties = []
        for row in party_rows:
            cells = row.xpath('.//td')
            if len(cells) == 0:
                # Empty row. Press on.
                continue
            row_text = row.text_content().strip().lower()
            if not row_text or row_text == 'v.':
                # Empty or nearly empty row. Press on.
                continue

            if len(cells) == 1 and cells[0].xpath('.//b'):
                # It's a party type value.
                party = {'type': cells[0].text_content().strip()}
                continue

            if len(cells) == 3:
                party['name'] = cells[0].xpath('.//b')[0].text_content().strip()
                party['extra_info'] = ''.join(
                    s.strip() for s in
                    cells[0].xpath('.//text()[not(./parent::b)]')
                )
                party['attorneys'] = self.get_attorneys(cells[2])
                parties.append(party)

        self._parties = parties
        return parties

    def get_attorneys(self, cell):
        """Get the attorney information from an HTML tr node.
        
        Input will look like:
        
            <td width="40%" valign="top">
                <b>Allen                Durham          Arnold         </b> 
                <br>Arendall &amp; Associates                                       
                <br>2018 Morris Avenue                                          
                <br>Suite 300                                                   
                <br>Birmingham              , AL 35203          
                <br>205-252-1550             
                <br>Fax: 205-252-1556        
                <br>Email: ada@arendalllaw.com
                <br><i>LEAD ATTORNEY</i>
                <br><i>ATTORNEY TO BE NOTICED</i><br><br>
                
                <b>David                Randall         Arendall        </b> 
                <br>Arendall &amp; Associates
                <br>2018 Morris Avenue, Third Floor
                <br>Birmingham              , AL 35203
                <br>205-252-1550
                <br>Fax: 205-252-1556
                <br>Email: dra@arendalllaw.com
                <br><i>LEAD ATTORNEY</i>
                <br><i>ATTORNEY TO BE NOTICED</i><br><br>
            </td>
            
        Output:
        
            [{
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
        """
        attorneys = []
        for atty_node in cell.xpath('.//b'):
            attorney = {
                'name': ' '.join(atty_node.text_content().strip().split()),
                'roles': [],
                'contact': '',
            }
            path = './following-sibling::* | ./following-sibling::text()'
            for prev, node, nxt in previous_and_next(atty_node.xpath(path)):
                if isinstance(node, _ElementStringResult):
                    clean_atty = '%s\n' % ' '.join(n.strip() for n in node.split())
                    if clean_atty.strip():
                        attorney['contact'] += clean_atty
                else:
                    if node.tag == 'i':
                        # It's a role.
                        attorney['roles'].append(node.text_content().strip())

                nxt_is_b_tag = isinstance(nxt, HtmlElement) and nxt.tag == 'b'
                if nxt is None or nxt_is_b_tag:
                    # No more data for this attorney.
                    attorneys.append(attorney)
                    break

        return attorneys

    @property
    def docket_entries(self):
        if self._docket_entries:
            return self._docket_entries
        docket_entries = {}
        self._docket_entries = docket_entries
        return docket_entries

    def query(self, pacer_case_id, date_range_type='Filed', date_start='',
              date_end='', doc_num_start='', doc_num_end='',
              show_parties_and_counsel=False, show_terminated_parties=False,
              show_list_of_member_cases=False, include_pdf_headers=True,
              show_multiple_docs=False, output_format='html',
              order_by='date'):
        """Query the docket report and return the results.

        :param pacer_case_id: The internal PACER case ID for a case.
        :param date_range_type: Whether the date range refers to the date items
        were entered into PACER or the date they were filed.
        :param date_start: The start date for the date range.
        :param date_end: The end date for the date range.
        :param doc_num_start: A range of documents can be requested. This is the
        lower bound of their ID numbers.
        :param doc_num_end: The upper bound of the requested documents.
        :param show_parties_and_counsel: Whether to show the parties and counsel
        in a case (note this adds expense).
        :param show_terminated_parties: Whether to show terminated parties in a
        case (note this adds expense).
        :param show_list_of_member_cases: Whether to show a list of member
        cases (note, this adds expense).
        :param include_pdf_headers: Whether the PDFs should have headers
        containing their metadata.
        :param show_multiple_docs: Show multiple docs at one time.
        :param output_format: Whether to get back the results as a PDF or as
        HTML.
        :param order_by: The ordering desired for the results.
        :return: request response object
        """
        # Set up and sanity tests
        if date_range_type not in ['Filed', 'Entered']:
            raise ValueError("Invalid value for 'date_range_type' parameter.")
        if output_format not in ['html', 'pdf']:
            raise ValueError("Invalid value for 'output_format' parameter.")
        if order_by == 'date':
            order_by = 'oldest date first'
        elif order_by == '-date':
            order_by = 'most recent date first'
        elif order_by == 'document_number':
            order_by = 'document number'
        else:
            raise ValueError("Invalid value for 'order_by' parameter.")

        if show_terminated_parties and not show_parties_and_counsel:
            raise ValueError("Cannot show terminated parties if parties and "
                             "counsel are not also requested.")

        query_params = {
            'all_case_ids': pacer_case_id,
            'sort1': order_by,
            'date_range_type': date_range_type,
            'output_format': output_format,

            # Any value works in this parameter, but it cannot be blank.
            # Normally this would have a value like '3:12-cv-3879', but that's
            # not even necessary.
            'case_num': ' '

            # These fields seem to be unnecessary/unused.
            # 'view_comb_doc_text': '',
            # 'PreResetField': '',
            # 'PreResetFields': '',
        }
        if date_start:
            query_params['date_from'] = date_start.strftime('%m/%d/%Y')
        if date_end:
            query_params['date_to'] = date_end.strftime('%m/%d/%Y')
        if doc_num_start:
            query_params['documents_numbered_from_'] = str(int(doc_num_start))
        if doc_num_end:
            query_params['documents_numbered_to_'] = str(int(doc_num_end))
        if show_parties_and_counsel is True:
            query_params['list_of_parties_and_counsel'] = 'on'
        if show_terminated_parties is True:
            query_params['terminated_parties'] = 'on'
        if show_list_of_member_cases is True:
            query_params['list_of_member_cases'] = 'on'
        if include_pdf_headers is True:
            query_params['pdf_header'] = '1'
        if show_multiple_docs is True:
            query_params['view_multi_docs'] = 'on'

        logger.info("Querying docket report for case ID '%s' with params %s" %
                    (pacer_case_id, query_params))

        return self.session.post(self.url + '?1-L_1_0-1', data=query_params,
                                 timeout=300)

    def parse(self, response):
        """Parse an HTML docket page.
        
        This will attempt to cover all of the corner cases across jurisdictions.
        
        :param response: a python request response object 
        :return: a dict containing all the data from a docket.
        """
        response.raise_for_status()
        set_response_encoding(response)
        text = clean_html(response.text)
        tree = get_html5_parsed_text(text)
        tree.rewrite_links(fix_links_in_lxml_tree, base_href=response.url)
        self.html_tree = tree

    def _get_metadata_table_cell_values(self):
        table = self.html_tree.xpath(
            '//td[contains('
            '    translate(.//text(), "f", "F"),'  # Match on Date [fF]iled
            '    "Date Filed:"'
            ')]/ancestor::table[1]'
        )[0]
        cells = table.xpath('.//td')
        strs = []
        # Convert the <br> separated content into text strings, treating as much
        # as possible as HTML.
        sep = 'FLP_SEPARATOR'
        for cell in cells:
            # Split on BR
            s = tostring(cell, encoding='unicode')
            s = re.sub(r'<br/?>', sep, s, flags=re.I)
            element = fromstring(s)
            strs.extend([s.strip() for s in
                         element.text_content().split(sep) if s])
        return strs

    def _get_case_name(self, values):
        if self.is_bankruptcy:
            pass
        else:
            matches = []
            for v in values:
                if self.case_name_regex.search(v):
                    matches.append(v)
                if self.in_re_regex.search(v):
                    matches.append(v)
            if len(matches) == 1:
                return matches[0]
            else:
                raise ParsingException("Unable to get case name.")

    def _get_docket_number(self):
        nodes = self.html_tree.xpath(self.docket_number_path)
        string_nodes = [s.text_content() for s in nodes]
        for s in string_nodes:
            match = self.docket_number_regex.search(s)
            if match:
                return match.group(1)

    def _get_date_filed(self, values):
        date_filed_str = self.__get_matching_value(
            values,
            self.date_filed_regex,
        )
        if date_filed_str is not None:
            return convert_date_string(date_filed_str)

    def _get_date_terminated(self, values):
        date_terminated_str = self.__get_matching_value(
            values,
            self.date_terminated_regex,
        )
        if date_terminated_str is not None:
            return convert_date_string(date_terminated_str)

    def _get_date_last_filing(self, values):
        date_last_filing_str = self.__get_matching_value(
            values,
            self.date_last_filing_regex,
        )
        if date_last_filing_str is not None:
            return convert_date_string(date_last_filing_str)

    def _get_assigned_to(self, values):
        judge_str = self.__get_matching_value(values, self.assigned_to_regex)
        if judge_str is not None:
            return normalize_judge_string(judge_str)[0]

    def _get_referred_to(self, values):
        judge_str = self.__get_matching_value(values, self.referred_to_regex)
        if judge_str is not None:
            return normalize_judge_string(judge_str)[0]

    @staticmethod
    def __get_matching_value(values, regex):
        """Find the matching value for a regex.
        
        Iterate over a list of values and return group(1) for the first that 
        matches regex. If none matches, return None.
        """
        for v in values:
            m = regex.search(v)
            if m:
                return m.group(1)
        return None
