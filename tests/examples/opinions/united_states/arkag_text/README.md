# Arkansas AG extraction fixtures

These JSON fixtures preserve the responses returned by Free Law Project's
Doctor `/extract/doc/text/?ocr_available=True` endpoint for complete source
PDFs. Tests consume the unedited `content` values.
They include a docket from every backfill year, 2012 through 2026, plus
regressions for missing signature text, preparers, split OCR names, delegated
issuance, and attached older opinions. Listing JSON fixtures test the API
metadata separately.

`manifest.json` records the exact source URL and SHA-256, the extracted-content
SHA-256 (UTF-8), whether Doctor used OCR, the visually checked signing official,
and the expected metadata. The PDFs are linked rather than committed.
Some source dockets are zero-padded differently from their PDF filenames;
use the recorded URL rather than constructing one from the docket.

Generated on 2026-11-04 using the official image:

```text
freelawproject/doctor@sha256:588afa7a7ed614ff74a2327b20582bb50f63828664d4358ae10f906bec8edc01
linux/amd64; pdftotext 25.03.0; Tesseract 5.5.0
```

For a local Doctor instance, an individual extraction can be reproduced with:

```python
import hashlib
import httpx

source_url = "https://opinionstorage.blob.core.windows.net/opinions/2015-094.pdf"
pdf = httpx.get(source_url).raise_for_status().content
print(hashlib.sha256(pdf).hexdigest())  # Compare with the manifest first.
response = httpx.post(
    "http://127.0.0.1:5050/extract/doc/text/",
    params={"ocr_available": "True"},
    files={"file": ("opinion.pdf", pdf, "application/pdf")},
    timeout=900,
).raise_for_status()
text = response.json()["content"]
```

Doctor may keep a PDF's existing text layer even when it loses a signature
name. A blank expected result deliberately preserves that uncertainty.
Names are never inferred solely from the letterhead, opinion preparer, year,
or footer initials. Whitespace inside a complete known name can be normalized.

`2015-0141` and `2017-0068` have substantial printed surname prefixes at the
signing line (`LESLIE RUTLED` and `LESLIE RUTLE`). They are recovered only with
independent corroboration: a complete matching name in the primary Arkansas
AG letterhead, a first-page opinion heading, consistent docket headings, one
recognizable closing, and the matching Attorney General title. The complete
first name and at least five surname letters must uniquely match a known AG,
with at most three missing terminal letters. Narrow ink-like punctuation is
allowed after the printed fragment; words, substituted letters, and conflicting
name evidence are not repaired. Delegation or recusal language blocks this
fallback. Complete signing names, including delegated Chief Deputy Zach Mayo,
continue to be read directly from the signing block.

Extraction locates a single official title on the closing page, then reads the
printed name immediately above it. Both exact-name extraction and recovery use
this same block; the title must end within 400 normalized characters of the
closing. Horizontal whitespace is normalized once, with line and page boundaries
preserved.

Before either direct extraction or recovery, the entire closing page is checked
for competing official titles and signing bylines, including material beyond the
400-character signing range or below an enclosure marker. Additional
unclassified text after the title and before numbered footnotes causes
abstention; only blank/ink lines, enclosure labels, and the observed reference-code
layout are ignored there. Reference codes never supply a signing identity.

The recovery fallback screens the untruncated PDF text for delegation or recusal.
This preserves primary-page footnotes below `Enclosure`, and conservatively
refuses recovery even if the relevant language occurs in attached material.
Complete, unambiguous deputy signatures remain readable directly.

Attribution also remains blank when the complete PDF contains competing
recognizable closings, including likely damaged `Sincer...` closing lines.
The parser does not choose the first or last signed document in that case,
even when an enclosure marker is present. This favors precision over recovering
the main signer from bundles of signed documents. Spaces and tabs in a title
or before the closing comma are normalized; title words on different lines
are not joined.

The malformed closing, punctuated boundary, quoted-letter ambiguity, and
horizontal title- and closing-spacing cases in `test_ArkagTest.py` are synthetic regression
tests, separate from these 21 real-document responses. The boundary guards
do not provide general document segmentation or arbitrary OCR repair.
Later competing signers and delegation footnotes below enclosure markers are
also synthetic regression cases. Missing page/footnote boundaries, unrecognized
titles, and wholly garbled evidence remain limits of plain-text attribution.

The main signatures in `2013-001` and `2013-149` precede enclosures with
different signers. `2026-118` is signed by Chief Deputy Zach Mayo after the
AG delegated issuance; its preparer is Kelly Summerside. These distinctions
must survive extraction.

`2013-149`, `2014-0137`, and `2015-094` remain blank. Their short or missing
signing names are not replaced using correspondence initials. A separate
90-PDF native-text survey (not additional Doctor fixtures) found eight visually
checked footer-code examples, but no delegated-signer example with such a
code. This does not establish that a code identifies the actual signer rather
than the official responsible for preparing or issuing correspondence.
