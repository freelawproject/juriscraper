# coding=utf-8
import copy
import pprint
import re
import sys

import six
from dateutil.tz import gettz
from lxml import etree
from lxml.html import HtmlElement, fromstring, tostring

from .docket_utils import normalize_party_types
from .reports import BaseReport
from .utils import (
    get_pacer_doc_id_from_doc1_url,
    get_pacer_seq_no_from_doc1_anchor,
)
from ..lib.judge_parsers import normalize_judge_string
from ..lib.log_tools import make_default_logger
from ..lib.string_utils import (
    clean_string,
    convert_date_string,
    force_unicode,
    harmonize,
)
from ..lib.utils import clean_court_object, previous_and_next

logger = make_default_logger()

date_regex = r"[—\d\-–/]+"


class BaseDocketReport(object):
    """A small class to hold functions common to the InternetArchive report
    and the PACER DocketReport

    It might be possible to have the InternetArchive report subclass the
    DocketReport, but that brings a lot of cruft along. Better to have this
    little class as a mixin with the common components.
    """

    date_terminated_regex = re.compile(
        r"[tT]erminated:\s+(%s)" % date_regex, flags=re.IGNORECASE
    )
    docket_number_dist_regex = re.compile(
        r"((\d{1,2}:)?\d\d-[a-zA-Z]{1,4}-\d{1,10})"
    )
    docket_number_bankr_regex = re.compile(r"(?:#:\s+)?((\d-)?\d\d-\d*)")
    docket_number_jpml = re.compile(r"(MDL No.\s+\d*)")

    def __init__(self, court_id):
        self.court_id = court_id
        if self.court_id.endswith("b"):
            self.is_bankruptcy = True
        else:
            self.is_bankruptcy = False

    def _clear_caches(self):
        """Clear any caches that are on the object."""
        for attr in self.CACHE_ATTRS:
            setattr(self, "_%s" % attr, None)

    @property
    def data(self):
        """Get all the data back from this endpoint."""
        if self.is_valid is False:
            return {}

        data = self.metadata.copy()
        data[u"parties"] = self.parties
        data[u"docket_entries"] = self.docket_entries
        return data

    @staticmethod
    def _normalize_see_above_attorneys(parties):
        """PACER frequently has "See above" for the contact info of an
        attorney.

        Normalize these values.
        """
        atty_cache = {}
        for party in parties:
            for atty in party.get(u"attorneys", []):
                if not atty[u"contact"]:
                    continue

                if re.search(r"see\s+above", atty[u"contact"], re.I):
                    try:
                        atty_info = atty_cache[atty[u"name"]]
                    except KeyError:
                        # Unable to find the atty in the cache, therefore, we
                        # don't know their contact info.
                        atty[u"contact"] = u""
                    else:
                        # Found the atty in the cache. Use the info.
                        atty[u"contact"] = atty_info
                else:
                    # We have atty info. Save it.
                    atty_cache[atty[u"name"]] = atty[u"contact"]
        return parties

    def _get_value(self, regex, query_strings, cast_to_date=False):
        """Find the matching value for a regex.

        Iterate over a list of values and return group(1) for the first that
        matches regex. If none matches, return the empty string.

        If cast_to_date is True, convert the string to a date object.
        """
        if isinstance(query_strings, six.string_types):
            query_strings = [query_strings]

        for v in query_strings:
            m = regex.search(v)
            if m:
                if cast_to_date:
                    return convert_date_string(m.group(1))
                hit = m.group(1)
                if "date filed" not in hit.lower():
                    # Safety check. Sometimes a match is made against the
                    # merged text string, including its headers. This is wrong.
                    return hit

        if cast_to_date:
            return None
        else:
            return ""

    @staticmethod
    def _xpath_text_0(node, xpath):
        """Get the first text element from a node or return ''

        This is annoyingly hard with normal xpath.
        """
        try:
            return node.xpath("%s/text()" % xpath)[0]
        except IndexError:
            return ""

    def _get_str_from_tree(self, path):
        try:
            s = self.tree.xpath("%s/text()" % path)[0].strip()
        except IndexError:
            return ""  # Return an empty string. Don't return None.
        else:
            return s

    def _parse_docket_number_strs(self, potential_docket_numbers):
        """Parse docket numbers from a list of potential ones

        :param potential_docket_numbers: Potential docket number unicode
        objects
        :type potential_docket_numbers: list
        :return: The correct docket number
        :rtype: unicode
        """
        if self.is_bankruptcy:
            # Uses both b/c sometimes the bankr. cases have a dist-style docket
            # number.
            regexes = [
                self.docket_number_dist_regex,
                self.docket_number_bankr_regex,
            ]
        else:
            regexes = [self.docket_number_dist_regex, self.docket_number_jpml]
        for regex in regexes:
            for s in potential_docket_numbers:
                match = regex.search(s)
                if match:
                    return match.group(1)

    def get_datetime_from_tree(self, path, cast_to_date=False):
        """Parse a datetime from the XML located at node.

        If cast_to_date is true, the datetime object will be converted to a
        date. Else, will return a datetime object in parsed TZ if possible.
        Failing that, it will assume UTC.
        """
        try:
            s = self.tree.xpath("%s/text()" % path)[0].strip()
        except IndexError:
            return None
        else:
            try:
                d = convert_date_string(s, datetime=True)
            except ValueError:
                logger.debug("Couldn't parse date: %s" % s)
                return None
            else:
                # Set it to UTC.
                d = d.replace(tzinfo=d.tzinfo or gettz("UTC"))
                if cast_to_date is True:
                    return d.date()
                return d

    @staticmethod
    def _br_split(element):
        """Split the text of an element on the BRs.

        :param element: Any HTML element
        :return: A list of text nodes from that element split on BRs.
        """
        sep = u"FLP_SEPARATOR"
        html_text = tostring(element, encoding="unicode")
        html_text = re.sub(r"<br/?>", sep, html_text, flags=re.I)
        html_text = re.sub(r"<p/?>", sep, html_text, flags=re.I)
        element = fromstring(html_text)
        text = force_unicode(" ".join(s for s in element.xpath(".//text()")))
        return [s.strip() for s in text.split(sep) if s]

    BR_REGEX = r"(?i)<br\s*/?>"

    @staticmethod
    def redelimit_p(target_element, delimiter_re):
        """Redelimit the children of the target element with <p> tags.

        Insert a <p> tag immediately after the target tag,
        and then replace the delimeter_re with <p> tags.
        Note that <p> is special because the lxml parser knows it
        it self-closing, so this would not work with arbitrary
        tags.

        Use this to turn:
          <foo>a<br>b<br>c</foo>
        Into the more easily iterable:
          <foo>
            <p>a</p>
            <p>b</p>
            <p>c</p>
          </foo>

        :param target_element: An lxml HtmlElement that will be redelimited
        :param delimiter_re: a re pattern matching the tag to replace, e.g.
        BR_REGEX aka r'(?i)<br\s*/?>'
        for a <br> (with optional space and optional /)
        :returns: The redelimited HtmlElement.
        """
        html_text = tostring(target_element, encoding="unicode")
        html_text = re.sub(r"(?i)^(<[^>]*>)", r"\1<p>", html_text)
        html_text = re.sub(delimiter_re, r"<p>", html_text)
        return fromstring(html_text)

    @staticmethod
    def _get_label_value_pair(node, require_colon, field_mappings):
        """Get the field name and value for a node with a tailed value

        :param node: The node with a tailing value.
        :param require_colon: Whether to check for a colon at the end of a
        field name. If True, labels without a colon are ignored.
        :param field_mappings: A dict mapping PACER labels to Juriscraper ones.
        :return a dict with a k-v mapping between a label and its value.
        """
        label = node.text_content().strip()
        if require_colon and not label.endswith(":"):
            return {}
        if isinstance(label, str):
            label = label.decode("utf-8")

        label = (
            label.strip()
            .lower()
            .replace(" ", "_")
            .replace(u"\xa0", "_")  # Non-breaking space
            .replace("(", "")
            .replace(")", "")
            .rstrip(":")
        )
        label = field_mappings.get(label, label)

        value = node.tail.strip()
        # Sometimes the colon is in the tail instead of in the label.
        value = value.lstrip(":").strip()
        if label.startswith("date_"):
            # Known date field. Parse it.
            if value:
                data = {label: convert_date_string(value)}
            else:
                data = {label: None}
        else:
            data = {label: force_unicode(value)}
        return data


