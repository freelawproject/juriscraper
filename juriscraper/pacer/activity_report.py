"""Parse the DktActivityRpt.pl ("Docket Activity Report") results.
A parser for PACER's Docket Activity Report that results as JSON.
"""
import pprint
import sys

from six.moves import range

from .docket_report import BaseDocketReport
from .reports import BaseReport
from ..lib.log_tools import make_default_logger
from ..lib.string_utils import clean_string, force_unicode, harmonize
from ..lib.utils import clean_court_object

logger = make_default_logger()


class ActivityReport(BaseDocketReport, BaseReport):
    """
    Parse the DktActivityRpt.pl ("Docket Activity Report") results.
    """
    PATH = 'cgi-bin/DktActivityRpt.pl'

    CACHE_ATTRS = ['metadata']

    def __init__(self, court_id, pacer_session=None):
        super(ActivityReport, self).__init__(court_id, pacer_session)
        # Initialize the empty cache properties
        self._clear_caches()
        self._metadata = None

    def parse(self):
        self._clear_caches()
        print(self)
        super(ActivityReport, self).parse()

    @property
    def metadata(self):
        if self._metadata is not None:

            return self._metadata

        # The data we're after look like this (re-spacing):
        #
        # <table width="98%" border="1">
    	# 	<tbody>
        #      <tr>
        #           <td align="center"><b>Case Number/Title</b></td>
        # 			<td align="center"><b>Dates</b></td>
        # 			<td align="center"><b>Category/<br>Event</b></td>
        # 			<td align="center"><b>Docketed by</b></td>
        # 			<td align="center"><b>Notes</b></td>
    	# 		</tr>
    	# 	    <tr>
        #             <td valign="top"><a href="https://ecf.azd.uscourts.gov/cgi-bin/DktRpt.pl?1224854">4:20-po-20403-EJM <br>USA v. Lopez-Domingo<br></a><b><font size="-1"> CASE CLOSED on 01/10/2020</font></b></td>
        #             <td valign="top"><i>Entered: </i>01/13/2020 <br>15:25:21<br><i>Filed: </i>01/13/2020</td>
        #             <td valign="top"><i>Category:</i> order-cr<br><i>Event:</i> OSL Order - Petty Cases Only<br><i>Document: </i><a href="https://ecf.azd.uscourts.gov/doc1/025121588988" onclick="goDLS(&#39;/doc1/025121588988&#39;,&#39;1224855&#39;,&#39;5&#39;,&#39;&#39;,&#39;&#39;,&#39;1&#39;,&#39;&#39;,&#39;&#39;);return(false);">1</a></td>
        #             <td valign="top">BAC<br>
        #             <i>Type: </i>crt</td>
        #             <td valign="top"><i>Office:</i> Tucson Division
        #             <br><i>Presider: </i>Eric J Markovich
        #             <br><i>Case Flags:</i> <span>OSFLP</span>
        #             </td>
        #         </tr>
        #         <tr>
        #             <td valign="top"><a href="https://ecf.azd.uscourts.gov/cgi-bin/DktRpt.pl?1224773">4:20-po-20404-EJM <br>USA v. Reyes-Lopez<br></a><b><font size="-1"> CASE CLOSED on 01/10/2020</font></b></td>
        #             <td valign="top"><i>Entered: </i>01/13/2020 <br>08:53:20<br><i>Filed: </i>01/13/2020</td>
        #             <td valign="top"><i>Category:</i> order-cr<br><i>Event:</i> OSL Order - Petty Cases Only<br><i>Document: </i><a href="https://ecf.azd.uscourts.gov/doc1/025121585462" onclick="goDLS(&#39;/doc1/025121585462&#39;,&#39;1224774&#39;,&#39;5&#39;,&#39;&#39;,&#39;&#39;,&#39;1&#39;,&#39;&#39;,&#39;&#39;);return(false);">1</a></td>
        #             <td valign="top">ARC<br>
        #             <i>Type: </i>crt</td>
        #             <td valign="top"><i>Office:</i> Tucson Division
        #             <br><i>Presider: </i>Eric J Markovich
        #             </td>
        #         </tr>
        #         <tr>
        #             <td valign="top"><a href="https://ecf.azd.uscourts.gov/cgi-bin/DktRpt.pl?1224861">4:20-po-20410-EJM <br>USA v. Florentino-Cano<br></a><b><font size="-1"> CASE CLOSED on 01/10/2020</font></b></td>
        #             <td valign="top"><i>Entered: </i>01/13/2020 <br>15:45:25<br><i>Filed: </i>01/13/2020</td>
        #             <td valign="top"><i>Category:</i> order-cr<br><i>Event:</i> OSL Order - Petty Cases Only<br><i>Document: </i><a href="https://ecf.azd.uscourts.gov/doc1/025121589269" onclick="goDLS(&#39;/doc1/025121589269&#39;,&#39;1224862&#39;,&#39;5&#39;,&#39;&#39;,&#39;&#39;,&#39;1&#39;,&#39;&#39;,&#39;&#39;);return(false);">1</a></td>
        #             <td valign="top">BAR<br>
        #             <i>Type: </i>crt</td>
        #             <td valign="top"><i>Office:</i> Tucson Division
        #             <br><i>Presider: </i>Eric J Markovich
        #             </td>
        #         </tr>
        #     </tbody>
        # </table>

        data = []

        table = self.tree.xpath('//table')[0]

        rows = table.xpath('.//tr')

        for b, row in enumerate(rows):

            cols = row.xpath('.//node()')

            def isFlags(cols):
                #Check for case flags. It's not always present.
                try:
                    cols.index('Case Flags:')
                except ValueError:
                    flag = "none"
                    return flag
                else:
                    flag = cols[cols.index('Case Flags:')+3]
                    return flag

            flags = isFlags(cols)

            if b > 0: # skip first
                data.append({
                    u"case":cols[2],
                    u"case_number":cols[4],
                    u"docket_report_url":cols[1].xpath('@href')[0],
                    u"entered": cols[cols.index('Entered: ')+1],
                    u"time": cols[cols.index('Entered: ')+3],
                    u"filed": cols[cols.index('Filed: ')+1],
                    u"closed": cols[8],
                    u"event": cols[cols.index('Event:')+1],
                    u"case_flags": flags,
                    u"category": cols[cols.index('Category:')+1],
                    u"presider": cols[cols.index('Presider: ')+1],
                    u"office": cols[cols.index('Office:')+1],
                    u"docketed_by":cols[cols.index('Document: ')+5],
                    u"doc1":cols[cols.index('Document: ')+1].xpath('@href')[0],
                    u"doc_count":cols[cols.index('Document: ')+2]

                })


        self._metadata = data
        return data

    def query(self, open, closed, office, type, start, end, text):
        """
         closed = 'on' or ''
         open = 'on' or ''

         office = 4
         options:
        <option value="2">Phoenix Division</option>
        <option value="3">Prescott Division</option>
        <option value="4">Tucson Division</option>


        type = 'po'
        options:
        <select name="case_type" multiple="" size="3">
        <option selected=""></option>
        <option value="cv">Civil</option>
        <option value="cr">Criminal</option>
        <option value="em">Emergency Matter</option>
        <option value="mj">Magistrate Judge</option>
        <option value="mc">Miscellaneous</option>
        <option value="md">Multi-District Litigation</option>
        <option value="nr">Non Reportable</option>
        <option value="nc">Non-Compliance</option>
        <option value="po">Petty Offense</option>
        <option value="ph">Pro Hac Vice Case</option>
        <option value="pt">Probation Transfer</option>
        <option value="ps">Prose Screening</option>
        <option value="sc">Sealed Civil</option>
        <option value="sm">Sealed Miscellaneous</option>
        <option value="mb">Search Warrant</option>
        <option value="sa">Staff Attorney Assignment</option>
        <option value="at">Temporary Case Type</option>
        <option value="vc">Virtual CR Case for 3rd Judge</option>
        <option value="wi">Waiver of Indictment</option>
        <option value="wt">Wire Tap</option>
        <option value="gj">~Grand Jury</option>
        </select>

        start = 'm/d/yyyy'
        end = 'm/d/yyyy'

        text = 'summary' or 'full'
        """

        assert self.session is not None, \
            "session attribute of DocketReport cannot be None."

            #Example:
            # One note, when open_cases is not checked in the form,
            # it does not appear as form data in the header.
            # u'all_case_ids': '0'
            # u'case_num': ''
            # u'closed_cases': 'on'
            # u'office': '4'
            # u'case_type': 'po'
            # u'event_category':''
            # u'case_flags': ''
            # u'filed_from': '1/13/2020'
            # u'filed_to': '1/13/2020'
            # u'date_range_limit': ''
            # u'docket_text': 'summary'
            # u'sort1': 'case number'

        params = {
            u'all_case_ids': '0',
            u'case_num': '',
            u'open_cases': open,
            u'closed_cases': closed,
            u'office': office,
            u'case_type': type,
            u'event_category':'' ,
            u'case_flags': '',
            u'filed_from': start,
            u'filed_to': end,
            u'date_range_limit': '',
            u'docket_text': text,
            u'sort1': 'case number'
        }


        logger.info(u"Running activity report from '%s' to '%s'", (start, end) )
        logger.info(self.url)
        self.response = self.session.post(self.url + '?1-L_1_0-1', data=params)
        logger.info(u"Response: %s", self.response)

        self.parse()

    @property
    def data(self):
        """Get all the data back from this endpoint.
        Don't attempt to return parties or docket_entries like the superclass
        does.
        """
        if self.is_valid is False:
            return {}

        data = list(self.metadata)
        return data


def _main():
    if len(sys.argv) != 2:
        print("Usage: python -m juriscraper.pacer.case_query filepath")
        print("Please provide a path to an HTML file to parse.")
        sys.exit(1)

    # Court ID is only needed for querying. Actual
    # parsed value appears in output
    report = ActivityReport('mad')
    filepath = sys.argv[1]
    print("Parsing HTML file at %s" % filepath)
    with open(filepath, 'r') as f:
        text = f.read().decode('utf-8')
    report._parse_text(text)
    pprint.pprint(report.data, indent=2)


if __name__ == "__main__":
    _main()
