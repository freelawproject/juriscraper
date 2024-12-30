import json
import pprint
import re
import sys
from collections import OrderedDict

from ..lib.html_utils import strip_bad_html_tags_insecure
from ..lib.log_tools import make_default_logger
from ..lib.string_utils import convert_date_string
from .appellate_docket import AppellateDocketReport

logger = make_default_logger()


class ACMSDocketReport(AppellateDocketReport):
    """Parse ACMS docket JSON."""

    def __init__(self, court_id, pacer_session=None):
        super().__init__(court_id, pacer_session)
        self._acms_json = None

    def _parse_text(self, text):
        """Store the ACMS JSON

        This does not, in fact, actually *parse* the data, it
        stores it for subsequent parsing, which happens in
        data(), parties(), and docket_entries().

        :param text: A unicode object
        :return: None
        """
        self._acms_json = json.loads(text)

    @property
    def metadata(self):
        """Metadata is the basis returned by BaseDocketReport's data property.

        That function then supplements it with parties and docket entries.
        """

        caseDetails = self._acms_json["caseDetails"]

        data = {
            "court_id": self.court_id,
            "pacer_case_id": caseDetails["caseId"],
            "docket_number": caseDetails["caseNumber"],
            "case_name": caseDetails["name"],
            "date_filed": convert_date_string(caseDetails["caseOpened"]),
            "appeal_from": caseDetails["court"]["name"],
            "fee_status": caseDetails["feeStatus"],
        }

        # originating_court_infomation, see AppellateDocketReport
        ogc_info = {}

        # Surprisingly, we lack the lower court docket number. (!)

        # At the moment, we lack a good way to turn the contents of the `court`
        # JSON Object into a `court_id`. Nor the `districtCourtName`
        # so for now, return these things:
        #
        # court: { name: "E.D.N.Y. (BROOKLYN)",
        #          identifier: "E.D.N.Y. BROOKLYN)" }
        # court:  { name: "S.D.N.Y. (WHITE PLAINS)",
        #           identifier: "S.D.N.Y. (WHITE PLAINS)" }
        # court: { name: "S.D.N.Y . (NEW YORK CITY)",
        #          identifier: "S.D.N.Y. (NEW YORK CITY)" }
        # districtCourtName: "San Francisco Northern California"
        # districtCourtName: "Los Angeles Central California"
        if caseDetails["court"]:
            court = caseDetails["court"]
            if "name" in court:
                ogc_info["name"] = court["name"]
            if "identifier" in court:
                ogc_info["identifier"] = court["identifier"]
        if caseDetails["districtCourtName"]:
            ogc_info["name"] = caseDetails["districtCourtName"]

        if caseDetails["aNumber"]:
            ogc_info["RESTRICTED_ALIEN_NUMBER"] = caseDetails["aNumber"]

        if ogc_info:
            data["originating_court_information"] = ogc_info

        # Comma-seperated list of non-null case types, subtypes, &c.
        case_type_keys = ["caseType", "caseSubType", "caseSubSubType"]
        case_types = [caseDetails[_] for _ in case_type_keys if caseDetails[_]]
        data["case_type_information"] = ", ".join(case_types)

        # This is unwise and unreasonably general, cf. lib/utils.py
        # # data = clean_court_object(data)

        return data

    @property
    def parties(self):
        """Parse and return a dict of party/atty info.

        This parses the HTML embeded in the docket entry JSON provided
        by ACMS.
        """

        # Simple example HTML, from ca2 23-7222
        _ = (
            """
<table width='100%'>
<tr>
  <td width='30%' style='padding-bottom: 20px;'>
    UNITED STATES OF AMERICA<br>
    &nbsp;&nbsp;&nbsp;&nbsp;AppelleeUSA, """
            + """
  </td><td style='padding-bottom: 20px;'>
    <div style='margin-bottom: 10px'>Won S. Shin, Assistant U.S. Attorney
    <br>Email: won.shin@usdoj.gov
    <br>[US Attorney]
    <br>United States Attorney's Office for the Southern District of New York
    <br>One Saint Andrew's Plaza
    <br>New York, NY 10007
    </div>
  </td>
</tr><tr>
  <td width='30%' style='padding-bottom: 20px;'> MUSTAPHA RAJI<br>
    &nbsp;&nbsp;&nbsp;&nbsp;AKA Sealed Defendant 1, <br>
    &nbsp;&nbsp;&nbsp;&nbsp;Appellant, """
            + """
  </td><td style='padding-bottom: 20px;'>
    <div style='margin-bottom: 10px'>Jeremy Schneider, -
    <br>Direct: 212-571-5500
    <br>Email: jschneider@rssslaaw.com
    <br>[CJA Appointment]
    <br>Rothman, Schneider, Soloway & Stern, LLP
    <br>100 Lafayette Street
    <br>Suite 501
    <br>New York, NY 10013
    </div>
  </td>
</tr>
</table>
"""
        )

        # Slightly more complicated HTML, also ca2: ca2-23-7246.json
        _ = (
            """
<table width='100%'>
<tr>
  <td width='30%' style='padding-bottom: 20px;'>
     ASCENT PHARMACEUTICALS, INC.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;Petitioner, """
            + """
  </td>
  <td style='padding-bottom: 20px;'>
    <div style='margin-bottom: 10px'>James A. Walden, -<br>
      Direct: 212-335-2031<br>
      Email: jwalden@wmhlaw.com<br>
      [Retained]<br>
      Walden Macht & Haran LLP<br>
      250 Vesey Street<br>
      27th Floor<br>
      New York, NY 10281
    </div>
  </td>
</tr>
<tr>
  <td width='30%' style='padding-bottom: 20px;'>
     UNITED STATES DRUG ENFORCEMENT ADMINISTRATION<br>
    &nbsp;&nbsp;&nbsp;&nbsp;Respondent, """
            + """
  </td>
  <td style='padding-bottom: 20px;'>
    <div style='margin-bottom: 10px'>
      Urja Mittal, -<br>
      Direct: 202-353-4895<br>
      Email: urja.mittal@usdoj.gov<br>
      [US Attorney]<br>
      United States Department of Justice<br>
      Civil Division, Appellate Staff<br>
      950 Pennsylvania Avenue, NW<br>
      Washington, DC 20530
    </div>
    <div style='margin-bottom: 10px'>
      Mark B. Stern, -<br>
      Email: mark.stern@usdoj.gov<br>
      [US Attorney]<br>
      United States Department of Justice<br>
      Civil Division, Office of Immigration Litigation<br>
      950 Pennsylvania Avenue, NW<br>
      Washington, DC 20530
    </div>
  <div style='margin-bottom: 10px'>
     United States Drug Enforcement Administration<br>
  </div>
  </td>
</tr>
<tr>
  <td width='30%' style='padding-bottom: 20px;'>
     UNITED STATES DEPARTMENT OF JUSTICE<br>
    <strong>Terminated:</strong>
    10/06/2023<br>
    &nbsp;&nbsp;&nbsp;&nbsp;Respondent, """
            + """
  </td>
  <td style='padding-bottom: 20px;'>
  <div style='margin-bottom: 10px'>
    Urja Mittal, -<br>
    <strong>Terminated:</strong> 10/06/2023<br>
    Direct: 202-353-4895<br>
    Email: urja.mittal@usdoj.gov<br>
    [US Attorney]<br>
    United States Department of Justice<br>
    Civil Division, Appellate Staff<br>
    950 Pennsylvania Avenue, NW<br>
    Washington, DC 20530
  </div>
  <div style='margin-bottom: 10px'>
    Mark B. Stern, -<br>
    <strong>Terminated:</strong> 10/06/2023<br>
    Email: mark.stern@usdoj.gov<br>
    [US Attorney]<br>
    United States Department of Justice<br>
    Civil Division, Office of Immigration Litigation<br>
    950 Pennsylvania Avenue, NW<br>
    Washington, DC 20530
  </div>
  <div style='margin-bottom: 10px'>
    Benjamin H. Torrance, Assistant U.S. Attorney<br>
    <strong>Terminated:</strong> 10/05/2023<br>
    Email: benjamin.torrance@usdoj.gov<br>
    [US Attorney]<br>
    United States Attorney's Office for the Southern District of New York<br>
    86 Chambers Street<br>
    New York, NY 10007
  </div>
  <div style='margin-bottom: 10px'>
    Lena D Watkins, Trial Attorney<br>
    <strong>Terminated:</strong> 10/05/2023<br>
    Direct: 202-514-8713<br>
    Email: Lena.Watkins@usdoj.gov<br>
    [US Attorney]<br>
    United States Department of Justice<br>
    CRM/Narc. & Dang. Drug. Sec.<br>
    145 N Street, NE<br>
    Second Floor, East W<br>
    Washington, DC 20530
  </div>
  </td>
</tr>
</table>"""
        )

        # HTML is a <table> with <tr> for each party.
        # Within that, the first <td> is the party name.
        # The second <td> is the atty list.
        # Within the atty list, there is one <div> per attorney.

        parties_html = self._acms_json["caseDetails"]["partyAttorneyList"]
        tree = strip_bad_html_tags_insecure(parties_html)
        party_rows = tree.xpath(".//tr")
        parties = []
        for row in party_rows:
            party = OrderedDict()

            (party_left, attorneys_block) = row.xpath(".//td")

            party.update(self._parse_party_left(party_left))

            attorneys = []
            for attorney in attorneys_block:
                _ = self._parse_attorney(attorney)
                # Sometimes there are empty padding lines, e.g.:
                #   <div><p>&nbsp;</p></div>
                # Ignore them.
                attorneys.append(_) if _ else None

            party["attorneys"] = attorneys

            parties.append(party)

        # Assert there is no "SEE ABOVE" in ACMS text, so no need
        # to call `self.normalalize_see_above_attorneys()`
        for party in parties:
            for attorney in party.get("attorneys", []):
                if re.search(r"see\s+above", attorney.get("attorneys", "")):
                    assert "Unexpected SEE ABOVE found in ACMS attorney list"

        return parties

    @property
    def docket_entries(self):
        """Return a dictionary of docket entries

        Format this for courtlistener's `DocketEntry` class
        (as mediated by `add_docket_entry()` in `cl/recap/mergers.py`).
        Unfortunately that class conflates filing and entry dates
        right now.  We do not have filing dates, only entry dates (and
        other dates that do not exist in our model).  Return the entry
        datetime as filing date, as well as continuing to do so for a
        future entry date.

        Unlike other docket parsers, we return this as HTML, as per
        @mlissner it is fine to do so, and there is semantic content
        to the HTML markup we would otherwise lose.

        """

        docket_entries = []
        for row in self._acms_json["docketInfo"]["docketEntries"]:
            _ = """Here's what we have to work with:
{
  "endDate": "2023-10-05",
  "endDateFormatted": "10/05/2023",
  "entryNumber": 19,
  "docketEntryText": "<p>NEW PARTY, Respondent United States Drug Enforcement Administration for United States Department of Justice, SUBSTITUTED. [Entered: 10/05/2023 03:56 PM] [Edited: 10/06/2023 10:51 AM]</p>",
  "docketEntryId": "a6a6d3d6-b863-ee11-be6e-001dd804ed2e",
  "createdOn": "2023-10-05T19:53:24Z",
  "documentCount": 0,
  "pageCount": 0,
  "fileSize": 0,
  "restrictedPartyFilingDocketEntry": false,
  "restrictedDocsAvailable": false,
  "selected": false
},"""

            de = {}
            de["document_number"] = row["entryNumber"]

            # Return HTML, currently unused.
            de["description_html"] = row["docketEntryText"]

            # Convert to plain text
            tree = strip_bad_html_tags_insecure(row["docketEntryText"])
            docket_text = tree.text_content()
            de["description"] = docket_text

            # "...[Entered: 09/27/2023 03:30 PM]"
            # "...[Entered: 10/05/2023 03:56 PM] [Edited: 10/06/2023 10:51 AM]"

            # It's not clear why we need to define the
            # `datetime_entered_regex` so narrowly, can't we just let
            # convert_date_string() call dateutil.parser.parse() and
            # let that fail if it doesn't work?
            # Anyhow, use the existing DATE_REGEX and then it's
            # anything goes for the time.

            # For now, skip the terminal $ anchoring to catch the Edited case.
            # We do not parse and we do ignore the Edited date.
            # # datetime_entered_regex = re.compile(
            # #     r"\[Entered:\s+(%s\s[^]]+)]$" % self.DATE_REGEX
            # # )
            datetime_entered_regex = re.compile(
                r"\[Entered:\s+(%s\s[^]]+)]" % self.DATE_REGEX
            )

            # Here's a lot of circumlocution use _get_value(), provided
            # by the superclass, which can be told to parse `date`s
            # but not `datetime`s. So we have to do it ourselves.
            datetime_str = self._get_value(datetime_entered_regex, docket_text)
            assert (
                datetime_str != ""
            ), "Docket entry's Entered: date should not be null"
            de["date_entered"] = convert_date_string(
                datetime_str, datetime=True
            )

            # Unfortunately, the server expects a `date_filed`,
            # which we don't have, and probably can't get (it's in the
            # NDA though). Although the server also doesn't know that
            # other parsers send it `date_entered` in lieu of
            # `date_filed`, without being so explicit about it. Ugh!
            de["date_filed"] = de["date_entered"]

            de["pacer_doc_id"] = row["docketEntryId"]
            de["page_count"] = row["pageCount"]

            docket_entries.append(de)

        return docket_entries


def _main():
    if len(sys.argv) != 2:
        print("Usage: python -m juriscraper.pacer.acms_docket filepath")
        print("Please provide a path to a JSON file to parse.")
        sys.exit(1)
    # Court ID is only needed for querying.
    report = ACMSDocketReport("ca9")
    filepath = sys.argv[1]
    print(f"Parsing JSON file at {filepath}")
    with open(filepath) as f:
        text = f.read()
    report._parse_text(text)
    pprint.pprint(report.data, indent=2)


if __name__ == "__main__":
    _main()
