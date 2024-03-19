import json
from pathlib import Path
from typing import Dict

import requests
from jsonschema import Draft7Validator, FormatChecker
from referencing import Registry, Resource, exceptions


def retrieve_from_filesystem(uri: str):
    """Resolve the schema URLs to Juriscraper's folder organization

    :param uri: URL value of $ref / $id in a schema
    :return: content of schema
    """
    schema_folder = Path(__file__).parent
    path = schema_folder / Path(
        uri.replace("https://courtlistener.com/schemas/", "")
    )
    contents = json.loads(path.read_text())

    return Resource.from_contents(contents)


def retrieve_from_github(uri: str):
    """Retrieve JSON from github

    `retrieve_from_filesystem` won't work with Docker

    :param uri: URL value of $ref / $id in a schema
    :return: content of schema
    """
    # TODO: this will need to be changed to the proper repo before merge
    gh = "https://raw.githubusercontent.com/grossir/juriscraper/new_opinion_site_subclass/juriscraper/schemas/"
    uri = uri.replace("https://courtlistener.com/schemas/", gh)

    return Resource.from_contents(requests.get(uri).json())


class SchemaValidator:
    """
    The JSON schemas map closely to Courtlistener's Django Models
    They are missing "Reference" or foreign key fields, which need to be
    looked up in the DB and will be built up using some string values
    For example: OpinionCluster.judges or Opinion.author_str

    Some extra fields that do not map to the Django/DB models:
    OpinionCluster.citation_strings
    Citations are parsed using `eyecite` on the caller side, so we pass
    them as strings if we find them. Some citations may be passed as
    proper objects, when the parsing is straightforward

    About types:
    JSON format does not support "date" or "datetime" types, but it can
    enforce the "date" format on a "string" type. This requires the package
    `rfc3339-validator`
    In order for the format checker to work, a FormatChecker object must
    be explicitly passed to the validator instance

    About `"additionalProperties": false` in the schemas:
    By default, the schema allows any unspecified property
    In Courtlistener we create objects from the returned JSON like this::
    `opinion = Opinion(**opinion_json)`
    so any additional property not expected by the model will break it
    """

    def __init__(self):
        """
        $id and $ref in the JSON Schema are URLs.
        Since we are serving these from files, we need to create a special Registry
        """
        docket_schema_id = "https://courtlistener.com/schemas/Docket.json"
        try:
            registry = Registry(retrieve=retrieve_from_filesystem)
            docket_schema = registry.get_or_retrieve(docket_schema_id)
        except exceptions.Unretrievable:
            registry = Registry(retrieve=retrieve_from_github)
            docket_schema = registry.get_or_retrieve(docket_schema_id)

        self.validator = Draft7Validator(
            docket_schema.value.contents,
            registry=registry,
            format_checker=FormatChecker(),
        )

    def validate(self, obj: Dict) -> None:
        """Calls the validator

        :raises: ValidationError if the object is invalid
        """
        self.validator.validate(obj)
