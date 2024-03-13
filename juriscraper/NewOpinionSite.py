from datetime import date, datetime
from functools import cmp_to_key
from typing import Dict, List, Union

from juriscraper.AbstractSite import AbstractSite
from juriscraper.lib.judge_parsers import normalize_judge_string
from juriscraper.lib.string_utils import (
    CaseNameTweaker,
    clean_string,
    convert_date_string,
    harmonize,
)
from juriscraper.schemas.schema_validator import SchemaValidator


class NewOpinionSite(AbstractSite):
    """
    Inherits from AbstractSite to access downloading and processing methods

    Overrides legacy methods which have to do with data transformation:
    converting, cleaning and shaping data

    Validates cleaned cases using JSON Schema Validator

    The main entry point is `parse`. Keeps interface compatible
    for courtlistener caller to consume

    Lifecycle of a scrape:
    - scrape is handled by inheriting scraper.
        For expected attribute naming style see `build_nested_object` docstring
    - build nested objects as expected by the schema
    - clean values
    - propagate values which repeat across objects
    - fill default values
    - validate against JSON Schema

    Design heuristics:
    Automate as much as possible, improve developer experience
    Inheriting scraper should concern itself mostly with parsing the
    page and assigning proper names to the values, not with building
    the nested object expected by CL, nor with manually calling the
    cleaning functions depending on the data type, nor with filling
    default values
    """

    expected_content_types = ["application/pdf", "Application/pdf"]
    is_cluster_site = True

    # `judges` and `joined_by_str` refer to multiple judges
    # if we pass a "symbol"-separated string of multiple judges
    # `normalize_judge_string` may missinterpret it depending
    # on the "symbol" . It is better that the scraper pass them as lists

    # Ingestion into the DB could be improved by adding extra descriptors
    # of the judge's names, flags for full or partial names, a flag
    # for "messy" string or only name included
    judge_keys = {
        "assigned_to_str",
        "referred_to_str",
        "judges",
        "author_str",
        "joined_by_str",
        "ordering_judge_str",
    }

    # For hash building
    sort_keys = [
        "case_dates",
        "case_names",
        "download_urls",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cases = []

        self.schema_validator = SchemaValidator()
        self.cnt = CaseNameTweaker()
        # To be filled by inheriting classes
        self.status = ""

    def __iter__(self):
        yield from self.cases

    def __getitem__(self, index: int) -> Dict:
        return self.cases[index]

    def __len__(self) -> int:
        return len(self.cases)

    def parse(self):
        """Overrides AbstractSite.parse"""
        if not self.downloader_executed:
            self.html = self._download()
            self._process_html()

        self._post_parse()

        clean_cases = []
        for case in self.cases:
            clean_case = self.build_nested_object(case)
            self.fill_default_and_required_values(clean_case)
            self.schema_validator.validate(clean_case.get("Docket"))
            self.recast_dates(clean_case)
            clean_cases.append(clean_case)

        self.cases = clean_cases
        self.cases.sort(key=cmp_to_key(self.sort_by_attributes))

        # Ordering is important for hash
        # Hash will be used by caller to skip downloading binary content if page has
        # already been seen
        self.case_names = [case["Docket"]["case_name"] for case in self.cases]
        self._make_hash()

        return self

    def build_nested_object(self, case: Dict) -> Dict:
        """Build nested object expected by CL and defined on JSON Schemas

        {Model Name}: {Naming convention}
        Docket: field name preceded by "d."
        OpinionCluster: field name preceded by "oc."
        Opinion: expected to be returned as an object, with key "opinions"
        OriginatingCourtInformation: expected to be returned as an object, with key "oci"

        :param case: case as returned by the scraper

        :return: Nested object as expected by CL
        """
        cl_obj = {"Docket": {"OpinionCluster": {}}}

        for k, v in case.items():
            clean_value = self.clean_value(k, v)
            if not clean_value:
                continue

            if "." in k:
                obj, key = k.split(".")
                if obj == "d":
                    cl_obj["Docket"][key] = clean_value
                elif obj == "oc":
                    cl_obj["Docket"]["OpinionCluster"][key] = clean_value
            elif k == "oci":
                cl_obj["Docket"]["OriginatingCourtInformation"] = clean_value
            elif k == "opinions":
                ops = (
                    [clean_value]
                    if isinstance(clean_value, dict)
                    else clean_value
                )
                cl_obj["Docket"]["OpinionCluster"]["Opinions"] = ops
            else:
                raise NotImplementedError(
                    f"Unsupported complex object with key '{k}' {v}"
                )

        return cl_obj

    def recast_dates(self, clean_case: Dict) -> None:
        """Converts datetime strings into Python `datetime.date` objects

        See `clean_value` docstring on dates for why we have to recast the dates

        :param clean_case: validated object
        :return: None, modifies objects in place
        """
        obj_x_date_fields = [
            (
                clean_case["Docket"]["OpinionCluster"],
                ["date_filed", "date_blocked"],
            ),
            (
                clean_case["Docket"],
                [
                    "date_filed",
                    "date_terminated",
                    "date_last_filing",
                    "date_blocked",
                ],
            ),
            (
                clean_case["Docket"].get("OriginatingCourtInformation", {}),
                [
                    "date_disposed",
                    "date_filed",
                    "date_judgment",
                    "date_judgment_eod",
                    "date_filed_noa",
                    "date_received_coa",
                ],
            ),
        ]

        for obj, date_fields in obj_x_date_fields:
            for df in date_fields:
                if obj.get(df):
                    obj[df] = datetime.strptime(obj[df], "%Y-%m-%d").date()

    def clean_value(
        self, key: str, value: Union[Dict, List, str]
    ) -> Union[Dict, List, str, None]:
        """Clean values recursively

        About dates:
        Courtlistener expects Python `datetime.date` objects, which has no direct support
        in JSON. At most, the validator supports `{"type": "string", "format": "date"}`
        where the string format follows RFC 3339. So, we cast dates into strings, and will
        recast them later after validation is passed

        :param key: field name, used to apply special cleaning functions
        :param value: dict, list or string

        :return: cleaned value, with same input type
        """
        if isinstance(value, dict):
            return {k: self.clean_value(k, v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.clean_value(key, item) for item in value]

        if value is None or not value:
            return

        if key == "download_url":
            value = value.strip()
        else:
            if isinstance(value, str):
                if "date" in key:
                    value = str(convert_date_string(value))
                else:
                    value = clean_string(value)
            elif isinstance(value, datetime):
                value = str(value.date())
            elif isinstance(value, date):
                value = str(value)

            if key in ["case_name", "docket_number"]:
                value = harmonize(value)
            elif key in self.judge_keys:
                value = normalize_judge_string(value)
                value = value[0]

        return value

    def fill_default_and_required_values(self, case: Dict) -> None:
        """Fill default values and propagate values shared between objects

        Many default fields are taken from Courtlistener's
        cl_scrape_opinions.make_objects

        :param case: nested object
        :return None
        """
        oc = case["Docket"]["OpinionCluster"]
        d = case["Docket"]

        # Default fields
        d["source"] = 2
        oc["source"] = "C"

        # Default if not filled
        if not oc.get("date_filed_is_approximate"):
            oc["date_filed_is_approximate"] = False
        if not oc.get("blocked"):
            oc["blocked"] = False
        if not d.get("blocked"):
            d["blocked"] = False

        # imitating cl_scrape_opinions.make_objects
        if d.get("blocked") and not d.get("date_blocked"):
            d["date_blocked"] = oc["date_blocked"] = date.today()

        if not oc.get("precedential_status"):
            oc["precedential_status"] = (
                self.status if self.status else "Unknown"
            )

        # Propagate fields
        if not oc.get("case_name") and d.get("case_name"):
            oc["case_name"] = d["case_name"]
        if not d.get("case_name") and oc.get("case_name"):
            oc["case_name"] = d["case_name"]
        if not d.get("case_name_short"):
            case_name_short = self.cnt.make_case_name_short(d["case_name"])
            d["case_name_short"] = oc["case_name_short"] = case_name_short

        # correct field shapes
        if oc.get("judges") and isinstance(oc["judges"], list):
            oc["judges"] = ";".join(oc["judges"])
        for op in oc["Opinions"]:
            if op.get("joined_by_str") and isinstance(
                op["joined_by_str"], list
            ):
                op["joined_by_str"] = ";".join(op["joined_by_str"])

    @staticmethod
    def sort_by_attributes(case: Dict, other_case: Dict) -> int:
        """Function passed as `key` argument to base `sort`
        Replaces AbstractSite._date_sort

        Keeping the order of attributes as OpinionSite ensures we have the same order of cases
        Order is important because a hash is calculated from ordered case names

        :param case: cleaned case
        :param other_case: another cleaned case
        :return 1 if first case is greater than second case
                0 if they are equal
                -1 if first case is less than second
        """
        oc = case["Docket"]["OpinionCluster"]
        other_oc = other_case["Docket"]["OpinionCluster"]

        for index in range(3):
            if index == 0:
                value = oc["date_filed"]
                other_value = other_oc["date_filed"]
            elif index == 1:
                value = case["Docket"]["case_name"]
                other_value = other_case["Docket"]["case_name"]
            elif index == 2:
                value = oc["Opinions"][0]["download_url"]
                other_value = other_oc["Opinions"][0]["download_url"]

            if value is None and other_value is None:
                continue
            elif other_value is None:
                return 1
            elif value is None:
                return -1

            if value == other_value:
                continue
            elif value > other_value:
                return 1
            else:
                return -1

        return 0

    def extract_from_text(self, scraped_text: str) -> Dict:
        """Parses Courtlistener's objects out of the download
        opinion document content

        :param scraped_text: May be HTML or plain_text
        :return: Dict in the format expected by Courtlistener
        """
        return {}
