from __future__ import print_function

import pprint
import re
import sys

from lxml.html import tostring

from .docket_report import BaseDocketReport
from .reports import BaseReport
from .utils import (
    get_court_id_from_url,
    get_pacer_doc_id_from_doc1_url,
    is_pdf,
)
from ..lib.judge_parsers import normalize_judge_string
from ..lib.log_tools import make_default_logger
from ..lib.string_utils import (
    clean_string,
    convert_date_string,
    force_unicode,
    harmonize,
)
from ..lib.utils import clean_court_object

logger = make_default_logger()


class AppellateDocketReport(BaseDocketReport, BaseReport):
    """Parse appellate dockets.

    These can be particularly detailed and for the most part we parse the data
    and provide it in our output. There are some exceptions:

     1. We don't parse the Prior/Current Cases table.
     2. We don't handle bankruptcy appellate panel dockets (yet)
    """

    docket_number_dist_regex = re.compile(
        r"((\d{1,2}:)?\d\d-[a-zA-Z]{1,4}-\d{1,10})"
    )

    CACHE_ATTRS = ["metadata", "docket_entries"]

    ERROR_STRINGS = BaseReport.ERROR_STRINGS + [
        r"The link to this page may not have originated from within CM/ECF.",
        r'Click on the "Accept Charges and Retrieve" button ONCE at the '
        r"bottom of this page to download the document image.",
        r'<embed width="100%" height="100%" name="plugin" id="plugin"',
        r"Access to the document you are about to view has been restricted.*"
        r"Do not allow it to be seen by unauthorized persons.",
        r'document.location\s*=\s*"https://pacer.login.uscourts.gov',
        r'http-equiv="REFRESH"',
        r"Case Number Not Found</b>",
        r"<title>404 Not Found</title>",
        r"<b>\d+ Documents are attached to this filing</b>",
    ]

    def __init__(self, court_id, pacer_session=None):
        BaseDocketReport.__init__(self, court_id)
        BaseReport.__init__(self, court_id, pacer_session)

        # Initialize the empty cache properties
        self._clear_caches()
        self._metadata = None
        self._parties = None
        self._docket_entries = None

    @property
    def url(self):
        if self.court_id == "psc":
            return (
                "https://dcecf.psc.uscourts.gov/"
                "n/beam/servlet/TransportRoom"
            )
        elif self.court_id in ["ca5", "ca7", "ca11"]:
            return (
                "https://ecf.%s.uscourts.gov/"
                "cmecf/servlet/TransportRoom" % self.court_id
            )
        else:
            return (
                "https://ecf.%s.uscourts.gov/"
                "n/beam/servlet/TransportRoom" % self.court_id
            )

    def query(
        self,
        docket_number,
        show_docket_entries=False,
        show_orig_docket=False,
        show_prior_cases=False,
        show_associated_cases=False,
        show_panel_info=False,
        show_party_atty_info=False,
        show_caption=False,
        date_start=None,
        date_end=None,
        output_format="html",
    ):
        """
        Query PACER to get a docket report.

        For the most part, this is a straightforward report to generate
        according to the parameters below. The report can be generated as
        either HTML (the default) or XML.

        :param docket_number: Required argument indicating the docket number
        you wish to view. Example from ca1 is 10-1095
        :param show_docket_entries: Whether to show docket entries.
        :param show_orig_docket: Whether to show information about the docket
        in the lower court.
        :param show_prior_cases: Whether to show information about the prior
        cases in the lower court.
        :param show_associated_cases: Whether to show information about
        associated cases.
        :param show_panel_info: Whether to show information about the judicial
        panel, if it is available.
        :param show_party_atty_info: Whether to show information about the
        parties and attorneys.
        :param show_caption: Whether to show the full caption. E.g.

            IN RE:  GIFTY R. SAMUELS

            Debtor

            -----------------------------------------------

            GIFTY R. SAMUELS

            Appellant

            v.

            DEUTSCHE BANK NATIONAL TRUST COMPANY, as Trustee of the Argent
            Securities, Inc., Asset-Backed Pass-Through Certificates, Series
            2005-W3

            Appellee

        :param date_start: A filter for the docket entries. Only show entries
        from after this date (inclusive).
        :param date_end: A filter for the docket entries. Only show entries
        before this date (inclusive).
        :param output_format: Either xml or html.
        :return: None, but self.response is set and self.parse() is run

        Some examples of GET and POST requests follow.

        Standard GET request when you click on a docket you want after
        searching for it (this is the "summary" docket):
            Url: https://ecf.ca1.uscourts.gov/n/beam/servlet/TransportRoom?
            Params:
                servlet=CaseSummary.jsp
                caseNum=10-1095
                incOrigDkt=Y
                incDktEntries=Y

        POST that's sent when you request the full docket as HTML:
            Url: https://ecf.ca1.uscourts.gov/n/beam/servlet/TransportRoom
            Params:
                servlet=CaseSummary.jsp
                CSRF=csrf_-3765577682638124700
                caseNum=10-1095
                fullDocketReport=Y
                incOrigDkt=Y
                incPrior=Y
                incAssoc=Y
                incPanel=Y
                incPtyAty=Y
                incCaption=long
                incDktEntries=Y
                dateFrom
                dateTo
                incPdfMulti=Y
                actionType=Run+Docket+Report
            Also works as a GET:
                https://ecf.ca1.uscourts.gov/n/beam/servlet/TransportRoom?servlet=CaseSummary.jsp&CSRF=csrf_-3765577682638124700&caseNum=10-1095&fullDocketReport=Y&incOrigDkt=Y&incPrior=Y&incAssoc=Y&incPanel=Y&incPtyAty=Y&incCaption=long&incDktEntries=Y&dateFrom&dateTo&incPdfMulti=Y&actionType=Run+Docket+Report

        POST that's done by clicking the XML button:
            Url: https://ecf.ca1.uscourts.gov/n/beam/servlet/TransportRoom
            Params:
                All parameters same as above, except...
                outputXML_TXT=XML <-- added
                actionType <-- removed

        POST that's done by clicking the "Accept Charges and Retrieve" button
        that's shown to you *after* you request the XML the first time:
            Url: https://ecf.ca1.uscourts.gov/n/beam/servlet/TransportRoom
            Params:
                All parameters same as above, except...
                confirmCharge=y <-- Added
        """
        assert (
            self.session is not None
        ), u"session attribute of AppellateDocketReport cannot be None."
        assert bool(docket_number), (
            u'docket_number must be a valid value, not "%s"' % docket_number
        )

        if not show_docket_entries and (date_end or date_start):
            raise ValueError(
                u"Cannot set date filtering on docket entries "
                u"while show_docket_entries=False"
            )

        if output_format.lower() not in [u"xml", u"html"]:
            raise ValueError(u"Invalid value for output_format parameter.")

        query_params = {
            u"servlet": u"CaseSummary.jsp",
            u"caseNum": docket_number,
        }
        if show_docket_entries:
            query_params[u"incDktEntries"] = u"Y"
        if show_orig_docket:
            query_params[u"incOrigDkt"] = u"Y"
        if show_prior_cases:
            query_params[u"incPrior"] = u"Y"
        if show_associated_cases:
            query_params[u"incAssoc"] = u"Y"
        if show_panel_info:
            query_params[u"incPanel"] = u"Y"
        if show_party_atty_info:
            query_params[u"incPtyAty"] = u"Y"
        if show_caption:
            query_params[u"incCaption"] = u"long"

        if date_start:
            query_params[u"dateFrom"] = date_start.strftime(u"%m/%d/%Y")
        if date_end:
            query_params[u"dateTo"] = date_end.strftime(u"%m/%d/%Y")

        if output_format.lower() == u"xml":
            query_params[u"outputXML_TXT"] = u"XML"
            query_params[u"confirmCharge"] = u"y"  # Lowercase y.
        elif output_format.lower() == u"html":
            # When doing HTML, we need to do actionType param.
            query_params[u"fullDocketReport"] = u"Y"
            query_params[u"actionType"] = u"Run+Docket+Report"

        logger.info(
            u"Querying appellate docket report for docket number '%s' "
            u"with params %s",
            docket_number,
            query_params,
        )
        self.response = self.session.get(self.url, params=query_params)
        self.parse()

    def parse(self):
        """Parse the item, but be sure to clear the cache before you do so.

        This ensures that if the DocketReport is used to parse multiple items,
        the cache is cleared in between.
        """
        self._clear_caches()
        super(AppellateDocketReport, self).parse()

    def download_pdf(self, pacer_doc_id, pacer_case_id=None):
        """Download a PDF from an appellate court.

        :param pacer_case_id: The case ID for the docket
        :param pacer_doc_id: The document ID for the item.
        :return: request.Response object containing the PDF, if one can be
        found, else returns None.

        This is a functional curl command to get a PDF (though the cookies have
        been changed to protect the innocent):

        curl 'https://ecf.ca1.uscourts.gov/n/beam/servlet/TransportRoom' \
            -H 'Referer: https://external' \
            -H 'Cookie: CMECFASESSIONID=xzy; NextGenCSO=abc;  PacerSession=def' \
            --data 'servlet=ShowDoc&incPdfHeader=Y&incPdfHeaderDisp=Y&dls_id=00116008873&pacer=t' \
            --output test.pdf

        This is done with the following HTML and JavaScript:

        <form name="AccCharge" action="TransportRoom" method="post">
            <input name="servlet" value="ShowDoc" type="hidden">
            <input name="CSRF" value="csrf_-7746865752981737651" type="hidden">
            <input name="incPdfHeader" value="N" type="hidden">
            <input name="incPdfHeaderDisp" value="Y" checked="" type="checkbox">Show PDF Header
            <input name="dls_id" value="00116008873" type="hidden">
            <input name="caseId" value="30442" type="hidden">
            <input name="recp" value="" type="hidden"><input name="pacer" value="t" type="hidden">
            <input value="Accept Charges and Retrieve" onclick="doSubmit()" type="button">
        </form>

        var today = new Date();
        function doSubmit() {
            document.AccCharge.recp.value=today.getTime()+"";

            if (document.forms[0].incPdfHeaderDisp.checked) {
                document.forms[0].incPdfHeader.value = 'Y';
            } else {
                document.forms[0].incPdfHeader.value = 'N';
            }

            document.AccCharge.submit();
        }

        Note that although the recp parameter is created by the JS, and so you
        might think it's important, it doesn't seem to do anything that we've
        identified and so is ignored below.
        # noqa
        """
        assert (
            self.session is not None
        ), u"session attribute of AppellateDocketReport cannot be None."
        query_params = {
            u"servlet": u"ShowDoc",
            u"incPdfHeader": u"Y",
            u"incPdfHeaderDisp": u"Y",
            u"dls_id": pacer_doc_id,
            u"pacer": u"t",  # Not sure what this does, but it's required.
        }
        if pacer_case_id:
            query_params[u"caseId"] = pacer_case_id
        logger.info(
            u"GETting PDF at URL: %s with params: %s", self.url, query_params
        )
        r = self.session.get(self.url, params=query_params)
        r.raise_for_status()
        if is_pdf(r):
            logger.info(
                "Got PDF binary data for document #%s in court %s",
                pacer_doc_id,
                self.court_id,
            )
            return r
        return None

    @property
    def metadata(self):
        if self.is_valid is False:
            return {}

        if self._metadata is not None:
            return self._metadata

        data = {
            u"court_id": self.court_id,
            u"docket_number": self._get_tail_by_regex("Docket #|Case Number"),
            u"case_name": self._get_case_name(),
            u"panel": self._get_panel(),
            u"nature_of_suit": self._get_tail_by_regex("Nature of Suit"),
            u"appeal_from": self._get_tail_by_regex("Appeal From"),
            u"fee_status": self._get_tail_by_regex("Fee Status"),
            u"date_filed": self._get_tail_by_regex("Docketed", True),
            u"date_terminated": self._get_tail_by_regex("Termed", True),
            u"case_type_information": self._get_case_type_info(),
            u"originating_court_information": self._get_originating_court_info(),
        }
        data = clean_court_object(data)
        self._metadata = data
        return data

    # Fields that need to be converted with convert_date_str()
    PARTY_DATE_FIELDS = [u"Terminated"]
    # Translation table from Appellate CMECF party fields schema to
    # juriscaper schema.
    PARTY_FIELDS = {
        u"Terminated": u"date_terminated",
    }

    @property
    def parties(self):
        """Return the party table as HTML.

        Take the first table inside the first table following
        `NEW SECTION - Party/Aty List` and for each non-blank
        `<tr>`, the first `<td>` is the party and the second `<td>`
        is the atty list, with individual attorneys delimited with
        `<br><br>` (which are notional `<p>`s) and lines of an atty
        delimited by `<br>`, where the first line is the name.

        """
        if self._parties is not None:
            return self._parties

        # Grab the rows of the first nested table
        # following the comment defining this section of the report
        path = (
            '//comment()[contains(., "NEW SECTION - Party/Aty List")]/'
            "following-sibling::table[1]//table//tr"
        )

        party_rows = self.tree.xpath(path)

        parties = []
        for row in party_rows:
            cells = row.xpath(".//td")
            party = {}

            # Skip merged cells, such as blank dividers
            if len(cells) < 2:
                continue

            # Format:
            #  <tr><td valign=top width=50%>
            #  THEODORE D'APUZZO, P.A.<BR>
            #  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[...];Petitioner
            # but sometimes there are more fields in there:
            #  <tr>
            #  <td valign=top width=50%>LORETTA E. LYNCH, Attorney General<BR>
            #  <B>Terminated: </B>07/31/2017<BR>
            #  Respondent

            name_role = self.redelimit_p(cells[0], self.BR_REGEX)
            count = len(name_role)
            assert (
                count >= 2
            ), "Expecting 2+ <br>-delimited portions of first cell."

            # Name is first, Role is last
            party[u"name"] = force_unicode(name_role[0].text_content().strip())
            role = name_role[count - 1].text_content().strip()
            # Strip terminal comma, if present.
            role = re.sub(r",$", "", role)
            party[u"type"] = role

            unparsed = []
            for i in range(1, count - 1):
                element = name_role[i]
                #  <B>Terminated: </B>07/31/2017<BR>
                bold = element.find("b")
                if bold is not None:
                    raw_field = bold.text_content().strip()
                    # Remove terminal colon
                    raw_field = re.sub(r":$", "", raw_field)
                    # Translate field name to Juriscraper schema, if it exists
                    if raw_field in self.PARTY_FIELDS:
                        field = self.PARTY_FIELDS[raw_field]
                    else:
                        field = raw_field

                    value = bold.tail
                    if raw_field in self.PARTY_DATE_FIELDS:
                        value = convert_date_string(value)
                    else:
                        value = force_unicode(value)

                    party[field] = value
                else:
                    s = "".join(
                        tostring(e, encoding="unicode") for e in element
                    )
                    unparsed.append(s)

            if unparsed:
                party[u"unparsed"] = unparsed

            attorneys = cells[1]

            # For reference, here's how the XML defines the schema:
            # <attorney firstName="David"
            #    middleName="G."
            #    lastName="Baker"
            #    generation=""
            #    suffix=""
            #    title=""
            #    email=""
            #    fax="866-661-5328"
            #    address1="236 Huntington Ave"
            #    address2=""
            #    address3=""
            #    office=""
            #    unit=""
            #    room=""
            #    businessPhone=""
            #    personalPhone="617-367-4260"
            #    city="Boston"
            #    state="MA"
            #    zip="02115-4701"
            #    terminationDate=""
            #    noticeInfo="[COR NTC Retained]" />

            # Here's the HTML we have to work with. Note that
            # sometimes we have a "Direct:" phone (personalPhone)
            # first, but it can be omitted.  It's followed by the
            # noticeInfo, [bracketed].
            # HTML:
            #   <td width="50%" valign="top">
            #   Nicole Giuliano
            #   <br>Direct: 954-848-2940
            #   <br>[COR LD NTC Retained]
            #   <br>Giuliano Law, PA
            #   <br>500 E BROWARD BLVD STE 1710
            #   <br>FT LAUDERDALE, FL 33394
            #   <br>
            #   <br>
            #   Morgan L. Weinstein
            #   <br>[COR NTC Retained]
            #   <br>Law Office of Morgan L. Weinstein
            #   <br>Firm: 954-540-2755
            #   <br>5216 VAN BUREN ST
            #   <br>HOLLYWOOD, FL 33021
            #   </td>

            # We fixup the raw HTML by separating attorneys into <p>
            # elements, replacing <br><br> pairs.
            attorney_rows = self.redelimit_p(
                attorneys, r"(?i)<br\s*/?><br\s*/?>"
            )
            attorneys = []
            for attorney_row in attorney_rows:
                attorney = {}
                # Performance note: _br_split() unparses and reparses
                # the element, just as redelimit_p() does above. So
                # it's a bit wasteful to use both.
                attorney_lines = self._br_split(attorney_row)
                # First line is the name
                attorney[u"name"] = attorney_lines.pop(0)
                if not attorney[u"name"]:
                    continue
                roles = []
                contacts = []
                for attorney_line in attorney_lines:
                    # [Bracketted] lines are roles, others are contacts.
                    m = re.match(r"\[(.*)\]", attorney_line)
                    if m:
                        roles.append(m.group(1))
                    else:
                        contacts.append(attorney_line)
                attorney[u"roles"] = roles
                attorney[u"contact"] = u"\n".join(contacts)
                attorneys.append(attorney)

            party[u"attorneys"] = attorneys
            parties.append(party)

        parties = self._normalize_see_above_attorneys(parties)

        self._parties = parties
        return parties

    @property
    def docket_entries(self):
        """Get the docket entries"""
        if self._docket_entries is not None:
            return self._docket_entries

        # If "View Multiple Documents" is checked, there's a form, if not, it's
        # a table. Thus, find all the trs below the first table or form after
        # the comment.
        path = (
            '//comment()[contains(., "DOCKET ENTRIES")]/'
            "following-sibling::*[self::table | self::form]//tr"
        )
        docket_entry_rows = self.tree.xpath(path)

        docket_entries = []
        for row in docket_entry_rows:
            de = {}
            cells = row.xpath(u"./td")
            if len(cells) == 1:
                if cells[0].text_content() == "No docket entries found.":
                    break
                continue

            date_filed_str = force_unicode(cells[0].text_content())
            de[u"date_filed"] = convert_date_string(date_filed_str)
            de[u"document_number"] = self._get_document_number(cells[1])
            de[u"pacer_doc_id"] = self._get_pacer_doc_id(cells[1])
            if not de[u"document_number"]:
                if de[u"pacer_doc_id"]:
                    # If we lack the document number, but have
                    # the pacer ID, use it.
                    de[u"document_number"] = de[u"pacer_doc_id"]
                else:
                    # We lack both the document number and the pacer ID.
                    # Probably a minute order. No need to set either.
                    pass
            de[u"description"] = force_unicode(cells[2].text_content())
            docket_entries.append(de)

        docket_entries = clean_court_object(docket_entries)
        self._docket_entries = docket_entries
        return docket_entries

    @staticmethod
    def _get_document_number(cell):
        """Get the document number"""
        text_nodes = cell.xpath(".//text()[not(parent::font)]")
        text_nodes = map(clean_string, text_nodes)
        for text_node in text_nodes:
            if text_node.isdigit():
                return text_node
        return None

    @staticmethod
    def _get_pacer_doc_id(cell):
        urls = cell.xpath(u".//a")
        if not urls:
            # Entry exists but lacks a URL. Probably a minute order or similar.
            return None
        else:
            doc1_url = urls[0].xpath("./@href")[0]
            return get_pacer_doc_id_from_doc1_url(doc1_url)

    def _get_case_name(self):
        """Get the case name."""

        # 1: Find the comment defining this section of the report
        # 2: On its following-sibling axis, take the next table descendant,
        # 3: as long as there is boldface in the first row of the table.
        # 4: Within that table, take the cell that doesn't have any bold.

        path = (
            '//comment()[contains(., "NEW SECTION - Case Stub")]/'  # 1
            "following-sibling::*//table[1]"  # 2
            "[.//tr[1]//b]//"  # 3
            "td[not(.//b)]"
        )  # 4

        case_name = self.tree.xpath(path)[0].text_content()
        return clean_string(harmonize(case_name))

    def _get_panel(self):
        """Get the panel information"""
        path = '//*[re:match(text(), "Panel Assignment")]/ancestor::td[1]'
        try:
            panel_table = self.tree.re_xpath(path)[0]
        except IndexError:
            # No panel table.
            return []

        panel_string = self._get_tail_by_regex("Panel:", node=panel_table)
        if panel_string in ["", "Not available"]:
            return []
        else:
            return panel_string.split()

    def _get_case_type_info(self):
        """Get the case type information and return it as a csv string"""
        path = (
            '//*[re:match(text(), "Case Type Information")]/'
            "ancestor::table[1]//b"
        )
        bold_nodes = self.tree.re_xpath(path)
        case_info = []
        for node in bold_nodes:
            tail = str(node.tail).strip()
            if not any([tail == "None", tail == "null", tail == "-"]):
                case_info.append(node.tail)
        return ", ".join(case_info)

    def _get_originating_court_info(self):
        """Get all of the originating type information as a dict."""
        try:
            ogc_table = self.tree.re_xpath(
                '//*[re:match(text(), "Originating Court Information")]/ancestor::table[1]'  # noqa
            )[0]
        except IndexError:
            # No originating court info.
            return {}

        ogc_info = {}
        docket_number_node_str = ogc_table.re_xpath(
            './/*[re:match(text(), "District")]/ancestor::td[1]'
        )[0].text_content()
        m = self.docket_number_dist_regex.search(docket_number_node_str)
        if m:
            ogc_info[u"docket_number"] = m.group(1)
        else:
            # Regex didn't match. Try another way. Seems to happen
            # when the OGC is a case that wasn't in a normal district
            # court. E.g. BIA.
            #   <B>District: </B>BIA-1 : A999-999-999
            docket_number = docket_number_node_str.split(":")[2].strip()
            ogc_info[u"docket_number"] = docket_number

        # Alien numbers are somewhat like social security numbers for
        # non-citizens, and attorneys generally redact them from
        # public filings. Although FRAP 25(a)(5) / FRCP 5.2(c) only
        # require SSNs and TINs be redacted, it's not great to be
        # sharing Alien Numbers.  Unfortunately, many/most appeals
        # courts list them in the docket metadata, but it would be
        # best not to do so on CL without a paywall.
        #
        # Place them in their own field so we can restrict access to them
        if re.match(r"A[0-9-]+", ogc_info[u"docket_number"]):
            ogc_info[u"RESTRICTED_ALIEN_NUMBER"] = ogc_info.pop(
                u"docket_number"
            )

        try:
            og_court_url = ogc_table.xpath(".//a/@href")[0]
        except IndexError:
            # Happens when dockets don't link to their OGC.
            ogc_info[u"court_id"] = u""
        else:
            ogc_info[u"court_id"] = get_court_id_from_url(og_court_url)

        judge_str = self._get_tail_by_regex("Trial Judge")
        if judge_str:
            ogc_info[u"assigned_to"] = normalize_judge_string(judge_str)[0]

        ogc_info[u"court_reporter"] = self._get_tail_by_regex("Court Reporter")
        ogc_info[u"date_filed"] = self._get_tail_by_regex("Date Filed", True)
        ogc_info[u"date_disposed"] = self._get_tail_by_regex(
            "Date Disposed", True
        )
        ogc_info[u"disposition"] = self._get_tail_by_regex("Disposition")

        trial_judge_str = self._get_tail_by_regex("Trial Judge")
        ogc_info[u"assigned_to"] = normalize_judge_string(trial_judge_str)[0]
        order_judge_str = self._get_tail_by_regex("Ordering Judge")
        ogc_info[u"ordering_judge"] = normalize_judge_string(order_judge_str)[
            0
        ]

        date_labels = ogc_table.xpath(".//tr[last() - 1]/td//text()")
        dates = ogc_table.xpath(".//tr[last()]/td//text()")
        for label, date in zip(date_labels, dates):
            label = clean_string(label)
            date = clean_string(date)
            if label == "Date Order/Judgment:":
                ogc_info[u"date_judgment"] = convert_date_string(date)
            if label == "Date Order/Judgment EOD:":
                ogc_info[u"date_judgment_eod"] = convert_date_string(date)
            # NOA: Notice of appeal
            if label == "Date NOA Filed:":
                ogc_info[u"date_filed_noa"] = convert_date_string(date)
            if label == "Date Rec'd COA:":
                ogc_info[u"date_received_coa"] = convert_date_string(date)
        return ogc_info

    def _get_tail_by_regex(self, regex, cast_to_date=False, node=None):
        """Search all text nodes for a string that matches the regex, then
        return the `tail`ing text.

        :param regex: A regex to search for in all text nodes.
        :param cast_to_date: Whether to convert the resulting text to a date.
        :param node: The node to search. If None, does self.tree.
        :returns unicode object: The tailing string cleaned up and optionally
        converted to a date.
        """
        node = node if node is not None else self.tree
        nodes = node.re_xpath('//*[re:match(text(), "%s")]' % regex)
        try:
            tail = clean_string(nodes[0].tail.strip())
        except (IndexError, AttributeError):
            if cast_to_date:
                return None
            else:
                return ""
        else:
            if cast_to_date:
                return convert_date_string(tail)
            return tail


def _main():
    if len(sys.argv) != 2:
        print("Usage: python -m juriscraper.pacer.appellate_docket filepath")
        print("Please provide a path to an HTML file to parse.")
        sys.exit(1)
    report = AppellateDocketReport(
        "ca9"
    )  # Court ID is only needed for querying.
    filepath = sys.argv[1]
    print("Parsing HTML file at {}".format(filepath))
    with open(filepath, "r") as f:
        text = f.read().decode("utf-8")
    report._parse_text(text)
    pprint.pprint(report.data, indent=2)


if __name__ == "__main__":
    _main()
