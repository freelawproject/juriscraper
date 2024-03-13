import unittest
from copy import deepcopy

from jsonschema.exceptions import ValidationError

from juriscraper.schemas.schema_validator import SchemaValidator


class RequiredProperties:
    """Container class for related tests"""

    case_name = "Example case v. Validation"
    date_filed = "2023-11-12"

    ## Missing required attribute in Docket
    invalid_object = {
        "Docket": {
            "case_name": case_name,
        }
    }

    ## missing required attributes in OpinionCluster
    invalid_object_first_level = {
        "Docket": {
            "docket_number": "11234",
            "case_name": case_name,
            "OpinionCluster": {
                "date_filed": date_filed,
            },
        }
    }

    ## missing required attributes in Opinion
    invalid_object_second_level = {
        "Docket": {
            "docket_number": "11234",
            "case_name": case_name,
            "OpinionCluster": {
                "date_filed": date_filed,
                "date_filed_is_approximate": False,
                "case_name": case_name,
                "precedential_status": "Published",
                "Opinions": [{"author_str": "A Judge"}],
            },
        }
    }
    invalid_object_second_level_no_opinions = deepcopy(
        invalid_object_second_level
    )
    invalid_object_second_level_no_opinions["Docket"]["OpinionCluster"][
        "Opinions"
    ] = []

    invalid_tests = [
        invalid_object,
        invalid_object_first_level,
        invalid_object_second_level,
        invalid_object_second_level_no_opinions,
    ]

    # Valid object
    valid_object = {
        "Docket": {
            "docket_number": "11234",
            "case_name": case_name,
            "OpinionCluster": {
                "date_filed": date_filed,
                "date_filed_is_approximate": False,
                "case_name": case_name,
                "precedential_status": "Published",
                "Opinions": [{"download_url": "https://courtlistener.com"}],
            },
        }
    }


class TypeTests:
    """Container class for related tests"""

    valid_object = RequiredProperties.valid_object

    invalid_boolean_type = deepcopy(valid_object)
    invalid_boolean_type["Docket"]["OpinionCluster"][
        "date_filed_is_approximate"
    ] = "False"

    invalid_opinion_enum = deepcopy(valid_object)
    invalid_opinion_enum["Docket"]["OpinionCluster"]["Opinions"][0][
        "type"
    ] = "Something"

    invalid_date_string = deepcopy(valid_object)
    invalid_date_string["Docket"]["OpinionCluster"][
        "date_filed"
    ] = "2023/12/30"

    not_a_date = deepcopy(valid_object)
    not_a_date["Docket"]["OpinionCluster"]["date_filed"] = "Not a date"

    inexistant_date_string = deepcopy(valid_object)
    inexistant_date_string["Docket"]["OpinionCluster"][
        "date_filed"
    ] = "2023-13-32"

    all_tests = [
        invalid_boolean_type,
        invalid_opinion_enum,
        invalid_date_string,
        not_a_date,
        inexistant_date_string,
    ]


class OptionalObjectsTest:
    """Container class for related tests"""

    valid_object = RequiredProperties.valid_object

    citation = {
        "volume": 123,
        "reporter": "Misc 3d",
        "page": "20",
        "type": 2,
    }
    valid_citation = deepcopy(valid_object)
    valid_citation["Docket"]["OpinionCluster"]["Citations"] = [citation]

    invalid_citation = deepcopy(valid_object)
    cit = deepcopy(citation)
    cit["volume"] = "123"
    invalid_citation["Docket"]["OpinionCluster"]["Citations"] = [cit]

    oci = {
        "docket_number": "02-20-00075-CV",
        "assigned_to_str": "E. Lee Gabriel",
        "date_judgment": "2022-01-13",
    }
    valid_oci = deepcopy(valid_object)
    valid_oci["Docket"]["OriginatingCourtInformation"] = oci

    # Has a property not included in OCI schema
    other_oci = deepcopy(oci)
    other_oci["appeal_from_str"] = "texapp"
    invalid_oci = deepcopy(valid_object)
    invalid_oci["Docket"]["OriginatingCourtInformation"] = other_oci


class OpinionSchemasValidationTest(unittest.TestCase):
    """Test that schema validator works as expected"""

    def setUp(self):
        self.validator = SchemaValidator()

    def test_required_properties(self):
        """Check that `required` properties are enforced

        Note that required array types, such as Docket.OpinionCluster.Opinion
        should have a `minItems` attribute, not only be in `required`
        """
        for obj in RequiredProperties.invalid_tests:
            self.assertRaises(
                ValidationError, self.validator.validate, obj["Docket"]
            )

        self.validator.validate(RequiredProperties.valid_object["Docket"])

    def test_invalid_types(self):
        """Test that type (and format) specification work as expected

        Note that {"type":"string", "format": "date"}
        """
        for obj in TypeTests.all_tests:
            self.assertRaises(
                ValidationError, self.validator.validate, obj["Docket"]
            )

    def test_optional_schemas(self):
        """Test Citation, OriginatingCourtInformation schemas"""
        self.assertRaises(
            ValidationError,
            self.validator.validate,
            OptionalObjectsTest.invalid_citation["Docket"],
        )
        self.assertRaises(
            ValidationError,
            self.validator.validate,
            OptionalObjectsTest.invalid_oci["Docket"],
        )
        self.validator.validate(OptionalObjectsTest.valid_citation["Docket"])
        self.validator.validate(OptionalObjectsTest.valid_oci["Docket"])
