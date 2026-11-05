"""Synthetic adversarial cases complementing the real PDF fixtures."""

import pytest

from juriscraper.opinions.united_states.attorney_general.arkag import Site


@pytest.mark.parametrize(
    "text",
    [
        "Sincerely,\nLESLIE RUTLE\nAttorney General\n",
        "Sincerely,\nGARBLED OCR\nAttorney General\n",
        "Sincerely,\nLESLIE RUT1EDGE\nAttorney General\n",
        "Sincerely,\nTIM GRIFFIN\nChief Deputy Attorney General\n",
        "Sincerely,\nZACH MAYO\nAttorney General\n",
        "TIM GRIFFIN\nAttorney General\n\nSincerely,\n~~\nAttorney General\n",
        "Deputy Attorney General Elisabeth A. Walker prepared this opinion.\n"
        "Sincerely,\n~~\nAttorney General\n",
        # A later attachment must not fill a missing current signature.
        "Sincerely,\n~~\nAttorney General\n\f"
        "Attached opinion\nSincerely,\nTIM GRIFFIN\nAttorney General\n",
        # PDF extractors can omit page separators between documents.
        "Sincerely,\n~~\nAttorney General\n"
        "Attached opinion\nSincerely,\nTIM GRIFFIN\nAttorney General\n",
        # A damaged main closing must not expose an enclosure's signer.
        "Unrecognizable signature\nAttorney General\nEnclosure\n\f"
        "Attached opinion\nSincerely,\nTIM GRIFFIN\nAttorney General\n",
        # A quoted mention in a paragraph is not a closing line.
        'The letter ends with "Sincerely".\nTIM GRIFFIN\nAttorney General\n',
    ],
)
def test_uncertain_signers_are_not_emitted(text):
    assert Site().extract_from_text(text) == {}


def test_ocr_whitespace_does_not_change_a_complete_known_name():
    text = "Sincerely,\r\nLESLIE\u00a0RUTLEDG E\r\nAttorney General\r\n"
    assert Site().extract_from_text(text) == {
        "OpinionCluster": {"judges": "LESLIE RUTLEDGE, Attorney General"}
    }


def test_multiple_signed_opinions_are_ambiguous_even_with_enclosure_marker():
    text = (
        "Sincerely,\nDUSTIN McDANIEL\nAttorney General\nEnclosure.\n\f"
        "Attached opinion\nSincerely,\nTIM GRIFFIN\nAttorney General\n"
    )
    assert Site().extract_from_text(text) == {}


def test_unsigned_enclosure_does_not_replace_the_current_signer():
    text = (
        "Sincerely,\nDUSTIN McDANIEL\nAttorney General\nEnclosure.\n\f"
        "Attached ballot form without a signing official.\n"
    )
    assert Site().extract_from_text(text) == {
        "OpinionCluster": {"judges": "DUSTIN McDANIEL, Attorney General"}
    }


@pytest.mark.parametrize(
    "marker", ["Enclosure.", "Enclosures:", "Attachment."]
)
def test_punctuated_boundary_blocks_a_damaged_main_closing(marker):
    text = (
        "Sincerelv,\n~~\nAttorney General\n"
        f"{marker}\n\fAttached opinion\n"
        "Sincerely,\nLESLIE RUTLEDGE\nAttorney General\n"
    )
    assert Site().extract_from_text(text) == {}


@pytest.mark.parametrize("main_closing", ["Sincerely,", "Sincerelv,"])
@pytest.mark.parametrize("quoted_boundary", ["", "Enclosure.\n"])
def test_competing_quoted_and_main_closings_are_ambiguous(
    main_closing, quoted_boundary
):
    text = (
        "An earlier letter is quoted below:\n"
        "Sincerely,\nLESLIE RUTLEDGE\nAttorney General\n"
        f"{quoted_boundary}"
        "The current opinion continues after the quotation.\n"
        f"{main_closing}\nTIM GRIFFIN\nAttorney General\n"
    )
    assert Site().extract_from_text(text) == {}


def test_unmarked_opinions_with_competing_closings_are_ambiguous():
    text = (
        "Sincerely,\nDUSTIN McDANIEL\nAttorney General\n\f"
        "Attached opinion\nSincerely,\nTIM GRIFFIN\nAttorney General\n"
    )
    assert Site().extract_from_text(text) == {}


@pytest.mark.parametrize(
    ("name", "title", "expected"),
    [
        ("TIM GRIFFIN", "Attorney  General", "TIM GRIFFIN, Attorney General"),
        ("TIM GRIFFIN", "Attorney\tGeneral", "TIM GRIFFIN, Attorney General"),
        (
            "ZACH MAYO",
            "Chief\t Deputy  Attorney \tGeneral",
            "ZACH MAYO, Chief Deputy Attorney General",
        ),
    ],
)
def test_horizontal_title_whitespace_is_normalized(name, title, expected):
    assert Site().extract_from_text(f"Sincerely,\n{name}\n{title}\n") == {
        "OpinionCluster": {"judges": expected}
    }


@pytest.mark.parametrize(
    ("name", "title"),
    [
        ("TIM GRIFFIN", "Attorney\nGeneral"),
        ("ZACH MAYO", "Chief\nDeputy Attorney General"),
    ],
)
def test_vertical_title_whitespace_is_not_joined(name, title):
    assert Site().extract_from_text(f"Sincerely,\n{name}\n{title}\n") == {}


def test_default_backfill_excludes_columbia_import_years():
    site = Site()
    assert site.back_scrape_iterable[0] == 2012
    assert Site(
        backscrape_start=2015, backscrape_end=2016
    ).back_scrape_iterable == [
        2015,
        2016,
    ]


@pytest.mark.parametrize("spacing", [" ", "\t", " \t ", "  "])
def test_horizontal_whitespace_before_closing_comma_is_normalized(spacing):
    text = f"Sincerely{spacing},\nTIM GRIFFIN\nAttorney General\n"
    assert Site().extract_from_text(text) == {
        "OpinionCluster": {"judges": "TIM GRIFFIN, Attorney General"}
    }


@pytest.mark.parametrize("closing", ["Sincerelv ,", "Sincerely ."])
def test_closing_whitespace_does_not_repair_damaged_words_or_punctuation(
    closing,
):
    text = f"{closing}\nTIM GRIFFIN\nAttorney General\n"
    assert Site().extract_from_text(text) == {}
