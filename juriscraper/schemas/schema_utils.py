import json
from pathlib import Path
from typing import Dict, List, Union

import requests
from jsonschema import Draft7Validator
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

    Previous function won't work with docket
    """
    gh = "https://raw.githubusercontent.com/grossir/juriscraper/new_opinion_site_subclass/juriscraper/schemas/"
    uri = uri.replace("https://courtlistener.com/schemas/", gh)

    return Resource.from_contents(requests.get(uri).json())


class SchemaValidator:
    """
    The JSON schemas map closely to Courtlistener's Django Models
    They are missing "Reference" or foreign key fields, which need to be
    looked up in the DB and will be built up using some string values
    For example: OpinionCluster.judges, or Opinion.author_str

    Some extra fields:
    OpinionCluster.citation_strings
        Citations are parsed using `eyecite` on the caller side, so we pass
        them as strings if we find them. Some citations may be passed as
        proper objects, when the parsing is straightforward

    About types:
    JSON format does not support "date" or "datetime" types, but it can
    enforce the "date" format on a string
    Luckily, the date-like values we collect are all "dates", which reduces
    the complexity of also supporting "datetime"
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

        Draft7Validator.check_schema(docket_schema.value.contents)
        self.validator = Draft7Validator(
            docket_schema.value.contents, registry=registry
        )

    def validate(self, obj: Union[Dict, List]):
        self.validator.validate(obj)
