# coding=utf-8
import re

from lxml import etree
from lxml.html import tostring, fromstring, HtmlElement

from .docket_utils import normalize_party_types
from .reports import BaseReport
from .utils import get_pacer_doc_id_from_doc1_url, clean_pacer_object
from ..lib.judge_parsers import normalize_judge_string
from ..lib.log_tools import make_default_logger
from ..lib.string_utils import convert_date_string, force_unicode, harmonize, \
    clean_string
from ..lib.utils import previous_and_next

logger = make_default_logger()

date_regex = r'[—\d\-–/]+'


class DocketReport(BaseReport):

    case_name_regex = re.compile(r"(?:Case\s+title:\s+)?(.*\bv\.?\s.*)")
    in_re_regex = re.compile(r"(\bIN\s+RE:\s+.*)", flags=re.IGNORECASE)
    date_filed_regex = re.compile(r'Date [fF]iled:\s+(%s)' % date_regex)
    date_terminated_regex = re.compile(r'Date [tT]erminated:\s+(%s)' % date_regex)
    date_converted_regex = re.compile(r'Date [Cc]onverted:\s+(%s)' % date_regex)
    # Be careful this does not match "Joint debtor discharged" field.
    date_discharged_regex = re.compile(r'(?:Date|Debtor)\s+[Dd]ischarged:\s+(%s)' % date_regex)
    assigned_to_regex = re.compile(r'Assigned to:\s+(.*)')
    referred_to_regex = re.compile(r'Referred to:\s+(.*)')
    cause_regex = re.compile(r'Cause:\s+(.*)')
    nos_regex = re.compile(r'Nature of Suit:\s+(.*)')
    jury_demand_regex = re.compile(r'Jury Demand:\s+(.*)')
    jurisdiction_regex = re.compile(r'Jurisdiction:\s+(.*)')
    demand_regex = re.compile(r'^Demand:\s+(.*)')
    docket_number_dist_regex = re.compile(r"((\d{1,2}:)?\d\d-[a-zA-Z]{1,4}-\d{1,10})")
    docket_number_bankr_regex = re.compile(r"(?:#:\s+)?((\d-)?\d\d-\d*)")

    PATH = 'cgi-bin/DktRpt.pl'

    CACHE_ATTRS = ['metadata', 'parties', 'docket_entries',
                   'is_adversary_proceeding']

    ERROR_STRINGS = BaseReport.ERROR_STRINGS + [
        "The report may take a long time to run because this case has many docket entries",
        "The page ID does not exist. Please enter a valid page ID number. ",
        "There are no documents in this case.",
        "Incomplete request. Please try your query again by choosing the Query or Reports option",
        "To accept charges shown below, click on the 'View Report' button",
        "Unable to create PDF file.",
        "This case was administratively closed",
        "The start date must be less than or equal to the end date",
        "The starting document number must be less than or equal to the ending document number",
        "Case not found.",
        "Either you do not have permission to view the document, or the document does not exist in the case.",
        "Format: text",
    ]

    def __init__(self, court_id, pacer_session=None):
        super(DocketReport, self).__init__(court_id, pacer_session)
        # Initialize the empty cache properties.
        self._clear_caches()

        if self.court_id.endswith('b'):
            self.is_bankruptcy = True
        else:
            self.is_bankruptcy = False

    def _clear_caches(self):
        """Clear any caches that are on the object."""
        for attr in self.CACHE_ATTRS:
            setattr(self, '_%s' % attr, None)

    def parse(self):
        """Parse the item, but be sure to clear the cache before you do so.

        This ensures that if the DocketReport is used to parse multiple items,
        the cache is cleared in between.
        """
        self._clear_caches()
        super(DocketReport, self).parse()

    @property
    def data(self):
        """Get all the data back from this endpoint."""
        if self.is_valid is False:
            return {}

        data = self.metadata.copy()
        data[u'parties'] = self.parties
        data[u'docket_entries'] = self.docket_entries
        return data

    @property
    def metadata(self):
        if self._metadata is not None:
            return self._metadata

        self._set_metadata_values()
        data = {
            u'court_id': self.court_id,
            u'docket_number': self._get_docket_number(),
            u'case_name': self._get_case_name(),
            u'date_filed': self._get_value(self.date_filed_regex,
                                           cast_to_date=True),
            u'date_terminated': self._get_value(self.date_terminated_regex,
                                                cast_to_date=True),
            u'date_converted': self._get_value(self.date_converted_regex,
                                               cast_to_date=True),
            u'date_discharged': self._get_value(self.date_discharged_regex,
                                                cast_to_date=True),
            u'assigned_to_str': self._get_judge(self.assigned_to_regex),
            u'referred_to_str': self._get_judge(self.referred_to_regex),
            u'cause': self._get_value(self.cause_regex),
            u'nature_of_suit': self._get_nature_of_suit(),
            u'jury_demand': self._get_value(self.jury_demand_regex),
            u'demand': self._get_value(self.demand_regex),
            u'jurisdiction': self._get_value(self.jurisdiction_regex),
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

        # All sibling rows to the rows that identify this as a party table.
        # We focus on the first td, because sometimes the third td in the
        # document table has bold/underline/italic text.
        path = (
            '//tr['
            '    ./td[1]//i/b/text() or '  # Bankruptcy
            '    ./td[1]//b/u/text() or '  # Regular district
            '    ./td[1]//b/text()[contains(., "-----")]'  # Adversary proceedings
            ']/../tr'
        )
        party_rows = self.tree.xpath(path)

        parties = []
        party = {}
        for prev, row, nxt in previous_and_next(party_rows):
            cells = row.xpath('.//td')
            if len(cells) == 0:
                # Empty row. Press on.
                continue
            row_text = force_unicode(row.text_content()).strip().lower()
            if not row_text or row_text == 'v.':
                # Empty or nearly empty row. Press on.
                continue

            # Handling for CA cases that put non-party info in the party html
            # table (see cand, 3:09-cr-00418).
            if cells[0].xpath('.//b/u'):
                # If a header is followed by a cell that lacks bold text, punt
                # the header row.
                if nxt is None or not nxt.xpath('.//b'):
                    continue
            elif not row.xpath('.//b'):
                # If a row has no bold text, we can punt it. The bold normally
                # signifies the party's name, or the party type. This ignores
                # the metadata under these sections.
                continue

            if len(cells) == 1 and cells[0].xpath('.//b/u'):
                # Regular docket - party type value.
                s = force_unicode(cells[0].text_content())
                party = {u'type': normalize_party_types(s)}
                continue
            elif '------' in row_text:
                # Adversary proceeding
                s = force_unicode(cells[0].text_content().strip())
                if len(cells) == 1:
                    s = re.sub(u'----*', '', s)
                    party = {u'type': normalize_party_types(s)}
                    continue
                elif len(cells) == 3:
                    # Some courts have malformed HTML that requires extra work.
                    party = {u'type': re.split(u'----*', s)[0]}
            elif len(cells) == 3 and cells[0].xpath('.//i/b'):
                # Bankruptcy - party type value.
                s = force_unicode(cells[0].xpath(u'.//i')[0].text_content())
                party = {u'type': normalize_party_types(s)}
            elif len(cells) == 3 and u'service list' in row_text:
                # Special case to handle the service list.
                party = {u'type': u"Service List"}

            name_path = u'.//b[not(./parent::i)][not(./u)][not(contains(., "------"))]'
            is_party_name_cell = (len(cells[0].xpath(name_path)) > 0)
            if is_party_name_cell:
                element = cells[0].xpath(name_path)[0]
                party[u'name'] = force_unicode(element.text_content().strip())
                party[u'extra_info'] = u'\n'.join(
                    force_unicode(s.strip()) for s in
                    cells[0].xpath(u'.//text()[not(./parent::b)]') if
                    s.strip()
                )

            if len(cells) == 3:
                party[u'attorneys'] = self._get_attorneys(cells[2])

            if party not in parties:
                # Sometimes there are dups in the docket. Avoid them.
                parties.append(party)

            if self.is_adversary_proceeding:
                # In adversary proceedings, there are multiple rows under one
                # party type header. Nuke the bulk of the party dict, except for
                # the type so that it's ready for the next iteration.
                party = {u'type': party[u'type']}
            else:
                party = {}

        parties = self._normalize_see_above_attorneys(parties)
        self._parties = parties
        return parties

    @staticmethod
    def _get_attorneys(cell):
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
            name_parts = force_unicode(atty_node.text_content().strip()).split()
            attorney = {
                u'name': u' '.join(name_parts),
                u'roles': [],
                u'contact': u'',
            }
            path = u'./following-sibling::* | ./following-sibling::text()'
            for prev, node, nxt in previous_and_next(atty_node.xpath(path)):
                # noinspection PyProtectedMember
                if isinstance(node, (etree._ElementStringResult,
                                     etree._ElementUnicodeResult)):
                    clean_atty = u'%s\n' % ' '.join(n.strip() for n in node.split())
                    if clean_atty.strip():
                        attorney[u'contact'] += clean_atty
                else:
                    if node.tag == u'i':
                        role = force_unicode(node.text_content().strip())
                        if not any([role.lower().startswith(u'bar status'),
                                    role.lower().startswith(u'designation')]):
                            attorney[u'roles'].append(role)

                nxt_is_b_tag = isinstance(nxt, HtmlElement) and nxt.tag == 'b'
                if nxt is None or nxt_is_b_tag:
                    # No more data for this attorney.
                    attorneys.append(attorney)
                    break

        return attorneys

    @staticmethod
    def _normalize_see_above_attorneys(parties):
        """PACER frequently has "See above" for the contact info of an attorney.
        Normalize these values.
        """
        atty_cache = {}
        for party in parties:
            for atty in party.get(u'attorneys', []):
                if not atty[u'contact']:
                    continue

                if re.search(r'see\s+above', atty[u'contact'], re.I):
                    try:
                        atty_info = atty_cache[atty[u'name']]
                    except KeyError:
                        # Unable to find the atty in the cache, therefore, we
                        # don't know their contact info.
                        atty[u'contact'] = u''
                    else:
                        # Found the atty in the cache. Use the info.
                        atty[u'contact'] = atty_info
                else:
                    # We have atty info. Save it.
                    atty_cache[atty[u'name']] = atty[u'contact']
        return parties

    @property
    def docket_entries(self):
        if self._docket_entries is not None:
            return self._docket_entries

        # There can be multiple docket entry tables on a single docket page. See
        # https://github.com/freelawproject/courtlistener/issues/762. ∴ we need
        # to identify the first table, and all following tables. The following
        # tables lack column headers, so we have to use the preceding-sibling
        # tables to make sure it's right.
        docket_header = './/text()[contains(., "Docket Text")]'
        bankr_multi_doc = 'not(.//text()[contains(., "Total file size of selected documents")])'
        docket_entry_rows = self.tree.xpath(
            '//table['
            '  preceding-sibling::table[{dh}] or {dh}'
            '][{b_multi_doc}]/tbody/tr'.format(
                dh=docket_header,
                b_multi_doc=bankr_multi_doc,
            )
        )[1:]  # Skip the first row.

        docket_entries = []
        for row in docket_entry_rows:
            de = {}
            cells = row.xpath(u'./td')
            if len(cells) == 4:
                # In some instances, the document entry table has an extra
                # column. See almb, 92-04963
                del cells[1]

            date_filed_str = force_unicode(cells[0].text_content())
            de[u'date_filed'] = convert_date_string(date_filed_str)
            de[u'document_number'] = self._get_document_number(cells[1])
            de[u'pacer_doc_id'] = self._get_pacer_doc_id(cells[1],
                                                         de[u'document_number'])
            de[u'description'] = self._get_description(cells)
            if not de[u'document_number']:
                # Minute order. Skip for now.
                continue
            if not de[u'document_number'].isdigit():
                # Some courts put weird stuff in this column.
                continue
            docket_entries.append(de)

        docket_entries = clean_pacer_object(docket_entries)
        self._docket_entries = docket_entries
        return docket_entries

    @property
    def is_adversary_proceeding(self):
        if self._is_adversary_proceeding is not None:
            return self._is_adversary_proceeding

        adversary_proceeding = False
        path = u'//*[text()[contains(., "Adversary Proceeding")]]'
        if self.tree.xpath(path):
            adversary_proceeding = True

        self._is_adversary_proceeding = adversary_proceeding
        return adversary_proceeding

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
        assert self.session is not None, \
            "session attribute of DocketReport cannot be None."
        assert bool(pacer_case_id), \
            "pacer_case_id must be truthy, not '%s'" % pacer_case_id

        if date_range_type not in [u'Filed', u'Entered']:
            raise ValueError(u"Invalid value for 'date_range_type' parameter.")
        if output_format not in [u'html', u'pdf']:
            raise ValueError(u"Invalid value for 'output_format' parameter.")
        if order_by == u'date':
            order_by = u'oldest date first'
        elif order_by == u'-date':
            order_by = u'most recent date first'
        elif order_by == u'document_number':
            order_by = u'document number'
        else:
            raise ValueError(u"Invalid value for 'order_by' parameter.")

        if show_terminated_parties and not show_parties_and_counsel:
            raise ValueError(u"Cannot show terminated parties if parties and "
                             u"counsel are not also requested.")

        query_params = {
            u'all_case_ids': pacer_case_id,
            u'sort1': order_by,
            u'date_range_type': date_range_type,
            u'output_format': output_format,

            # Any value works in this parameter, but it cannot be blank.
            # Normally this would have a value like '3:12-cv-3879', but that's
            # not even necessary.
            u'case_num': u' '

            # These fields seem to be unnecessary/unused.
            # 'view_comb_doc_text': '',
            # 'PreResetField': '',
            # 'PreResetFields': '',
        }
        if date_start:
            query_params[u'date_from'] = date_start.strftime(u'%m/%d/%Y')
        else:
            # If it's a big docket and you don't filter it in some form you get
            # an intermediate page that says, paraphrasing: "Do you really want
            # to pull that whole, big, docket?" However, if we always make sure
            # to have this field populated, we don't see that page. ∴, always
            # set this value. See #210.
            query_params[u'date_from'] = '1/1/1960'
        if date_end:
            query_params[u'date_to'] = date_end.strftime(u'%m/%d/%Y')
        if doc_num_start:
            query_params[u'documents_numbered_from_'] = str(int(doc_num_start))
        if doc_num_end:
            query_params[u'documents_numbered_to_'] = str(int(doc_num_end))
        if show_parties_and_counsel is True:
            query_params[u'list_of_parties_and_counsel'] = u'on'
        if show_terminated_parties is True:
            query_params[u'terminated_parties'] = u'on'
        if show_list_of_member_cases is True:
            query_params[u'list_of_member_cases'] = u'on'
        if include_pdf_headers is True:
            query_params[u'pdf_header'] = u'1'
        if show_multiple_docs is True:
            query_params[u'view_multi_docs'] = u'on'

        logger.info(u"Querying docket report for case ID '%s' with params %s" %
                    (pacer_case_id, query_params))

        self.response = self.session.post(self.url + '?1-L_1_0-1',
                                          data=query_params)
        self.parse()

    def _set_metadata_values(self):
        # The first ancestor table of the table cell containing "date filed"
        table = self.tree.xpath(
            # Match any td containing Date [fF]iled
            u'//td[.//text()[contains(translate(., "f", "F"), "Date Filed:")]]'
            # And find its highest ancestor table that lacks a center tag.
            u'/ancestor::table[not(.//center)][last()]'
        )[0]
        cells = table.xpath(u'.//td')
        # Convert the <br> separated content into text strings, treating as much
        # as possible as HTML.
        values = []
        for cell in cells:
            clean_texts = [clean_string(s) for s in self._br_split(cell)]
            values.extend(clean_texts)
        values.append(' '.join(values))
        self.metadata_values = values

    @staticmethod
    def _get_pacer_doc_id(cell, document_number):
        if not document_number:
            return None
        else:
            # We find the first link having the document number as text.
            # This is needed because txnb combines the second and third
            # column in their docket report.
            urls = cell.xpath(u'.//a')
            if len(urls) == 0:
                # Docket entry exists, but cannot download document (it's sealed
                # or otherwise unavailable in PACER).
                return None
            for url in urls:
                if url.text_content().strip() == document_number:
                    doc1_url = url.xpath('./@href')[0]
                    return get_pacer_doc_id_from_doc1_url(doc1_url)

    def _get_document_number(self, cell):
        """Get the document number.

        Some jurisdictions have the number as, "13 (5 pgs)" so some processing
        is needed. See flsb, 09-02199-JKO.
        """
        words = [word for phrase in self._br_split(cell) for word in
                 phrase.split()]
        if words:
            first_word = re.sub(u'[\s\u00A0]', '', words[0])
            if self.court_id == u'txnb':
                # txnb merges the second and third columns, so if the first word
                # is a number, return it. Otherwise, assume doc number isn't
                # listed for the item.
                if first_word.isdigit():
                    return first_word
            else:
                return first_word
        return u''

    def _get_description(self, cells):
        if self.court_id != u'txnb':
            return force_unicode(cells[2].text_content())

        s = force_unicode(cells[1].text_content())
        # In txnb the second and third columns of the docket entries are
        # combined. The field can have one of four formats. Attempt the most
        # detailed first, then work our way down to just giving up and capturing
        # it all.
        ws = u'[\s\u00A0]'  # Whitespace including nbsp
        regexes = [
            # 2 (23 pgs; 4 docs) Blab blah (happens when attachments exist and
            # page numbers are on)
            u'^{ws}*\d+{ws}+\(\d+{ws}+pgs;{ws}\d+{ws}docs\){ws}+(.*)',
            # 2 (23 pgs) Blab blah (happens when pg nums are on)
            u'^{ws}*\d+{ws}+\(\d+{ws}+pgs\){ws}+(.*)',
            # 2 Blab blah (happens when page nums are off)
            u'^{ws}*\d+{ws}+(.*)',
            # Blab blah (happens when a doc is sealed; can't be downloaded)
            u'^{ws}*(.*)',
        ]
        for regex in regexes:
            try:
                desc = re.search(regex.format(ws=ws), s).group(1)
                break
            except AttributeError:
                continue
        # OK to ignore error below b/c last regex will always match.
        # noinspection PyUnboundLocalVariable
        return desc

    def _get_case_name(self):
        if self.is_bankruptcy:
            # Check if there is somebody described as a debtor
            try:
                return [p for p in self.parties if
                        p[u'type'] == u'Debtor' or
                        p[u'type'] == u'Debtor In Possession'][0][u'name']
            except IndexError:
                pass

            # This is probably a sub docket to a larger case. Use that title.
            try:
                path = u'//i[contains(., "Lead BK Title")]/following::text()'
                case_name = self.tree.xpath(path)[0].strip()
            except IndexError:
                case_name = u"Unknown Case Title"

            if self.is_adversary_proceeding:
                case_name += u' - Adversary Proceeding'
        else:
            matches = []
            # Skip the last value, it's a concat of all previous values and
            # isn't needed for case name matching.
            for v in self.metadata_values[:-1]:
                m = self.case_name_regex.search(v)
                if m:
                    matches.append(m)
                in_re_m = self.in_re_regex.search(v)
                if in_re_m:
                    matches.append(in_re_m)
            if len(matches) == 1:
                case_name = matches[0].group(1)
            else:
                case_name = u"Unknown Case Title"

        return clean_string(harmonize(case_name))

    def _get_docket_number(self):
        if self.is_bankruptcy:
            docket_number_path = '//font'
            # Uses both b/c sometimes the bankr. cases have a dist-style docket
            # number.
            regexes = [self.docket_number_dist_regex,
                       self.docket_number_bankr_regex]
        else:
            docket_number_path = '//h3'
            regexes = [self.docket_number_dist_regex]
        nodes = self.tree.xpath(docket_number_path)
        string_nodes = [s.text_content() for s in nodes]
        for regex in regexes:
            for s in string_nodes:
                match = regex.search(s)
                if match:
                    return match.group(1)

    def _get_nature_of_suit(self):
        if self.is_adversary_proceeding:
            # Add the next table too, if it contains the nature of suit.
            path = u'//table[contains(., "Nature[s] of")]//tr'
            rows = self.tree.xpath(path)
            nos = []
            for row in rows:
                cell_texts = [force_unicode(s.strip()) for s in
                              row.xpath(u'./td[position() > 2]/text()') if
                              s.strip()]
                if len(cell_texts) > 1:
                    nos.append(' '.join(cell_texts))
            return '; '.join(nos) or ''
        else:
            return self._get_value(self.nos_regex)

    def _get_judge(self, regex):
        judge_str = self._get_value(regex)
        if judge_str is not None:
            return normalize_judge_string(judge_str)[0]

    def _get_value(self, regex, cast_to_date=False):
        """Find the matching value for a regex.

        Iterate over a list of values and return group(1) for the first that
        matches regex. If none matches, return the empty string.

        If cast_to_date is True, convert the string to a date object.
        """
        for v in self.metadata_values:
            m = regex.search(v)
            if m:
                if cast_to_date:
                    return convert_date_string(m.group(1))
                hit = m.group(1)
                if "date filed" not in hit.lower():
                    # Safety check. Sometimes a match is made against the merged
                    # text string, including its headers. This is wrong.
                    return hit

        if cast_to_date:
            return None
        else:
            return ''

    @staticmethod
    def _br_split(element):
        """Split the text of an element on the BRs.

        :param element: Any HTML element
        :return: A list of text nodes from that element split on BRs.
        """
        sep = u'FLP_SEPARATOR'
        html_text = tostring(element, encoding='unicode')
        html_text = re.sub(r'<br/?>', sep, html_text, flags=re.I)
        element = fromstring(html_text)
        text = force_unicode(' '.join(s for s in element.xpath('.//text()')))
        return [s.strip() for s in text.split(sep) if s]
