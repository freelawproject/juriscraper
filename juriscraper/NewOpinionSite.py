from datetime import datetime
from functools import cmp_to_key
from typing import Callable

from jsonschema import Draft7Validator, FormatChecker

from juriscraper.AbstractSite import AbstractSite, logger
from juriscraper.lib.string_utils import (
    clean_string,
    convert_date_string,
    harmonize,
)
from juriscraper.OpinionSite import OpinionSite
from juriscraper.schemas.scraper_schema import validation_schema

opinion_site = OpinionSite()
opinion_site_ordered_attributes = opinion_site._all_attrs
del opinion_site


class NewOpinionSite(AbstractSite):
    short_to_full_key = {
        "citation": "citations",
        "name": "case_names",
        "docket": "docket_numbers",
        "date": "case_dates",
        "url": "download_urls",
        "judge": "judges",
        "lower_court": "lower_courts",
    }
    default_fields = {
        "date_filed_is_approximate": False,
        "blocked_statuses": False,
    }

    def __init__(self, cnt=None):
        super().__init__()
        self.cases = []

        self.validator = Draft7Validator(
            validation_schema, format_checker=FormatChecker()
        )

    def __iter__(self):
        for case in self.cases:
            yield case

    def __getitem__(self, index: int):
        return self.cases[index]

    def __len__(self) -> int:
        return len(self.cases)

    def parse(self):
        """Overrides AbstractSite.parse"""
        if not self.downloader_executed:
            # Run the downloader if it hasn't been run already
            self.html = self._download()

            # Process the available html (optional)
            self._process_html()

        self._post_parse()

        # Instead of self._check_sanity()
        # date type validation, non-empty validation, etc will be done by JSON Schema validator
        clean_cases = []
        for case in self.cases:
            clean_case = self.clean_case(case)
            self.fill_default_values(clean_case)

            try:
                self.validator.validate(clean_case)
            except Exception as e:
                # TODO: need to write custom validator for case with Deferred values,
                # which are functions to be called
                if "bound method" not in str(e):
                    raise e

            clean_cases.append(clean_case)

        self.cases = clean_cases
        self.cases.sort(key=cmp_to_key(self.sort_by_attributes))

        # This is an example of something in Juriscraper that is exclusively used in CL
        # and that should be put there
        self.case_names = [case["case_names"] for case in self.cases]
        self._make_hash()

        # Only for showing
        for case in self.cases:
            self.get_deferred_values(case)

        return self

    def fill_default_values(self, case) -> None:
        """Required fields"""
        for key, default_value in self.default_fields.items():
            if case.get(key) is None:
                case[key] = default_value

    def get_deferred_values(self, case) -> None:
        """Use this function to consume deferred values
        Deferred values are functions that wait until execution to perform
        the requests, usually after duplication has been checked by the caller

        If a single deferring_function scrapes multiple fields, it is better to
        repeat it in every field, for clarity

        For example:

        ```
        # Use functools.partial to pass an argument to a function
        # without calling it

        docket_number = "2023-23"
        deferred_function = partial(self.scrape_detail,
                                    docket_number=docket_number)

        self.cases.append({
            "case_dates": date(2024, 01, 01),
            "judge": deferred_function,
            "citation": deferred_function,
            "lower_court": some_other_function,
        })
        ```
        """
        update_values = {}
        seen_callables = set()

        for value in case.values():
            if isinstance(value, Callable) and value not in seen_callables:
                deferred_dict = value()
                deferred_dict = self.clean_case(deferred_dict)
                logger.info("Got deferred values %s", str(deferred_dict))
                update_values.update(deferred_dict)
                seen_callables.add(value)

        case.update(update_values)

    @staticmethod
    def sort_by_attributes(case, other_case) -> int:
        """Replaces AbstractSite._date_sort
        Keeping the order of attributes as OpinionSite ensures we have the same order of cases
        """
        for attr in opinion_site_ordered_attributes:
            value = case.get(attr)
            other_value = other_case.get(attr)

            if value is None and other_value is None:
                continue
            elif other_value is None:
                return 1
            elif value is None:
                return -1

            if value == other_value:
                return 0
            elif value > other_value:
                return 1
            else:
                return -1

    @classmethod
    def clean_case(cls, case) -> None:
        """Replaces AbstractSite._clean_attributes

        Clean case dict in place
        """
        clean_case = {}

        for key, value in case.items():
            if key == "download_urls":
                value = value.strip()
            else:
                if "date" in key:
                    value = str(convert_date_string(value))
                elif isinstance(value, datetime):
                    value = str(value.date())
                elif isinstance(value, str):
                    value = clean_string(value)

                if key in ["case_names", "docket_numbers"]:
                    value = harmonize(value)

            clean_key = cls.short_to_full_key.get(key, key)
            clean_case[clean_key] = value

        return clean_case
