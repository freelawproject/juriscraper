"""Downloading and parsing of dockets from the Supreme Court.

Dockets offering a JSON rendering use the following URL naming pattern:

Base URL: https://www.supremecourt.gov/RSS/Cases/JSON/< YY >< DT >< # >.json
Term (YY): Two-digit year of the Supreme Court term beginning in October.
Docket type (DT): One of {'-', 'A', 'M', 'O'}, corresponding to the nature of the
    docket.
    '-': Petitions, typically for writs of certiorari or mandamus
    'A': Applications, not yet reviewed by the Court
    'M': Motions, such as for leave to file as a veteran
    'O': 'Orig.' cases; this designation is unclear and there are few
Case number (#): Two increasing ranges of integers.
    'Paid' cases number from 1 to 4999 in a given term
    'IFP' (in forma pauperis) a.k.a pauper cases number 5001 and up each term
"""

from io import BytesIO
import json
from math import sqrt
import re
from time import sleep
from urllib.parse import urljoin

import fitz  # the package name of the `pymupdf` library
import requests
from requests.exceptions import ConnectionError

from juriscraper.lib.log_tools import make_default_logger
from juriscraper.lib.exceptions import AccessDeniedError
from .clients import (
    download_client,
    response_handler,
    jitter,
    is_docket,
    is_not_found_page,
    is_stale_content,
)
from . import utils


logger = make_default_logger()


def linear_download(
    docket_numbers: list,
    delay: float = 0.25,
    since_timestamp: str = None,
    fails_allowed: int = 5000,
    **kwargs,
):
    """Iterate over specific docket numbers and yield valid responses.

    :param docket_numbers: List of docket numbers in valid format.
    :param delay: Float value of throttling delay between download attempts.
    """
    base_url = "https://www.supremecourt.gov/RSS/Cases/JSON/{}.json"
    session = requests.Session()

    # store docket not found instances to estimate data endpoint
    not_found = set()
    stale_set = set()
    fresh_set = set()

    # truncate possible values for rate-limiting delay
    trunc_delay = max(0, min(delay, 2.0))

    logger.info("Querying docket numbers...")
    for dn in docket_numbers:
        docketnum = utils.endocket(dn)
        logger.debug(f"Trying docket {docketnum}...")

        # exception handling delegated to downloader
        response = download_client(
            url=base_url.format(docketnum),
            session=session,
            since_timestamp=since_timestamp,
        )
        try:
            valid_response = response_handler(response)
        except (AccessDeniedError, ConnectionError) as e:
            logger.critical(f"Abording download at {docketnum}", exc_info=e)
            raise

        if is_stale_content(valid_response):
            logger.debug(f"{docketnum} returned 304; skipping.")
            stale_set.add(docketnum)
            continue  # no delay
        elif is_docket(valid_response):
            logger.debug(f"Found docket {docketnum}.")
            fresh_set.add(
                (
                    docketnum,
                    utils.makedate(response.headers.get("Last-Modified")),
                )
            )
            yield response
            # delay to rate-limit requests
            sleep(trunc_delay + jitter(sqrt(delay)))
        elif is_not_found_page(valid_response):
            not_found.add(docketnum)
            logger.debug(f"Not found {docketnum}")
            if len(not_found) > fails_allowed:
                # stop downloading when cumulative `fails_allowed` is exceeded
                break
            else:
                # delay to rate-limit requests
                sleep(trunc_delay + jitter(sqrt(delay)))
        else:
            raise RuntimeError(f"Found edge case downloading {docketnum}")

    session.close()

    # log download results
    logger.info(
        f"Finished updating --> {{Updated: {len(fresh_set)}, "
        f"Stale (ignored): {len(stale_set)}, "
        f"'Not Found': {len(not_found)}}}"
    )
    _fs = sorted(list(fresh_set), key=lambda z: utils.docket_priority(z[0]))
    logger.debug(f"Updated dockets: {_fs}")

    _nf = sorted(list(not_found), key=utils.docket_priority)
    logger.debug(f"Not Found: {_nf}")

    _ss = sorted(list(stale_set), key=utils.docket_priority)
    logger.debug(f"Stale dockets: {_ss}")


