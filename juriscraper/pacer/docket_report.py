from juriscraper.lib.log_tools import make_default_logger

logger = make_default_logger()


class DocketReport(object):
    def __init__(self, court_id, pacer_session):
        self.court_id = court_id
        self.session = pacer_session
        super(DocketReport, self).__init__()

    @property
    def url(self):
        if self.court_id == 'psc':
            return 'https://dcecf.psc.uscourts.gov/cgi-bin/DktRpt.pl'
        else:
            return 'https://ecf.%s.uscourts.gov/cgi-bin/DktRpt.pl' % self.court_id

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

        return self.session.post(self.url + '?1-L_1_0-1',
                                 data=query_params,
                                 timeout=300)
