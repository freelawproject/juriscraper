# Scraper Guidelines

These guidelines apply to both opinion and oral argument scrapers.

## Issue Creation

**Structure:**
- The title should include the failing scraper ID or court name and a description. Example: "`conn` scraper failing"
- If referencing data in the source website, include a link to the source website.
- If referencing data in Courtlistener (date range with 0 opinions, an opinion with bad data, etc) include a Courtlistener link
- Include error messages / stack traces from Sentry or logs
- Reference Sentry issue IDs when applicable
  - Sentry links let reviewers count occurrences, see affected courts, and trace exact failing records. Any proposed fix should address those specific occurrences.
- Show data examples (screenshots, SQL counts, specific records) to illustrate the problem
  - Reviewers need real edge cases to verify fixes against. Without examples, PRs get reviewed blindly and bugs slip through.
  - If the issue is getting to big, use the `<details><summary>Title of collapsible section</summary>A lot of content</details>` tags to organize extra info.
- Reference related issues with `#number`
- For backscrape issues: specify the date range and expected opinion counts
  - The person running the backscrape needs the expected yield to verify completeness.

**Content standards:**
- One issue per scraper/court unless they share a root cause
- Quantify the impact (e.g., "10,586 events in the last 30 days", "missing opinions from May to December")
  - Prioritization depends on knowing if it's 5 missed opinions or 10,000. Also sets the bar for verifying the fix worked.
- For data quality issues: include specific examples of bad vs expected values
- For site changes: note old vs new URL/format
- Discuss implementation ideas in the issue before opening a PR
  - Avoids the PR itself becoming the design discussion. Aim for a polished starting point.

## Code Review and new scrapers

**Never skip silently:**
- Always use `logger.warning` or `logger.error` when skipping rows
  - Silent skips cause the most difficult kind of missing opinions in prod.
- `logger.error` for skips worth tracking in Sentry; `logger.warning` for expected/low-priority skips
- Sentry error messages should be easy to read in the feed: `"ky: no document details returned for Docket %s"`
- Better to miss a metadata field than to miss a whole document
  - A document with only a docket number is still valuable in CL. Skipping for missing non-essential fields (status, date, summary) loses the opinion entirely.
- Prefer letting the scraper crash over silently losing data
  - Adding error handling to an already-failed download just obscures the real problem. If the site changed, we need to know.

**Example files and testing:**
- Use real data from the source, not synthetic data
  - Real data captures encoding quirks, edge cases, and unexpected fields that synthetic data misses.
- Auto-generate example compare files via: `python -m unittest -v tests.local.test_ScraperExampleTest juriscraper.opinions`
  - Manually created compare files drift from actual scraper output. The test command generates them from saved responses.
- Test both scraper AND backscraper with `sample_caller`.
  - Backscrapers often have separate URL-building/pagination logic that breaks independently. Use `--save-responses` to save downloaded files to `/tmp/juriscraper/` for debugging.
- Verify scraped values make sense (dates not inverted, docket numbers not citations, correct court)
- Check example files for edge cases
- Update example compare files when modifying scraper logic
- When creating `extract_from_text` tests, use real data and include the real example link to Courtlistener or to the source
  - To test this, use `python -m unittest -v tests.local.test_ScraperExtractFromText`

**Code style:**
- Use `from urllib.parse import urljoin` for URL building
- Use `juriscraper.lib.string_utils.titlecase` for case names
- OpinionSiteLinear: process case-by-case in `_process_html`, not attribute-by-attribute
  - Processing all names, then all dates, then all URLs duplicates iteration and makes it harder to see what each case contains.
- Don't override AbstractSite behavior unnecessarily
- Don't add test-mode-specific code (`if self.test_mode_enabled()`) when the base class handles it
  - The base class already manages test mode. Adding checks creates redundant, divergent code paths.
- Use `self.request["parameters"]` instead of custom request logic
  - AbstractSite calls `save_response` after each request. In prod, responses are saved to S3 for debugging/auditing. Custom request logic bypasses this.
- Imports at top level, not inside functions
- Add comments when logic isn't self-evident from the code
- Add issue references (`#1234`) in skip/workaround comments where context is too big for a single comment
- Delete unused code
- Add type annotations and docstrings to new public methods
- Prefer simpler regex: drop unnecessary `(?:)` non-capturing groups, use `s?` not `(?:s)?`
- Limit text searches to first N characters when pattern is expected near the start (e.g., `scraped_text[:1000]`)
- Walrus operator for match-and-assign: `if match := pattern.search(text):`

**Exception handling:**
- Be specific about exception types
  - e.g., Python's `ConnectionError` and `requests.exceptions.ConnectionError` are unrelated classes. Catching the wrong one silently misses the actual error.
- Don't catch errors too broadly in AbstractSite — failures there are important
- `InvalidDocumentError` only works in `cleanup_content`, not in `_process_html`
  - In `_process_html`, this exception stops the entire scrape. In `cleanup_content`, it skips just that one document. Misusing it loses all remaining opinions.

**Data quality:**
- Verify case names are from the correct court
- Check that docket numbers aren't actually citations or dates
- Verify each date value is going to the correct date field (for example, date_filed vs other_dates)
- Return empty dict `{}` from `extract_from_text` when no match
  - Returning `{"appeal_from_str": ""}` overwrites an existing value. Returning `{}` preserves whatever CL already has.
- Use `date_filed_is_approximate = True` when exact dates aren't available; don't set unrealistic dates
- `"Unknown"` status when status can't be determined, not `"Published"`
- Try to parse the most amount of data possible. If a source shows the author of an opinion, the disposition, a summary, etc; try to pick it up. If there is some interesting field you don't know where to fit in the accepted return keys, highlight it to the user so they can research.
- If a source shows different opinion types for the same case, consider using `ClusterSite` as a base class to group those together.

**PR requirements:**
- Every PR must update `CHANGES.md` citing the original issue number
- Research root cause before fixing — understand why it fails
  - Fixing the exception without understanding it can ingest unwanted documents (motions, non-opinions) into the DB.
- Run the scraper and verify output before submitting
- Keep backscrape default date ranges reasonable (e.g., 30 days, not 100)
  - A 100-day default means every hourly scrape requests 100 days of data. 10-30 days is enough for the regular scraper; `--backscrape` handles historical ranges.
