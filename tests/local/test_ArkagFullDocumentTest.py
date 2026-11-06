"""Whole-document provenance and regressions supplement the boundary cases."""

import hashlib
import json
from pathlib import Path

import pytest

from juriscraper.opinions.united_states.attorney_general.arkag import Site

EXAMPLES = Path(__file__).parent.parent / "examples/opinions/united_states"


def test_preserved_doctor_responses_cover_every_backfill_year():
    root = EXAMPLES / "arkag_text"
    examples = json.loads((root / "manifest.json").read_text())["examples"]
    assert {int(example["docket"][:4]) for example in examples} == set(
        range(2012, 2027)
    )
    for example in examples:
        response = json.loads((root / example["response_file"]).read_text())
        content = response["content"]
        assert (
            hashlib.sha256(content.encode()).hexdigest()
            == example["content_sha256"]
        )
        assert response["extracted_by_ocr"] == example["extracted_by_ocr"]
        assert Site().extract_from_text(content) == example["expected"]


def test_additional_complete_local_ocr_documents():
    root = EXAMPLES / "arkag_local_ocr"
    for example in json.loads((root / "manifest.json").read_text())[
        "examples"
    ]:
        content = json.loads((root / example["fixture"]).read_text())[
            "content"
        ]
        assert (
            hashlib.sha256(content.encode()).hexdigest()
            == example["content_sha256"]
        )
        assert Site().extract_from_text(content) == example["expected"]


@pytest.mark.parametrize(
    "name",
    [
        "LESLIE RUTLAND",
        "TIM GRIFFITH",
        "ZACK MAYO",
        "BRADFORD J. PHELP",
        "DUSTIN M?DANIEL",
    ],
)
def test_near_names_are_not_whitelisted(name):
    role = (
        "Chief Deputy Attorney General"
        if name.startswith(("ZACK", "BRADFORD"))
        else "Attorney General"
    )
    assert Site().extract_from_text(f"Sincerely,\n{name}\n{role}\n") == {}


def test_exact_phelps_name_requires_the_deputy_role():
    assert Site().extract_from_text(
        "Sincerely,\nBRADFORD J. PHELPS\nChief Deputy Attorney General\n"
    ) == {
        "OpinionCluster": {
            "judges": "BRADFORD J. PHELPS, Chief Deputy Attorney General"
        }
    }
    assert (
        Site().extract_from_text(
            "Sincerely,\nBRADFORD J. PHELPS\nAttorney General\n"
        )
        == {}
    )


@pytest.mark.parametrize("name", ["DUSTIN M&DANIEL", "DUSTIN M@&DANIEL"])
def test_explicit_mcdaniel_ocr_spellings_remain_role_and_boundary_checked(
    name,
):
    text = f"Sincerely,\n{name}\nAttorney General\n"
    assert Site().extract_from_text(text) == {
        "OpinionCluster": {"judges": "DUSTIN McDANIEL, Attorney General"}
    }
    assert (
        Site().extract_from_text(
            text.replace("Attorney General", "Chief Deputy Attorney General")
        )
        == {}
    )
    assert (
        Site().extract_from_text(
            text + "\fSincerely,\nTIM GRIFFIN\nAttorney General\n"
        )
        == {}
    )