judgment_regex = re.compile(r"^Judgment", flags=re.IGNORECASE)
simple_petition_regex = re.compile(
    r"((?<=Petition\s)|(?<=Case\s))(DENIED|DISMISSED)", flags=re.IGNORECASE
)
affirmed_regex = re.compile(r"Adjudged to be AFFIRMED")
closed_regex = re.compile(r"Case considered closed")
removed_regex = re.compile(r"Case removed from Docket")
cert_dismissed_regex = re.compile(r"Writ of Certiorari Dismissed")

distributed_regex = re.compile(r"(?<=DISTRIBUTED)(?:.*?)([0-9/]+)", flags=re.I)
amicus_regex = re.compile(
    (
        r"(?<=Brief amicus curiae of )(.*?)( in support of neither party)?\s?"
        r"(?=[fF]iled|(Corrected version submitted)|submitted)"
    ),
    flags=re.I,
)

# use this only after splitting entry text on '.'
wildcard_petition_regex = re.compile(
    r"((?<=Petition\s)|(?<=Case\s)).*(DENIED|DISMISSED)", flags=re.IGNORECASE
)


denied_regex = re.compile(
    r"(?<=Application )(?:\(\w{4,8}\)\s)?.*DENIED"
    r"|(?<=Motion )(?:\(\w{4,8}\)\s)?.*DENIED",
    flags=re.IGNORECASE,
)
granted_regex = re.compile(
    r"(?<=Application )(?:\(\w{4,8}\)\s)?.*GRANTED"
    r"|(?<=Motion )(?:\(\w{4,8}\)\s)?.*GRANTED",
    flags=re.IGNORECASE,
)
completed_regex = re.compile(
    r"(?<=Application )(?:\(\w{4,8}\)\s)?.*COMPLETED"
    r"|(?<=Motion )(?:\(\w{4,8}\)\s)?.*COMPLETED",
    flags=re.IGNORECASE,
)
withdrawn_regex = re.compile(
    r"(?<=Application )(?:\(\w{4,8}\)\s)?.*WITHDRAWN"
    r"|(?<=Motion )(?:\(\w{4,8}\)\s)?.*WITHDRAWN",
    flags=re.IGNORECASE,
)
ifp_dismissed_regex = re.compile(
    r"Motion of petitioner for leave to proceed in forma pauperis denied, "
    r"and petition for writ of (mandamus|certiorari to the).*dismissed."
)


