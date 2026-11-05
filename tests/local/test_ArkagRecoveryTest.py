"""Synthetic constraints on recovery, separate from real Doctor fixtures."""

import pytest

from juriscraper.opinions.united_states.attorney_general.arkag import Site

HEADER = (
    "STATE OF ARKANSAS\nATTORNEY GENERAL\nLESLIE RUTLEDGE\n\n"
    "Opinion No. 2017-068\n\n"
)


def opinion(
    name="LESLIE RUTLE", *, header=HEADER, body="", title="Attorney General"
):
    return f"{header}{body}\nSincerely,\n~/~\n{name}\n{title}\n"


@pytest.mark.parametrize(
    "text",
    [
        opinion(name="~~"),  # Header alone is insufficient.
        opinion(name="~~") + "LR/EAW:cyh\n",  # Initials do not replace a name.
        opinion(name="LESLIE"),
        opinion(name="LESLIE RUTL"),  # Too little surname evidence.
        opinion(name="LESLIE RUT1E"),  # No substituted-letter repair.
        opinion(name="LESLIE RUTLAND"),
        opinion(name="LESLIE RUTLEDGER"),
        opinion(name="JANE RUTLED"),
        opinion(name="LESLIE RUTLE JR."),
        opinion(name="LESLIE RUTLEDGE JR."),
        opinion(name="LESLIE RUTLED ,JR."),
        opinion(name="LESLIE RUTLED-ANN"),
        opinion(name="ANOTHER OFFICIAL\nLESLIE RUTLE"),
        opinion(name="ΩΩΩ\nLESLIE RUTLE"),
        opinion(header=HEADER.replace("LESLIE RUTLEDGE", "TIM GRIFFIN")),
        opinion(header=HEADER.replace("LESLIE RUTLEDGE", "UNKNOWN OFFICIAL")),
        opinion(header=HEADER.replace("Opinion No. 2017-068", "")),
        opinion(header="A quoted letterhead:\n" + HEADER),
        opinion(body=HEADER.replace("LESLIE RUTLEDGE", "TIM GRIFFIN")),
        opinion(body="Opinion No. 2016-001\n"),
        opinion(body="The Attorney General recused and delegated issuance.\n"),
        opinion(body="An acting Attorney General issued this opinion.\n"),
        opinion(title="Chief Deputy Attorney General"),
        opinion(title="Deputy Attorney General"),
        HEADER + "Sincerelv,\n~~\nAttorney General\nEnclosure.\n" + opinion(),
    ],
)
def test_corroboration_does_not_override_conflicting_or_insufficient_evidence(
    text,
):
    assert Site().extract_from_text(text) == {}


def test_complete_delegated_signer_does_not_depend_on_the_letterhead():
    text = opinion(
        name="ZACH MAYO",
        header=HEADER.replace("LESLIE RUTLEDGE", "TIM GRIFFIN"),
        body="The AG recused and delegated issuance to the Chief Deputy.\n",
        title="Chief Deputy Attorney General",
    )
    assert Site().extract_from_text(text) == {
        "OpinionCluster": {
            "judges": "ZACH MAYO, Chief Deputy Attorney General"
        }
    }


def test_complete_other_signer_is_not_replaced_by_the_header_name():
    assert Site().extract_from_text(opinion(name="TIM GRIFFIN")) == {
        "OpinionCluster": {"judges": "TIM GRIFFIN, Attorney General"}
    }


def test_short_corrupted_name_and_initials_are_not_sufficient():
    text = (
        opinion(
            name="DUSTIN Me",
            header=HEADER.replace("LESLIE RUTLEDGE", "DUSTIN McDANIEL"),
        )
        + "DM:JMB/cyh\n"
    )
    assert Site().extract_from_text(text) == {}


@pytest.mark.parametrize("name", ["LESLIE RUTLE", "LESLIE RUTLEDGE"])
@pytest.mark.parametrize(
    "extra_signer",
    [
        "TIM GRIFFIN\nAttorney General\n",
        "By: NICHOLAS BRONNI\nDeputy Attorney General\n",
        "By: NICHOLAS BRONNI\n",
        "NICHOLAS BRONNI\n",
        "nicholas\nbronni\n",
        "ΩΩΩ\n",
        "BRONNI\n",
        "Enclosure\nTIM GRIFFIN\nAttorney General\n",
        "\n" * 450 + "TIM GRIFFIN\nAttorney General\n",
    ],
    ids=[
        "second-ag",
        "by-deputy",
        "by-name",
        "unlabelled-name",
        "split-lowercase-name",
        "unicode-name",
        "single-name-fragment",
        "after-enclosure",
        "late-primary-page",
    ],
)
def test_later_competing_signer_blocks_assignment(name, extra_signer):
    assert Site().extract_from_text(opinion(name=name) + extra_signer) == {}


@pytest.mark.parametrize(
    "footnote",
    [
        "Enclosure\n36 The Attorney General recused and delegated issuance.\n",
        "Enclosure.\n36 The Attorney General recused and delegated issuance.\n\fAttachment",
        "Enclosure\n\f36 The Attorney General recused and delegated issuance.\n",
    ],
)
def test_enclosure_does_not_hide_delegation_evidence(footnote):
    assert Site().extract_from_text(opinion() + footnote) == {}


def test_ordinary_primary_page_footnote_does_not_prevent_recovery():
    text = (
        opinion()
        + "Enclosure\n21 Ark. Code Ann. § 7-9-107(c).\n\fBallot text.\n"
    )
    assert Site().extract_from_text(text) == {
        "OpinionCluster": {"judges": "LESLIE RUTLEDGE, Attorney General"}
    }


def test_complete_delegated_signer_keeps_primary_page_footnote():
    text = (
        opinion(
            name="ZACH MAYO",
            header=HEADER.replace("LESLIE RUTLEDGE", "TIM GRIFFIN"),
            title="Chief Deputy Attorney General",
        )
        + "Enclosure\n36 The Attorney General recused and delegated issuance to Mayo.\n"
    )
    assert Site().extract_from_text(text) == {
        "OpinionCluster": {
            "judges": "ZACH MAYO, Chief Deputy Attorney General"
        }
    }


def test_explicit_next_page_attachment_is_outside_the_signing_block():
    text = (
        opinion()
        + "Enclosure\n\fAttached letter\nTIM GRIFFIN\nAttorney General\n"
    )
    assert Site().extract_from_text(text) == {
        "OpinionCluster": {"judges": "LESLIE RUTLEDGE, Attorney General"}
    }


@pytest.mark.parametrize("reference", ["LR/RO:cyh", "LR/cyh"])
def test_reference_layout_is_not_used_to_identify_a_signer(reference):
    assert Site().extract_from_text(opinion() + reference + "\n") == {
        "OpinionCluster": {"judges": "LESLIE RUTLEDGE, Attorney General"}
    }
    assert (
        Site().extract_from_text(opinion(name="~~") + reference + "\n") == {}
    )
