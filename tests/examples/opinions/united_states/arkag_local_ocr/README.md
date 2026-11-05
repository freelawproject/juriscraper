# Additional complete OCR documents

These two fixtures contain unedited text from complete public PDFs processed
locally with Poppler 26.09.0 and Tesseract 5.5.3. They are **not Doctor
responses**. The recorded source and content hashes distinguish them from the
21 preserved Doctor responses in `../arkag_text`.

Render every page with `pdftoppm -r 200 -png`, run `tesseract PAGE stdout -l eng`
on pages in numerical order, and join the outputs with a form feed. The manifest
records source URLs, hashes, printed primary signers and expected extraction.

`2012-009` contains the exact local OCR spelling `DUSTIN M@&DANIEL`. The earlier
review example reported `DUSTIN M&DANIEL` for the same source. These two explicit
spellings map to the accepted name; arbitrary close names are not accepted.
The printed signing name was checked against the source page. OCR output varies
by extraction version, and Doctor was unavailable during this repair.

`2013-078` is signed by Chief Deputy Bradford J. Phelps and includes the older
opinion `2013-012` as an attachment. The complete OCR has two closings, so its
expected result is blank. A standalone Phelps closing tests his accepted name
and role separately; it cannot establish correct attribution for the bundle.
