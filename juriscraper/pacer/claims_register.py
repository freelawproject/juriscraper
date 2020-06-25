# coding=utf-8
import re
import urlparse

from juriscraper.pacer.reports import BaseReport
from .docket_report import BaseDocketReport
from .utils import get_pacer_doc_id_from_doc1_url
from ..lib.log_tools import make_default_logger
from ..lib.string_utils import convert_date_string, force_unicode, harmonize
from ..lib.utils import clean_court_object

logger = make_default_logger()


class ClaimsRegister(BaseDocketReport, BaseReport):
    """Query and parse the claims registry.

    This is the most naive version of this parser possible. It does not support
    *any* variation to the table, and assumes that the table is *always*
    queried in the same way, using the default options. Because this table is
    not uploaded by RECAP, we do not need to support all the possible versions,
    only those that we need for a particular client job. Enhancements welcome
    to make it more flexible on the parsing and featureful on the querying.
    """

    PATH = "cgi-bin/SearchClaims.pl"
    CACHE_ATTRS = ["claims", "metadata"]
    ERROR_STRINGS = BaseReport.ERROR_STRINGS + [
        "No claims found for this case using selection criteria entered"
    ]

    def __init__(self, court_id, pacer_session=None):
        BaseDocketReport.__init__(self, court_id)
        BaseReport.__init__(self, court_id, pacer_session)

        self._clear_caches()
        self._metadata = None
        self._claims = None
        assert court_id.endswith(
            "b"
        ), "Unable to create object. Must use bankruptcy court abbreviation."

    @property
    def data(self):
        """Get all the data back from this endpoint."""
        if self.is_valid is False:
            return {}
        data = self.metadata.copy()
        data["claims"] = self.claims
        return data

    @property
    def metadata(self):
        if self.is_valid is False:
            return {}

        if self._metadata is not None:
            return self._metadata

        data = {
            "court_id": self.court_id,
        }
        field_mappings = {
            "case_name": "case_name",
            "case_number": "docket_number",
            "chapter": "chapter",
            "closed": "date_closed",
            "converted": "date_converted",
            "date_filed": "date_filed",
            "debtor_dismissed": "date_debtor_dismissed",
            "judge": "assigned_to_str",
            "office": "office",
            "trustee": "trustee_str",
            "last_date_to_file_claims": "date_last_to_file_claims",
            "last_date_to_file_govt": "date_last_to_file_govt",
        }
        # The title row has some weird labels that look like:
        #  <span class="label">Closed</span> 10/26/2018
        label_nodes = self.tree.xpath('//span[@class="label"]')
        for label_node in label_nodes:
            data.update(
                self._get_label_value_pair(label_node, False, field_mappings)
            )

        # Each cell in the header table has a value like:
        # <td><b>Judge:</b>  Barbara J. Houser</td>
        cells = self.tree.xpath("//center/p/table[1]//td[text()]")
        for cell in cells:
            label_node = cell.xpath("./b")[0]
            data.update(
                self._get_label_value_pair(label_node, True, field_mappings)
            )

        # Finally, do the cells in the footer area. These look like:
        # <b>Case Name:</b> Scottish Holdings, Inc. <br>
        label_nodes = self.tree.xpath("//center/b")
        for label_node in label_nodes:
            data.update(
                self._get_label_value_pair(label_node, True, field_mappings)
            )

        data["docket_number"] = self._clean_docket_number(
            data.get("docket_number", "")
        )

        data["case_name"] = harmonize(data["case_name"])
        data = clean_court_object(data)
        self._metadata = data
        return data

    def _clean_docket_number(self, docket_number):
        """Strip the judge initials off docket numbers, and do any other
        similar cleanup.

        :param: docket_number: A string docket number to clean.
        """
        # Uses both b/c sometimes the bankr. cases have a dist-style docket
        # number.
        regexes = [
            self.docket_number_dist_regex,
            self.docket_number_bankr_regex,
        ]
        for regex in regexes:
            match = regex.search(docket_number)
            if match:
                return match.group(1)

        # Fail safe
        return docket_number

    @property
    def claims(self):
        """Parse out all the claims information"""
        if self._claims is not None:
            return self._claims

        claim_tables = self.tree.xpath('//table[@class="complexReport"]')
        claims = []
        for claim_table in claim_tables:
            claim = {}

            # Identify and parse each cell.
            creditor_td = claim_table.xpath("(.//tr)[1]/td[1]")[0]
            claim.update(self._parse_creditor_cell(creditor_td))

            claim_number_td = claim_table.xpath("(.//tr)[1]/td[2]")[0]
            claim.update(self._parse_claim_number_cell(claim_number_td))

            claim_metadata_td = claim_table.xpath("(.//tr)[1]/td[3]")[0]
            claim.update(self._parse_claim_metadata_cell(claim_metadata_td))

            amounts_td = claim_table.xpath("(.//tr)[2]/td[1]")[0]
            claim.update(self._parse_amounts_cell(amounts_td))

            # Paths here are a bit more complex because the amounts table above
            # contains a table, so we can't just get trs by index anymore.
            history_path = './/tr[.//i[text() = "History:"]]'
            history_td = claim_table.xpath(history_path)[0]
            claim["history"] = self._parse_history_cell(history_td)

            description_path = './/i[text() = "Description:"]'
            description_node = claim_table.xpath(description_path)[0]
            claim.update(
                self._get_label_value_pair(
                    description_node, True, {"Description": "description"}
                )
            )

            remarks_path = './/i[text() = "Remarks:"]'
            remarks_td = claim_table.xpath(remarks_path)[0]
            claim.update(
                self._get_label_value_pair(
                    remarks_td, True, {"remarks": "remarks"}
                )
            )

            claims.append(claim)

        self._claims = claims
        return claims

    def _parse_creditor_cell(self, td):
        """Get creditor_id, creditor_details"""
        credit_label = td.xpath(".//i")[0]
        info = self._get_label_value_pair(
            credit_label, True, {"creditor": "creditor_id"}
        )
        info["creditor_id"] = info["creditor_id"].strip("()")

        # Redelimit the <br> tags, then use newlines to join everything but the
        # first line in the cell, and the "Claimant History" link if applicable
        better_td = self.redelimit_p(td, self.BR_REGEX)
        good_text = [s.strip() for s in better_td.xpath(".//p/text()")[1:]]
        info["creditor_details"] = "\n".join(good_text).strip()

        return info

    def _parse_claim_number_cell(self, td):
        """Get the claim_number and date fields"""
        data = {}
        claim_number_text = td.xpath(".//b")[0].text_content()
        claim_number = int(re.search("\d+", claim_number_text).group(0))
        data["claim_number"] = claim_number

        labels = td.xpath(".//i")
        fields = {
            "original_filed_date": "date_original_filed",
            "original_entered_date": "date_original_entered",
            "last_amendment_filed": "date_last_amendment_filed",
            "last_amendment_entered": "date_last_amendment_entered",
        }
        for label in labels:
            data.update(self._get_label_value_pair(label, False, fields))
        return data

    def _parse_claim_metadata_cell(self, td):
        """Get the status, filed_by, entered_by, date_modified fields"""
        labels = td.xpath(".//i")
        data = {}
        fields = {
            "modified": "date_modified",
        }
        for label in labels:
            data.update(self._get_label_value_pair(label, True, fields))
        return data

    @staticmethod
    def _parse_amounts_cell(td):
        """Get the amounts claimed/secured/etc."""
        # These fields are tricky. They come in a table like this:
        #  | Amount  | Claimed: | $49.00
        #  | Secured | Claimed: | $49.00
        # We go row by row.
        fields = {
            "Amount": "amount_claimed",
            "Secured": "secured_claimed",
            "Priority": "priority_claimed",
            "Unsecured": "unsecured_claimed",
            "Admin": "admin_claimed",
            "Unknown": "unknown_claimed",
        }
        rows = td.xpath(".//tr")
        data = {}
        for row in rows:
            # The first cell sets the field name
            label = row.xpath(".//td[1]")[0].text_content().strip()
            if not label:
                # There's an empty row; ignore it.
                continue
            label = fields[label]
            value = row.xpath(".//td[3]")[0].text_content().strip()
            data[label] = value
        return data

    def _parse_history_cell(self, td):
        """Parse the history table.

        This is similar to a mini-docket entries table, but it has a mixture of
        claims documents (with their own numbering scheme), and normal docket
        entries.
        """
        history_rows = []
        entry_trs = td.xpath(".//tr")
        for entry_tr in entry_trs:
            row = {}
            number_cell = entry_tr.xpath("./td[3]")[0]
            number = number_cell.text_content().strip()

            """
            Four kinds of entry formats:

            Claim
             - Number format: 7-1
             - Link: /cgi-bin/show_doc.pl?caseid=171908&claim_id=15151763&claim_num=7-1&magic_num=MAGIC

             Claim 2:
              - Number format: 7-1
              - Link: /doc1/072035305573?caseid=671949&claim_id=34489904&claim_num=28-1&magic_num=MAGIC&pdf_header=1

            Docket entry:
             - Number format: 287
             - Link: /cgi-bin/show_doc.pl?caseid=171908&de_seq_num=981&dm_id=15184563&doc_num=287

             Docket entry 2:
              - Number format: 7-1
              - Link: /doc1/150014580417
            """
            try:
                href = number_cell.xpath(".//a/@href")[0]
            except IndexError:
                href = None

            if "-" in number:
                nums = [int(v) for v in number.split("-")]
                row["document_number"] = nums[0]
                row["attachment_number"] = nums[1]
            else:
                try:
                    row["document_number"] = int(number)
                except ValueError:
                    # Minute entry
                    row["document_number"] = None

            if href and "claim_id" in href:
                row["type"] = "claim"
            else:
                row["type"] = "docket_entry"

            # Next do the URL parsing for whatever is in it (if we have a URL)
            if href and row["document_number"] is not None:
                if "doc1" in href:
                    row["pacer_doc_id"] = get_pacer_doc_id_from_doc1_url(href)

                try:
                    qs = href.rsplit("?")[1]
                except IndexError:
                    pass
                else:
                    qs_dict = urlparse.parse_qs(qs)
                    if row["type"] == "claim":
                        row["id"] = qs_dict["claim_id"][0]
                        row["pacer_case_id"] = qs_dict["caseid"][0]
                    elif row["type"] == "docket_entry":
                        # Unfortunately, no doc1 value. There is a dm_id, which I'm
                        # not familiar with, but I'm not sure what it does, and we
                        # lack a field for it in our DB.
                        row["pacer_seq_no"] = qs_dict["de_seq_num"][0]
                        row["pacer_case_id"] = qs_dict["caseid"][0]
                        row["pacer_dm_id"] = qs_dict["dm_id"][0]

            # Date
            date_cell = entry_tr.xpath("./td[4]")[0]
            row["date_filed"] = convert_date_string(date_cell.text_content())

            # Description
            desc_cell = entry_tr.xpath("./td[5]")[0]
            row["description"] = force_unicode(
                desc_cell.text_content().strip()
            )
            history_rows.append(row)
        return history_rows

    def query(
        self, pacer_case_id, docket_number, date_start=None, date_end=None
    ):
        """Query the claims register and return the results.

        :param pacer_case_id: The internal PACER ID for the case
        :type pacer_case_id: str
        :param date_start: The earliest claim entry you wish to have. Default
        is 1960-01-01 (before anything was put in PACER)
        :type date_start: date
        :param date_end: The latest claim entry you with to have. Default is
        tomorrow.
        :type date_end: date
        :param docket_number: A docket number to look up. Something like
        2:17-bk-39239.
        :type: str
        :return: request response object
        """
        assert (
            self.session is not None
        ), "session attribute of ClaimsRegister cannot be None."

        params = {
            "all_case_ids": pacer_case_id,
            # Whether to filter by filed date or entered date. Parser only
            # currently supports filed date.
            "EntFil": "Fil",
            "SearchingClaims": "true",
            "f_sort1": "cl_claimno",
            "f_sort2": "cl_dt_filed",
            # This field seems to be required while 'all_case_ids' is not.
            "case_num": docket_number,
        }
        if date_start:
            params["f_fromdt"] = date_start.strftime(u"%m/%d/%Y")
        else:
            # Set the default
            params["f_fromdt"] = "1/1/1960"
        if date_end:
            params["f_todt"] = date_end.strftime(u"%m/%d/%Y")

        logger.info(
            "Querying claims register for case ID '%s' in court '%s' "
            "with params %s",
            pacer_case_id,
            self.court_id,
            params,
        )
        self.response = self.session.post(self.url + "?1-L_1_0-1", data=params)
        self.parse()