# TODO: text value cleaning, harmonizing from lib.string_utils
class SCOTUSDocketReport:
    """Parser for SCOTUS JSON dockets.
    Modeled on juriscraper.pacer.appellate_docket.AppellateDocketReport.
    """

    meta_mapping = {
        "docket_number": "CaseNumber",
        "capital_case": "bCapitalCase",
        "question_presented": "QPLink",  # URL
        "related_cases": "RelatedCaseNumber",  # list type
        "linked_cases": "Links",  # str 'Linked with YY-NNNNN'
        "fee_status": "sJsonCaseType",
        "date_filed": "DocketedDate",
        "petitioner": "PetitionerTitle",
        "respondent": "RespondentTitle",
        "lower_court": "LowerCourt",
        "lower_court_case_numbers": "LowerCourtCaseNumbers",  # list type?
        "lower_court_decision_date": "LowerCourtDecision",
        "lower_court_rehearing_denied_date": "LowerCourtRehearingDenied",
    }
    entries_mapping = {
        "date_filed": "Date",
        "description": "Text",
        "document_title": "Description",
        "url": "DocumentUrl",
    }

    base_url = "https://www.supremecourt.gov/RSS/Cases/JSON/{}.json"

    # exclude docket boilerplate entries e.g. 'Proof of Service'
    exclude_entries_pattern = r"Main Document" r"|Proof of Service"
    exclude_entries_regex = re.compile(exclude_entries_pattern)
    petitioner_regex = re.compile(r".+(?=, Petitioner|Applicant)")

    def __init__(self, docket: dict, **kwargs):
        """Takes the decoded JSON object for a single SCOTUS docket."""
        self._docket = docket
        self._kwargs = kwargs
        self.court_id = self.__module__
        self._docket_number = None
        self._url = utils.docket_number_regex.search(docket["CaseNumber"])
        self._metadata = None
        self._docket_entries = None
        self._attorneys = None
        self._dispositions = []
        self._distributions = []
        self._amici = set()
        self._argued_date = None

    @classmethod
    def from_response(cls, response: requests.Response, **kwargs):
        """Instantiate with values taken from `response`."""
        return cls.__init__(response.json(), **kwargs)

    @classmethod
    def from_text(cls, json_text: str, **kwargs):
        """Instantiate with dict from a JSON-encoded string."""
        return cls.__init__(json.loads(json_text), **kwargs)

    @property
    def docket_number(self):
        if self._docket_number is None:
            dn = self._docket["CaseNumber"].rstrip()
            self._docket_number = utils.docket_num_strict_regex.search(dn).group(0)
        return self._docket_number

    def _get_petitioner(self):
        """Strip ', Petitioner' from the title as this is implicit."""
        _petitioner = self._docket["PetitionerTitle"]
        if psearch := self.petitioner_regex.search(_petitioner):
            _petitioner = psearch.group(0)
        return _petitioner

    def _get_case_name(self):
        """Petitioner v. Respondent"""
        return f"{self._get_petitioner()} v. {self._docket.get('RespondentTitle')}"

    def _get_lower_court_cases(self):
        """These are presented as a string representation of a tuple, but not
        correctly formatted for serializing. Use regex."""
        if (casenums := self._docket["LowerCourtCaseNumbers"]) == "":
            return None
        else:
            return casenums.strip("()").replace(" ", "").split(",")

    def _get_related_cases(self):
        """These are presented as a list."""
        # cases_str =
        if (related := self._docket["RelatedCaseNumber"]) != []:
            return related
        else:
            return None

    @property
    def url(self):
        url_template = "https://www.supremecourt.gov/RSS/Cases/JSON/{}.json"
        return url_template.format(self.docket_number)

    def query(self, docket_number, since_timestamp, *args, **kwargs):
        """Query supremecourt.gov and set self.response with the response."""
        raise NotImplementedError(".query() must be overridden")
        # url = self.base_url.format(docket_number)
        # response = download_client(url, since_timestamp=since_timestamp)
        # validated_response = response_handler(response)

        # if is_stale_docket(validated_response):
        #     pass
        # elif is_docket(validated_response):
        #     self._docket = validated_response.json()

    def parse(self):
        """Parse the JSON data provided in a requests.response object. In most cases, you won't need to call this since it will be automatically called by self.query, if needed.

        :return: None
        """
        self._parse_text(self._docket)

    def _parse_text(self, *args):
        """A method intended to clean up HTML source.

        This is being preserved in case it is needed for adapting the JSON parser to a caller that expects the `BaseReport` interface.

        :return: None
        """
        raise NotImplementedError("This class does not parse HTML text.")

    def _get_questions_presented(self):
        """Download 'Questions Presented' PDF. Missing from some dockets, for
        example, motions or applications for extension of time.
        """
        qp = None

        if pdfpath := self._docket.get("QPLink"):
            base = "https://www.supremecourt.gov/"
            url = urljoin(base, pdfpath)
            r = requests.get(url)
            r.raise_for_status()
            if r.headers.get("content-type") == "application/pdf":
                msg = (
                    "Got PDF binary data for 'Questions Presented' "
                    f"in {self.docket_number}"
                )
                logger.info(msg)
                qp = r
        return qp

    def _parse_filing_links(self, links: list, keep_boilerplate: bool = True) -> list:
        """Return the main documents from a docket entry with links by excluding
        ancillary documents e.g. 'Proof of Service' and 'Certificate of Word Count'.

        :param links: List of docket entries
        """
        filings = []
        for row in links:
            match = utils.filing_url_regex.search(row["DocumentUrl"])
            record = {
                "entry_number": match.group("entrynum"),
                "document_title": row["Description"],
                "url": row["DocumentUrl"],
                "document_timestamp": utils.parse_filing_timestamp(
                    match.group("timestamp")
                ),
            }
            if not keep_boilerplate and self.exclude_entries_regex.search(
                row["Description"]
            ):
                continue
            filings.append(record)
        return filings

    @property
    def metadata(self) -> dict:
        if self._metadata is None:
            data = {
                "petitioner": "PetitionerTitle",
                "respondent": "RespondentTitle",
                "appeal_from": "LowerCourt",
                "question_presented": "QPLink",
                "related_cases": "RelatedCaseNumber",
                "linked_cases": "Links",  # str 'Linked with YY-NNNNN'
                "fee_status": "sJsonCaseType",
                "lower_court": "LowerCourt",
                "lower_court_case_numbers": "LowerCourtCaseNumbers",  # list type?
                "lower_court_decision_date": "LowerCourtDecision",
                "lower_court_rehearing_denied_date": "LowerCourtRehearingDenied",
                "capital_case": "bCapitalCase",
            }
            self._metadata = {
                "court_id": self.court_id,
                "docket_number": self.docket_number,
                "case_name": self._get_case_name(),
                "date_filed": self._get_docketed_date(),
            }
            self._metadata |= {k: self._docket.get(v) for k, v in data.items()}
        return self._metadata

    def _original_entries(self) -> list:
        """The original docket entries from the docket JSON."""
        return self._docket["ProceedingsandOrder"]

    def _entry_count(self) -> int:
        """The number of docket entries as originally presented on supremecourt.gov.
        This may differ from the number of entries as parsed elsewhere in this class.
        """
        return len(self._docket["ProceedingsandOrder"])

    @property
    def docket_entries(self) -> list:
        """Return docket entries as a list of dict records. Where an entry contains multiple attachments, merge entry and attachment metadata."""
        if self._docket_entries is None:
            docket_entry_rows = self._docket["ProceedingsandOrder"]

            docket_entries = []
            for row in docket_entry_rows:
                de = {
                    "date_filed": utils.makedate(row["Date"]).date(),
                    "docket_number": self.docket_number,
                    "description": row["Text"],
                }

                if links := row.get("Links"):
                    filing_list = self._parse_filing_links(links)
                    for filing in filing_list:
                        docket_entries.append(de | filing)
                else:
                    docket_entries.append(de)

            self._docket_entries = docket_entries
        return self._docket_entries

    def _amicus_entries(self) -> list:
        """Subset of docket entries containing amicus curiæ briefs."""
        entries = []

        for e in self.docket_entries:
            # only take the briefing document; skip boilerplate docs
            if (
                amicus_regex.search(e["description"])
                and "not accepted for filing" not in e["description"]
                and e["document_title"] in {"Main Document", "Other"}
            ):
                entries.append(e)
        return entries

    @property
    def amici(self) -> set:
        """List the amici curiae who file briefs in this docket."""
        if self._amici == set():
            for e in self._amicus_entries():
                match = amicus_regex.search(e["description"])
                self._amici.add(match.group(1))

        return set(sorted(self._amici))

    def _get_docketed_date(self):
        """If this field is missing, substitute the date of the first docket entry."""
        if (_docketed := self._docket.get("DocketedDate")) == "":
            # fall back on first docket entry
            return self.docket_entries[0].get("date_filed")
        else:
            return utils.makedate(_docketed).date()

    def _application_disposition(self, entry):
        """Search for dispositions specific to Applications: either
        'denied' or 'granted'."""
        if denied_regex.search(entry):
            return "DENIED"
        elif granted_regex.search(entry):
            return "GRANTED"
        elif completed_regex.search(entry):
            return "COMPLETED"
        elif withdrawn_regex.search(entry):
            return "WITHDRAWN"
        else:
            return None

    # TODO: sometimes dispositions are subject to rehearing; abandon this?
    @property
    def disposition(self) -> list:
        """Find any case disposition in docket entries."""
        if self._dispositions == []:

            def mkdt(entry):
                """Return a datetime.date object from the entry's date field."""
                return utils.makedate(entry["Date"]).date()

            _docket_type = self.docket_number[2]

            for entry in self._original_entries():
                desc = entry["Text"]

                if _docket_type in {"A", "M"}:
                    if _disposition := self._application_disposition(desc):
                        self._dispositions.append((_disposition, mkdt(entry)))
                        continue

                # Judgment issued
                if judgment_regex.search(desc) or affirmed_regex.search(desc):
                    self._dispositions.append(("DECIDED", mkdt(entry)))
                    continue
                # Petition denied or dismissed
                elif _disposition := simple_petition_regex.search(desc):
                    self._dispositions.append(
                        (_disposition.group(2).upper(), mkdt(entry))
                    )
                    continue
                elif closed_regex.search(desc):
                    self._dispositions.append(("CLOSED", mkdt(entry)))
                    continue
                elif removed_regex.search(desc):
                    self._dispositions.append(("REMOVED", mkdt(entry)))
                    continue
                elif cert_dismissed_regex.search(desc):
                    self._dispositions.append(("DISMISSED", mkdt(entry)))
                    continue
                elif _related := self._get_related_cases():
                    # could be Vided (i.e. combined)
                    for row in _related:
                        if isinstance(row, dict):
                            if "Vide" in row["RelatedType"]:
                                self._dispositions.append(("VIDED", mkdt(entry)))
                                break

                # now try splitting field on period before pattern matching
                for s in desc.split("."):
                    sentence = s.strip()
                    if sentence == "":
                        continue
                    elif judgment_regex.search(sentence) or affirmed_regex.search(
                        sentence
                    ):
                        self._dispositions.append(("DECIDED", mkdt(entry)))
                        break
                    elif _disposition := wildcard_petition_regex.search(sentence):
                        self._dispositions.append(
                            (_disposition.group(2).upper(), mkdt(entry))
                        )
                        break

                # elif ifp_dismissed_regex.search(desc):
                #     self._dispositions.append(
                #         ("DISMISSED", utils.makedate(entry["Date"]).date())
                #     )
                # elif denied_regex.search(desc):
                #     self._dispositions.append(
                #         ("DENIED", utils.makedate(entry["Date"]).date())
                #     )
                # elif dismissed_regex.search(desc):
                #     self._dispositions.append(
                #         ("DISMISSED", utils.makedate(entry["Date"]).date())
                #     )
        try:
            return self._dispositions[-1]
        except IndexError:
            return None

    @property
    def distributions(self) -> list:
        """Find date(s) where case was distributed for conference."""
        if self._distributions == []:

            def distributed_date(desc):
                """Return a datetime.date object from the entry's date field."""
                if match := distributed_regex.search(desc):
                    dstring = match.group(1)
                    return utils.makedate(dstring, dayfirst=False).date()
                else:
                    return

            for entry in self._original_entries():
                desc = entry["Text"]
                if dt := distributed_date(desc=desc):
                    self._distributions.append(dt)

            self._distributions.sort()

        return self._distributions

    @property
    def argued_date(self):
        """Return oral arguments date."""
        if self._argued_date is None:
            for e in self.docket_entries:
                if e["description"].lstrip().lower()[:6] == "argued":
                    self._argued_date = e["date_filed"]
        return self._argued_date

    @staticmethod
    def _parse_attorney(row, affiliation) -> dict:
        """Parse an attorney entry."""
        record = {
            "affiliation": affiliation,
            "party": row["PartyName"],
            "counsel_of_record": row["IsCounselofRecord"],
            "name": row["Attorney"],
            "firm": row["Title"],
            "prisoner_id": row["PrisonerId"],
            "contact": {
                "email": row["Email"],
                "phone": row["Phone"],
                "address": row["Address"],
                "city": row["City"],
                "state": row["State"],
                "zipcode": row["Zip"],
            },
        }
        return record

    def _parse_petitioner_attorneys(self) -> list:
        """Parse attorney(s) for Petitioner."""
        records = []
        for row in self._docket["Petitioner"]:
            row["docket_number"] = self._docket_number
            records.append(self._parse_attorney(row, "Petitioner"))
        return records

    def _parse_respondent_attorneys(self) -> list:
        """Parse attorney(s) for Respondent."""
        records = []
        if self._docket.get("Respondent"):
            for row in self._docket["Respondent"]:
                row["docket_number"] = self._docket_number
                records.append(self._parse_attorney(row, "Respondent"))
        return records

    def _parse_other_attorneys(self) -> list:
        """Parse attorney(s) representing other parties, if any."""
        records = []
        if self._docket.get("Other"):
            for row in self._docket["Other"]:
                row["docket_number"] = self._docket_number
                records.append(self._parse_attorney(row, "Other"))
        return records

    def _parse_attorneys(self):
        """Parse all attorneys for this docket."""
        all_attorneys = (
            self._parse_petitioner_attorneys(),
            self._parse_respondent_attorneys(),
            self._parse_other_attorneys(),
        )
        return [r for party in all_attorneys for r in party]

    @property
    def parties(self) -> list:
        """Modeled on juriscraper.pacer.docket_report.DocketReport."""
        petitioner = {
            "name": self._get_petitioner(),
            "type": "Petitioner",
            "attorneys": self._parse_petitioner_attorneys(),
        }
        respondent = {
            "name": self._docket["RespondentTitle"],
            "type": "Respondent",
            "attorneys": self._parse_respondent_attorneys(),
        }
        return [petitioner, respondent]

    @property
    def attorneys(self) -> list:
        """List of all attorneys associated with this docket."""
        if self._attorneys is None:
            self._attorneys = self._parse_attorneys()
        return self._attorneys

    @staticmethod
    def docket_pdf_download(
        url: str,
        retries: int = 3,
        delay: float = 0.5,
        **kwargs,
    ) -> requests.Response:
        """Download an Orders PDF.

        Note: kwargs passed to session.get().
        """
        pdf_headers = {
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,*/*;q=0.8"
            ),
            "Host": "www.supremecourt.gov",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "same-origin",
            "Sec-GPC": "1",
        }

        for i in range(retries):
            response = download_client(
                url=url,
                headers=pdf_headers,
                **kwargs,
            )
            # allow caller to handle status code 304 responses

            try:
                result = response_handler(response)
            except requests.exceptions.HTTPError as he:
                logger.debug(f"Retry {i + 1} because {repr(he)}")
                sleep((i * delay) + jitter(delay))
            else:
                return result

    @staticmethod
    def docket_pdf_parser(pdf: bytes) -> set:
        """Extract docket numbers from an Orders PDF. In-memory objects are passed to
        the 'stream' argument."""
        if isinstance(pdf, BytesIO):
            open_kwds = dict(stream=pdf)
        elif isinstance(pdf, bytes):
            open_kwds = dict(stream=BytesIO(pdf))
        else:
            open_kwds = dict(filename=pdf)

        _pdf = fitz.open(**open_kwds)
        text_pages = [pg.get_text() for pg in _pdf]
        # pdf_string = "\n".join()
        # matches = utils.orders_docket_regex.findall(pdf_string)
        # # clean up dash characters so only U+002D is used
        # docket_set = set(
        #     [utils.dash_regex.sub("\u002d", dn) for dn in matches]
        # )
        return text_pages