class DocketReport(BaseDocketReport, BaseReport):
    case_name_str = r"(?:Case\s+title:\s+)?(.*\bvs?\.?\s.*)"
    case_name_regex = re.compile(case_name_str)
    case_name_i_regex = re.compile(case_name_str, flags=re.IGNORECASE)
    case_title_regex = re.compile(
        r"(?:Case\s+title:\s+)(.*)", flags=re.IGNORECASE
    )
    in_re_regex = re.compile(r"(\bIN\s+RE:\s+.*)", flags=re.IGNORECASE)
    in_the_matter_regex = re.compile(
        r"(\bIn\s+the\s+matter\s+.*)", flags=re.IGNORECASE
    )
    case_name_regexes = [
        case_name_regex,
        case_name_i_regex,
        case_title_regex,
        in_re_regex,
        in_the_matter_regex,
    ]
    date_filed_regex = re.compile(r"Date [fF]iled:\s+(%s)" % date_regex)
    date_converted_regex = re.compile(
        r"Date [Cc]onverted:\s+(%s)" % date_regex
    )
    # Be careful this does not match "Joint debtor discharged" field.
    date_discharged_regex = re.compile(
        r"(?:Date|Debtor)\s+[Dd]ischarged:\s+(%s)" % date_regex
    )
    assigned_to_regex = r"Assigned to:\s+(.*)"
    referred_to_regex = r"Referred to:\s+(.*)"
    cause_regex = re.compile(r"Cause:\s+(.*)")
    nos_regex = re.compile(r"Nature of Suit:\s+(.*)")
    jury_demand_regex = re.compile(r"Jury Demand:\s+(.*)")
    jurisdiction_regex = re.compile(r"Jurisdiction:\s+(.*)")
    mdl_status_regex = re.compile(r"MDL Status:\s+(.*)")
    demand_regex = re.compile(r"^Demand:\s+(.*)")
    offense_regex = re.compile(
        r"highest\s+offense.*(?P<status>opening|terminated)", flags=re.I
    )
    counts_regex = re.compile(
        r"(?P<status>pending|terminated)\s+counts", flags=re.I
    )
    complaints_regex = re.compile(r"(?P<status>complaints)", flags=re.I)

    PATH = "cgi-bin/DktRpt.pl"

    CACHE_ATTRS = [
        "metadata",
        "parties",
        "docket_entries",
        "is_adversary_proceeding",
    ]

    ERROR_STRINGS = BaseReport.ERROR_STRINGS + [
        "The report may take a long time to run because this case has many "
        "docket entries",
        "The page ID does not exist. Please enter a valid page ID number. ",
        "There are no documents in this case.",
        "Incomplete request. Please try your query again by choosing the "
        "Query or Reports option",
        "To accept charges shown below, click on the 'View Report' button",
        "Unable to create PDF file.",
        "This case was administratively closed",
        "The start date must be less than or equal to the end date",
        "The starting document number must be less than or equal to the "
        "ending document number",
        "Case not found.",
        "Either you do not have permission to view the document, or the "
        "document does not exist in the case.",
        "Format: text",
        "Server timeout waiting for the HTTP request from the client.",
        "The case type was.*but it must be",
        "This case is in the process of being opened, please check back later "
        "for additional information.",
        "Submission already made, please wait for response from server",
    ]

    def __init__(self, court_id, pacer_session=None):
        BaseDocketReport.__init__(self, court_id)
        BaseReport.__init__(self, court_id, pacer_session)

        # Initialize the empty cache properties.
        self._clear_caches()
        self._metadata = None
        self._parties = None
        self._docket_entries = None

    def parse(self):
        """Parse the item, but be sure to clear the cache before you do so.

        This ensures that if the DocketReport is used to parse multiple items,
        the cache is cleared in between.
        """
        self._clear_caches()
        super(DocketReport, self).parse()

    @property
    def metadata(self):
        if self.is_valid is False:
            return {}

        if self._metadata is not None:
            return self._metadata

        self._set_metadata_values()
        data = {
            u"court_id": self.court_id,
            u"docket_number": self._get_docket_number(),
            u"case_name": self._get_case_name(),
            u"date_filed": self._get_value(
                self.date_filed_regex, self.metadata_values, cast_to_date=True
            ),
            u"date_terminated": self._get_value(
                self.date_terminated_regex,
                self.metadata_values,
                cast_to_date=True,
            ),
            u"date_converted": self._get_value(
                self.date_converted_regex,
                self.metadata_values,
                cast_to_date=True,
            ),
            u"date_discharged": self._get_value(
                self.date_discharged_regex,
                self.metadata_values,
                cast_to_date=True,
            ),
            u"assigned_to_str": self._get_judge(self.assigned_to_regex),
            u"referred_to_str": self._get_judge(self.referred_to_regex),
            u"cause": self._get_value(self.cause_regex, self.metadata_values),
            u"nature_of_suit": self._get_nature_of_suit(),
            u"jury_demand": self._get_value(
                self.jury_demand_regex, self.metadata_values
            ),
            u"demand": self._get_value(
                self.demand_regex, self.metadata_values
            ),
            u"jurisdiction": self._get_value(
                self.jurisdiction_regex, self.metadata_values
            ),
            u"mdl_status": self._get_value(
                self.mdl_status_regex, self.metadata_values
            ),
        }
        data = clean_court_object(data)
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
                }],
                'criminal_data': {
                    ...See self._add_criminal_data_to_parties()...
                },
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
            "//tr["
            # Bankruptcy
            "    ./td[1]//i/b/text() or "
            # Regular district
            "    ./td[1]//b/u/text() or "
            # Adversary proceedings
            '    ./td[1]//b/text()[contains(., "-----")]'
            "]/../tr"
        )
        party_rows = self.tree.xpath(path)

        parties = []
        party = {}
        for prev, row, nxt in previous_and_next(party_rows):
            cells = row.xpath(".//td")
            should_continue = self._test_for_early_continues(row, cells, nxt)
            if should_continue:
                continue

            party, should_continue = self._get_party_type(row, cells, party)
            if should_continue:
                continue

            name_path = (
                u".//b[not(./parent::i)][not(./u)]"
                u'[not(contains(., "------"))]'
            )
            is_party_name_cell = len(cells[0].xpath(name_path)) > 0
            prev_has_disposition = (
                prev is not None and "Disposition" in prev.text_content()
            )
            if is_party_name_cell and not prev_has_disposition:
                element = cells[0].xpath(name_path)[0]
                party[u"name"] = force_unicode(element.text_content().strip())
                party[u"extra_info"] = u"\n".join(
                    force_unicode(s.strip())
                    for s in cells[0].xpath(u".//text()[not(./parent::b)]")
                    if s.strip()
                )
                party[u"date_terminated"] = self._get_value(
                    self.date_terminated_regex,
                    party[u"extra_info"],
                    cast_to_date=True,
                )

            if len(cells) == 3 and party != {}:
                party[u"attorneys"] = self._get_attorneys(cells[2])

            if party != {} and party.get(u"type") is None:
                # Ensure that every record has a type value of some kind.
                party[u"type"] = u"Unknown"

            if party not in parties and party != {}:
                # Sometimes there are dups in the docket. Avoid them.
                parties.append(party)

            if self.is_adversary_proceeding:
                # In adversary proceedings, there are multiple rows under one
                # party type header. Nuke the bulk of the party dict, except
                # for the type so that it's ready for the next iteration.
                party = {u"type": party[u"type"]}
            else:
                party = {}

        parties = self._normalize_see_above_attorneys(parties)

        # Do a second pass to get the criminal data if any and attach it to the
        # correct party.
        if not self.is_bankruptcy:
            self._add_criminal_data_to_parties(parties, party_rows)

        self._parties = parties
        return parties

    @staticmethod
    def _test_for_early_continues(row, cells, nxt):
        """Check for opportunities to skip the current row.

        :param row: The tr that we're parsing.
        :param cells: A list of tds within the row.
        :param nxt: The next row after the current one, so we can look ahead in
        it.
        :returns bool: True if there's an opportunity to continue to the next
        iteration in the current loop; False if not.
        """
        if len(cells) == 0:
            # Empty row. Press on.
            return True
        row_text = force_unicode(row.text_content()).strip().lower()
        if not row_text or row_text == "v.":
            # Empty or nearly empty row. Press on.
            return True

        # Handling for criminal cases that put non-party info in the party html
        # table (see cand, 3:09-cr-00418).
        if cells[0].xpath(".//b/u"):
            if nxt is None or not nxt.xpath(".//b"):
                # If a header is followed by a cell that lacks bold text,
                # punt the header row.
                return True
            if len(cells) == 3 and cells[2].text_content() == "Disposition":
                # This row contains count/offense information. Skip it until
                # criminal data is done in a second pass through the rows.
                return True
        elif not row.xpath(".//b"):
            # If a row has no bold text, we can punt it. The bold normally
            # signifies the party's name, or the party type. This ignores
            # the metadata under these sections.
            return True
        return False

    def _get_party_type(self, row, cells, party):
        """Get the party type info and return it as a dict.

        :param row: The tr we're currently processing.
        :param cells: The array of cells in the row.
        :param party: The party dict as it existed before this iteration. If
        no matches happen in this code, we just pass this through.
        :returns A tuple of the party dict with just the type parameter
        completed and a boolean indicating whether the calling function should
        continue its loop.
        """
        row_text = force_unicode(row.text_content()).strip().lower()
        if len(cells) == 1 and cells[0].xpath(".//b/u"):
            # Regular docket - party type value.
            s = force_unicode(cells[0].text_content())
            return {u"type": normalize_party_types(s)}, True
        elif "------" in row_text:
            # Adversary proceeding
            s = force_unicode(cells[0].text_content().strip())
            if len(cells) == 1:
                s = re.sub(u"----*", "", s)
                return {u"type": normalize_party_types(s)}, True
            elif len(cells) == 3:
                # Some courts have malformed HTML that requires extra work.
                return {u"type": re.split(u"----*", s)[0]}, False
        elif all(
            [self.is_bankruptcy, len(cells) == 3, cells[0].xpath(".//i/b")]
        ):
            # Bankruptcy - party type value.
            s = force_unicode(cells[0].xpath(u".//i")[0].text_content())
            return {u"type": normalize_party_types(s)}, False
        elif len(cells) == 3 and u"service list" in row_text:
            # Special case to handle the service list.
            return {u"type": u"Service List"}, False
        else:
            return party, False

    def _add_criminal_data_to_parties(self, parties, party_rows):
        """Iterate over the party rows, identify criminal data, and add it.

        Final criminal data will look like:

        'criminal_data': {
            'highest_offense_level_opening': 'None',
            'highest_offense_level_terminated': 'Felony',
            'counts': [{
                'name': 'Attempted money laundering',
                'disposition': '',
                'status': 'pending',
            }, {
                'name': 'Theft of public property',
                'disposition': 'Dismissed on deft's motion',
                'status': 'terminated',
            }],
            'complaints': [{
                'name': '18 USC 1956',
                'disposition': '',
            }],
        },

        :param parties: The already-populated party dicts
        :param party_rows: The trs with party/criminal data
        :return: None
        """
        # Because criminal data spans multiple trs, the way we do this is by
        # keeping track of which party we're currently working on. Then, when
        # we get useful criminal data, we add it to that party.
        empty_criminal_data = {
            u"counts": [],
            u"complaints": [],
            u"highest_offense_level_opening": "",
            u"highest_offense_level_terminated": "",
        }
        section_info = {
            "current_section": None,
            "header_info": None,
            "changed": False,
        }
        current_party_i = -1
        criminal_data = copy.deepcopy(empty_criminal_data)
        for prev, row, nxt in previous_and_next(party_rows):
            cells = row.xpath(".//td")
            if len(cells) == 0:
                # Empty row. Press on.
                continue
            row_text = force_unicode(row.text_content()).strip().lower()
            if not row_text or row_text == "v.":
                # Empty or nearly empty row. Press on.
                continue

            is_represented_by_row = len(
                cells
            ) == 3 and "represented by" in clean_string(
                cells[1].text_content()
            )
            # A row representing a party without representation. ID it by
            # looking for bold underlined text in this row followed by bold
            # text in the next row.
            is_special_party_type_row = all(
                [
                    len(cells) == 1,
                    cells[0].xpath(".//b/u"),
                    nxt is not None
                    and nxt.xpath(".//b")
                    and "represented by"
                    not in clean_string(nxt.text_content()),
                ]
            )
            if any([is_represented_by_row, is_special_party_type_row]):
                # If we hit a "represented by" row or a row that looks like a
                # party type row, we know we've moved to the next party.
                # Increment the party index, so we know to whom we should
                # associate the criminal data.
                if criminal_data != empty_criminal_data:
                    criminal_data = clean_court_object(criminal_data)
                    parties[current_party_i][u"criminal_data"] = criminal_data
                current_party_i += 1
                # Reset section info and criminal data.
                criminal_data = copy.deepcopy(empty_criminal_data)
                self._values_to_none(section_info)
                continue

            section_info = self._get_current_section(section_info, cells)
            if section_info["changed"]:
                continue

            if section_info["current_section"] == "highest_offense":
                offense_level = cells[0].text_content()
                criminal_data[section_info["header_info"]] = offense_level
                continue

            if section_info["current_section"] == "counts":
                try:
                    disposition = cells[2].text_content()
                except IndexError:
                    # Sometimes, if there's no disposition, the cell itself is
                    # missing.
                    disposition = ""
                count_name = cells[0].text_content().strip()
                if count_name == u"None":
                    # No counts here. (Happens with terminated ones a lot.)
                    continue
                criminal_data[u"counts"].append(
                    {
                        u"name": count_name,
                        u"disposition": disposition,
                        u"status": section_info["header_info"],
                    }
                )
                continue

            if section_info["current_section"] == "complaints":
                try:
                    disposition = cells[2].text_content()
                except IndexError:
                    # No disposition info.
                    disposition = ""
                complaint_name = cells[0].text_content()
                if complaint_name == u"None":
                    # No counts here. (Happens with terminated ones a lot.)
                    continue
                criminal_data[u"complaints"].append(
                    {
                        u"name": complaint_name,
                        u"disposition": disposition,
                    }
                )

    @staticmethod
    def _values_to_none(d):
        """Set the values for a dictionary all to None"""
        for k in d.keys():
            d[k] = None

    def _get_current_section(self, current_section, cells):
        """Get the current section for the row.

        If the row contains a section header, then we return the new section
        value. If not, then we return the current_section value (without
        changing it).

        :param current_section: The current section when this function is
        started. This might just get passed through.
        :param cells: The cells (tds) in the current row as a list
        :returns dict with keys:
          'current_section': the current section name
          'header_info': any extra info that might be needed by the caller that
                         we gather from the section header itself
          'changed': whether the section has changed, a boolean,
        """
        cell_0_text = clean_string(cells[0].text_content())
        offense_m = self.offense_regex.search(cell_0_text)
        if offense_m:
            return {
                "current_section": u"highest_offense",
                "header_info": u"highest_offense_level_%s"
                % offense_m.group("status").lower(),
                "changed": True,
            }

        counts_m = self.counts_regex.search(cell_0_text)
        if counts_m:
            return {
                "current_section": u"counts",
                "header_info": counts_m.group("status").lower(),
                "changed": True,
            }

        complaint_m = self.complaints_regex.search(cell_0_text)
        if complaint_m:
            return {
                "current_section": u"complaints",
                "header_info": None,
                "changed": True,
            }

        if cells[0].xpath("./b/u"):
            # it's a header we don't recognize like "Plaintiff". We can't hard
            # code them all.
            return {
                "current_section": "unknown",
                "header_info": None,
                "changed": True,
            }

        current_section["changed"] = False
        return current_section

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
        for atty_node in cell.xpath(".//b"):
            name_parts = force_unicode(
                atty_node.text_content().strip()
            ).split()
            attorney = {
                u"name": u" ".join(name_parts),
                u"roles": [],
                u"contact": u"",
            }
            path = u"./following-sibling::* | ./following-sibling::text()"
            for prev, node, nxt in previous_and_next(atty_node.xpath(path)):
                # noinspection PyProtectedMember
                if isinstance(
                    node,
                    (etree._ElementStringResult, etree._ElementUnicodeResult),
                ):
                    clean_atty = u"%s\n" % " ".join(
                        n.strip() for n in node.split()
                    )
                    if clean_atty.strip():
                        attorney[u"contact"] += clean_atty
                else:
                    if node.tag == u"i":
                        role = force_unicode(node.text_content().strip())
                        if not any(
                            [
                                role.lower().startswith(u"bar status"),
                                role.lower().startswith(u"designation"),
                            ]
                        ):
                            attorney[u"roles"].append(role)

                nxt_is_b_tag = isinstance(nxt, HtmlElement) and nxt.tag == "b"
                if nxt is None or nxt_is_b_tag:
                    # No more data for this attorney.
                    attorneys.append(attorney)
                    break

        return attorneys

    @property
    def docket_entries(self):
        if self._docket_entries is not None:
            return self._docket_entries

        # There can be multiple docket entry tables on a single docket page.
        # See https://github.com/freelawproject/courtlistener/issues/762. ∴ we
        # need to identify the first table, and all following tables. The
        # following tables lack column headers, so we have to use the
        # preceding-sibling tables to make sure it's right.
        docket_header = './/text()[contains(., "Docket Text")]'
        bankr_multi_doc = (
            'not(.//text()[contains(., "Total file size of '
            'selected documents")])'
        )
        footer_multi_doc = 'not(.//text()[contains(., "Footer format:")])'
        docket_entry_rows = self.tree.xpath(
            "//table"
            "[preceding-sibling::table[{dh}] or {dh}]"
            "[{b_multi_doc}]"
            "[{footer_multi_doc}]"
            "/tbody/tr".format(
                dh=docket_header,
                b_multi_doc=bankr_multi_doc,
                footer_multi_doc=footer_multi_doc,
            )
        )[
            1:
        ]  # Skip the first row.

        docket_entries = []
        for row in docket_entry_rows:
            de = {}
            cells = row.xpath(u"./td[not(./input)]")
            if len(cells) == 4:
                # In some instances, the document entry table has an extra
                # column. See almb, 92-04963
                del cells[1]

            date_filed_str = force_unicode(cells[0].text_content())
            if not date_filed_str:
                # Some older dockets have missing dates. Press on.
                continue
            de[u"date_filed"] = convert_date_string(date_filed_str)
            de[u"document_number"] = self._get_document_number(cells[1])
            results = self._get_pacer_doc_id_and_seq_no(
                cells[1], de[u"document_number"]
            )
            de[u"pacer_doc_id"], de[u"pacer_seq_no"] = results[0], results[1]
            de[u"description"] = self._get_description(cells)

            number = de[u"document_number"]
            if number is not None and not number.isdigit():
                # Some courts use the word "doc" instead of a docket number. We
                # skip these for now.
                continue
            docket_entries.append(de)

        docket_entries = clean_court_object(docket_entries)
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

    def query(
        self,
        pacer_case_id,
        date_range_type="Filed",
        date_start=None,
        date_end=None,
        doc_num_start="",
        doc_num_end="",
        show_parties_and_counsel=False,
        show_terminated_parties=False,
        show_list_of_member_cases=False,
        include_pdf_headers=True,
        show_multiple_docs=False,
        output_format="html",
        order_by="date",
    ):
        """Query the docket report and return the results.

        :param pacer_case_id: The internal PACER case ID for a case.
        :param date_range_type: Whether the date range refers to the date items
        were entered into PACER or the date they were filed.
        :param date_start: The start date for the date range (as a date object)
        :param date_end: The end date for the date range (as a date object)
        :param doc_num_start: A range of documents can be requested. This is
        the lower bound of their ID numbers.
        :param doc_num_end: The upper bound of the requested documents.
        :param show_parties_and_counsel: Whether to show the parties and
        counsel in a case (note this adds expense).
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
        :return: None. Instead sets self.response attribute and runs
        self.parse()
        """
        # Set up and sanity tests
        assert (
            self.session is not None
        ), "session attribute of DocketReport cannot be None."
        assert bool(pacer_case_id), (
            "pacer_case_id must be truthy, not '%s'" % pacer_case_id
        )

        if date_range_type not in [u"Filed", u"Entered"]:
            raise ValueError(u"Invalid value for 'date_range_type' parameter.")
        if output_format not in [u"html", u"pdf"]:
            raise ValueError(u"Invalid value for 'output_format' parameter.")
        if order_by == u"date":
            order_by = u"oldest date first"
        elif order_by == u"-date":
            order_by = u"most recent date first"
        elif order_by == u"document_number":
            order_by = u"document number"
        else:
            raise ValueError(u"Invalid value for 'order_by' parameter.")

        if show_terminated_parties and not show_parties_and_counsel:
            raise ValueError(
                u"Cannot show terminated parties if parties and "
                u"counsel are not also requested."
            )

        query_params = {
            u"all_case_ids": pacer_case_id,
            u"sort1": order_by,
            u"date_range_type": date_range_type,
            u"output_format": output_format,
            # Any value works in this parameter, but it cannot be blank.
            # Normally this would have a value like '3:12-cv-3879', but that's
            # not even necessary.
            u"case_num": u" "
            # These fields seem to be unnecessary/unused.
            # 'view_comb_doc_text': '',
            # 'PreResetField': '',
            # 'PreResetFields': '',
        }
        if date_start:
            query_params[u"date_from"] = date_start.strftime(u"%m/%d/%Y")
        else:
            # If it's a big docket and you don't filter it in some form you get
            # an intermediate page that says, paraphrasing: "Do you really want
            # to pull that whole, big, docket?" However, if we always make sure
            # to have this field populated, we don't see that page. ∴, always
            # set this value. See #210.
            query_params[u"date_from"] = "1/1/1960"
        if date_end:
            query_params[u"date_to"] = date_end.strftime(u"%m/%d/%Y")
        if doc_num_start:
            query_params[u"documents_numbered_from_"] = str(int(doc_num_start))
        if doc_num_end:
            query_params[u"documents_numbered_to_"] = str(int(doc_num_end))
        if show_parties_and_counsel is True:
            query_params[u"list_of_parties_and_counsel"] = u"on"
        if show_terminated_parties is True:
            query_params[u"terminated_parties"] = u"on"
        if show_list_of_member_cases is True:
            query_params[u"list_of_member_cases"] = u"on"
        if include_pdf_headers is True:
            query_params[u"pdf_header"] = u"1"
        if show_multiple_docs is True:
            query_params[u"view_multi_docs"] = u"on"

        logger.info(
            u"Querying docket report for case ID '%s' with params %s"
            % (pacer_case_id, query_params)
        )

        self.response = self.session.post(
            self.url + "?1-L_1_0-1", data=query_params
        )
        self.parse()

    def _set_metadata_values(self):
        # The first ancestor table of the table cell containing "date filed"
        table = self.tree.xpath(
            # Match any td containing Date [fF]iled
            u'//td[.//text()[contains(translate(., "f", "F"), "Date Filed:")]]'
            # And find its highest ancestor table that lacks a center tag.
            u"/ancestor::table[not(.//center)][last()]"
        )[0]
        cells = table.xpath(u".//td")
        # Convert the <br> separated content into text strings, treating as
        # much as possible as HTML.
        values = []
        for cell in cells:
            clean_texts = [clean_string(s) for s in self._br_split(cell)]
            values.extend(clean_texts)
        values.append(" ".join(values))
        self.metadata_values = values

    @staticmethod
    def _get_pacer_doc_id_and_seq_no(cell, document_number):
        if not document_number:
            return None, None
        else:
            # We find the first link having the document number as text.
            # This is needed because txnb combines the second and third
            # column in their docket report.
            anchors = cell.xpath(u".//a")
            if len(anchors) == 0:
                # Docket entry exists, but cannot download document (it's
                # sealed, a minute entry, or otherwise unavailable in PACER).
                return None, None
            for anchor in anchors:
                if anchor.text_content().strip() == document_number:
                    doc1_url = anchor.xpath("./@href")[0]
                    pacer_doc_id = get_pacer_doc_id_from_doc1_url(doc1_url)
                    pacer_seq_no = get_pacer_seq_no_from_doc1_anchor(anchor)
                    return pacer_doc_id, pacer_seq_no

        # In case none of our URLs can be parsed.
        return None, None

    def _get_document_number(self, cell):
        """Get the document number.

        Some jurisdictions have the number as, "13 (5 pgs)" so some processing
        is needed. See flsb, 09-02199-JKO.
        """
        words = [
            word for phrase in self._br_split(cell) for word in phrase.split()
        ]
        if words:
            first_word = re.sub(u"[\s\u00A0]", "", words[0])
            if self.court_id == u"txnb":
                # txnb merges the second and third columns, so if the first
                # word is a number, return it. Otherwise, assume doc number
                # isn't listed for the item.
                if first_word.isdigit():
                    return first_word
            else:
                return first_word
        return None

    def _get_description(self, cells):
        if self.court_id != u"txnb":
            return force_unicode(cells[2].text_content())

        s = force_unicode(cells[1].text_content())
        # In txnb the second and third columns of the docket entries are
        # combined. The field can have one of four formats. Attempt the most
        # detailed first, then work our way down to just giving up and
        # capturing it all.
        ws = u"[\s\u00A0]"  # Whitespace including nbsp
        regexes = [
            # 2 (23 pgs; 4 docs) Blab blah (happens when attachments exist and
            # page numbers are on)
            u"^{ws}*\d+{ws}+\(\d+{ws}+pgs;{ws}\d+{ws}docs\){ws}+(.*)",
            # 2 (23 pgs) Blab blah (happens when pg nums are on)
            u"^{ws}*\d+{ws}+\(\d+{ws}+pgs\){ws}+(.*)",
            # 2 Blab blah (happens when page nums are off)
            u"^{ws}*\d+{ws}+(.*)",
            # Blab blah (happens when a doc is sealed; can't be downloaded)
            u"^{ws}*(.*)",
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
                return [
                    p
                    for p in self.parties
                    if p[u"type"] == u"Debtor"
                    or p[u"type"] == u"Debtor In Possession"
                ][0][u"name"]
            except IndexError:
                pass

            # This is probably a sub docket to a larger case. Use that title.
            try:
                path = u'//i[contains(., "Lead BK Title")]/following::text()'
                case_name = self.tree.xpath(path)[0].strip()
            except IndexError:
                case_name = u"Unknown Case Title"

            if self.is_adversary_proceeding:
                case_name += u" - Adversary Proceeding"
        else:
            # Skip the last value, it's a concat of all previous values and
            # isn't needed for case name matching.
            case_name = None
            v = self.metadata_values[0]
            for regex in self.case_name_regexes:
                m = regex.search(v)
                if m:
                    case_name = m.group(1)
                    break

            if case_name is None:
                # Try to get the case name from the party attribute. Use first
                # plaintiff v. first defendant
                plaintiff = None
                defendant = None
                for party in self.parties:
                    if plaintiff is None and party["type"] == "Plaintiff":
                        plaintiff = party["name"]
                    elif defendant is None and party["type"] == "Defendant":
                        defendant = party["name"]
                if plaintiff and defendant:
                    case_name = "%s v. %s" % (plaintiff, defendant)

            if case_name is None:
                # All parsing has failed. Give up.
                case_name = u"Unknown Case Title"

        return clean_string(harmonize(case_name))

    def _get_docket_number(self):
        if self.is_bankruptcy:
            docket_number_path = "//font"
        else:
            docket_number_path = "//h3"
        nodes = self.tree.xpath(docket_number_path)
        string_nodes = [s.text_content() for s in nodes]
        return self._parse_docket_number_strs(string_nodes)

    def _get_nature_of_suit(self):
        if self.is_adversary_proceeding:
            # Add the next table too, if it contains the nature of suit.
            path = u'//table[contains(., "Nature[s] of")]//tr'
            rows = self.tree.xpath(path)
            nos = []
            for row in rows:
                cell_texts = [
                    force_unicode(s.strip())
                    for s in row.xpath(u"./td[position() > 2]/text()")
                    if s.strip()
                ]
                if len(cell_texts) > 1:
                    nos.append(" ".join(cell_texts))
            return "; ".join(nos) or ""
        else:
            return self._get_value(self.nos_regex, self.metadata_values)

    def _get_judge(self, regex):
        judge_regex = re.compile(regex, flags=re.DOTALL | re.IGNORECASE)
        judge_str = self._get_value(judge_regex, self.metadata_values)
        if judge_str:
            return normalize_judge_string(judge_str)[0]
        else:
            # No luck getting it in the metadata_values attribute. Broaden
            # the search to look in the entire docket HTML.
            text_nodes = self.tree.xpath("//text()")
            text_nodes = [t for t in text_nodes if t and not t.isspace()]
            judge_str = self._get_value(judge_regex, text_nodes)
            return normalize_judge_string(judge_str)[0]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m juriscraper.pacer.docket_report filepath")
        print("Please provide a path to an HTML file to parse.")
        sys.exit(1)
    report = DocketReport("cand")  # Court ID is only needed for querying.
    filepath = sys.argv[1]
    print("Parsing HTML file at %s" % filepath)
    with open(filepath, "r") as f:
        text = f.read().decode("utf-8")
    report._parse_text(text)
    pprint.pprint(report.data, indent=2)
