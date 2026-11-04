# Arkansas AG extraction fixtures

These are unedited Doctor responses for 21 complete Arkansas AG opinion PDFs,
with at least one opinion from each year, 2012-2026. Tests read each response's
`content`; the listing fixtures test API metadata separately.

`manifest.json` records each source URL and PDF SHA-256, the UTF-8 content
SHA-256, OCR status, visually checked signer, and expected result. The PDFs are
linked rather than committed. Use the recorded URL: docket and filename padding
sometimes differ.

Generated on 2026-11-04 with the official image:

```text
freelawproject/doctor@sha256:588afa7a7ed614ff74a2327b20582bb50f63828664d4358ae10f906bec8edc01
linux/amd64; pdftotext 25.03.0; Tesseract 5.5.0
```

To reproduce a response with Doctor running locally:

```python
import hashlib
import httpx

source_url = "https://opinionstorage.blob.core.windows.net/opinions/2015-094.pdf"
pdf = httpx.get(source_url).raise_for_status().content
print(hashlib.sha256(pdf).hexdigest())  # Check source_sha256 before extracting.
response = httpx.post(
    "http://127.0.0.1:5050/extract/doc/text/",
    params={"ocr_available": "True"},
    files={"file": ("opinion.pdf", pdf, "application/pdf")},
    timeout=900,
).raise_for_status()
text = response.json()["content"]
print(hashlib.sha256(text.encode("utf-8")).hexdigest())  # Check content_sha256.
```

Use the pinned image and compare both hashes with the manifest. Different
Doctor versions may produce different text.

The JSON responses are real document extractions. `test_ArkagTest.py` and
`test_ArkagRecoveryTest.py` add synthetic cases for damaged OCR, conflicting
signers, whitespace, and ambiguous document boundaries.

Five fixtures intentionally return no signer. In `2015-094`, for example,
Doctor loses the printed name; the preparer must not be substituted. A year,
letterhead, or footer initials alone cannot establish who signed.

Two truncated Rutledge signatures (`2015-0141` and `2017-0068`) are recovered
only with a complete first name, at least five surname letters (at most three
missing), and matching primary letterhead, title, and docket. Conflicting
evidence or delegation/recusal language blocks that fallback. Complete deputy
signatures, such as Zach Mayo in `2026-118`, are read directly.

This is conservative text extraction, not general document segmentation or OCR
repair. Signed attachments, missing page/footnote boundaries, and unrecognized
or garbled signing evidence can prevent attribution.
