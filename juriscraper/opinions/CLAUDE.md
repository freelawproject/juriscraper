# Opinion Scrapers - AI Development Guidelines

This guide provides specific instructions for creating and reviewing opinion scrapers in the `juriscraper/opinions/` module. These guidelines are **module-specific** and do not affect PACER scrapers or other modules.

## Module Overview

### Purpose
The opinions module scrapes judicial opinions (court decisions) from federal and state courts across the United States. Each scraper targets a specific court's website to extract opinion metadata and download URLs.

### Scope
- **Applies to:** All scrapers in `juriscraper/opinions/` and subdirectories
- **Does not affect:** PACER scrapers, oral argument scrapers, or other modules
- **Base classes:** `OpinionSite`, `OpinionSiteLinear`, and their WebDriven variants

### Directory Structure
```
juriscraper/opinions/
├── opinion_template.py           # Template for new scrapers
├── united_states/
│   ├── federal_appellate/        # Federal appellate courts
│   ├── federal_district/         # Federal district courts
│   ├── federal_special/          # Specialized federal courts
│   ├── state/                    # State supreme and appellate courts
│   └── territories/              # U.S. territories
└── united_states_backscrapers/   # Historical scraping variants
```

## Choosing the Right Base Class

**⚠️ CRITICAL: All new scrapers MUST use `OpinionSiteLinear` or `OpinionSiteLinearWebDriven`.**

The legacy `OpinionSite` class is maintained only for existing scrapers. Do NOT use it for new development.

### OpinionSiteLinear (Required for All New Scrapers)

This is the **only** acceptable base class for new opinion scrapers. It uses a dictionary-based pattern:

```python
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

class Site(OpinionSiteLinear):
    def _process_html(self):
        """Parse the response and build case dictionaries."""
        for item in self.html.json()["results"]:
            self.cases.append({
                "name": item["title"],
                "date": item["date"],
                "url": item["download_url"],
                "status": "Published",
            })
```

**Why OpinionSiteLinear:**
- Modern, maintainable architecture
- Handles any data source (JSON APIs, HTML, XML)
- Built-in pagination support
- Easier to test and debug
- Consistent with project direction

### OpinionSiteLinearWebDriven (When JavaScript Required)

Use `OpinionSiteLinearWebDriven` only when:
- JavaScript rendering is required to load content
- Dynamic content that cannot be accessed via direct API calls
- Interactive forms that must be submitted
- **Important:** Set `self.uses_selenium = True` in `__init__`

**Note:** Selenium scrapers are slower, more fragile, and harder to maintain. Only use when absolutely necessary (when direct API or HTML requests are impossible).

## Required Scraper Metadata

Every scraper **must** include a complete docstring header:

```python
"""Scraper for [Full Court Name]
CourtID: [unique abbreviation, e.g., 'ariz', 'ca1']
Court Short Name: [citation format, e.g., 'Ariz.', '1st Cir.']
Author: [Your name or 'Claude Code']
Reviewer: [Reviewer name, if applicable]
History:
  YYYY-MM-DD: Created by [Name]
  YYYY-MM-DD: Updated by [Name] - [description of changes]
"""
```

**Important:**
- CourtID should match the module path (e.g., `ariz` for `state/ariz.py`)
- Court Short Name follows citation conventions (Bluebook style)
- Always include creation date in History

## Required Implementation (OpinionSiteLinear)

### The `_process_html()` Method

**This is the only method you need to implement.** It processes the downloaded content and populates `self.cases` with dictionaries.

Each case dictionary must include these **required fields**:
- `name` (str) - Case name
- `date` (str) - Filing date in various string formats or date object
- `url` (str) - Absolute URL to the opinion PDF/HTML
- `status` (str) - Must be "Published", "Unpublished", or "Unknown"

**High-priority optional fields:**
- `docket` (str) - Docket number
- `judge` (str) - Authoring judge (singular, not list)
- `citation` (str) - Official citation
- `summary` (str) - Case summary/synopsis

### Basic Example
```python
def _process_html(self):
    """Extract opinion data from the page."""
    # For HTML responses
    for row in self.html.xpath("//tr[@class='opinion-row']"):
        self.cases.append({
            "name": row.xpath(".//td[@class='name']/text()")[0],
            "date": row.xpath(".//td[@class='date']/text()")[0],
            "url": urljoin(self.base_url, row.xpath(".//a/@href")[0]),
            "status": "Published",
            "docket": row.xpath(".//td[@class='docket']/text()")[0],
        })
```

### Important Guidelines for Case Fields

#### 1. Case Names (`name`)
**Use `titlecase()` ONLY when source data is ALL UPPERCASE:**
```python
from juriscraper.lib.string_utils import titlecase

# Source is uppercase - use titlecase
name = "MCDONALD V. SMITH"
case_dict["name"] = titlecase(name)  # → "McDonald v. Smith" ✓

# Source is properly cased - do NOT use titlecase
name = "McDonald v. Smith"
case_dict["name"] = name  # ✓ Keep as-is

# WRONG - could destroys proper capitalization
case_dict["name"] = titlecase("McDonald v. Smith")  # → "Mcdonald v. Smith" ✗
```

**Critical:** `titlecase()` will break proper names like "McDonald", "O'Brien", "MacArthur" if applied to already-cased text.

#### 2. Dates (`date`)
Use `convert_date_string()` to parse dates:
```python
from juriscraper.lib.string_utils import convert_date_string

# Auto-detect format
case_dict["date"] = convert_date_string("01/15/2024")

# Or pass datetime objects directly
from datetime import datetime
case_dict["date"] = datetime(2024, 1, 15)
```

Common date format examples:
- `"01/15/2024"` → Parsed automatically
- `"January 15, 2024"` → Parsed automatically
- `"2024-01-15"` → Parsed automatically

#### 3. Status (`status`)
**Always normalize to standard values:**
```python
# Map source values to standard statuses
if "Opinion" in raw_status or "Published" in raw_status:
    case_dict["status"] = "Published"
elif "Memorandum" in raw_status or "Unpublished" in raw_status:
    case_dict["status"] = "Unpublished"
else:
    case_dict["status"] = "Unknown"
```

**Only use these three values:**
- `"Published"` - Precedential opinions
- `"Unpublished"` - Non-precedential/memorandum decisions
- `"Unknown"` - Cannot determine status

#### 4. URLs (`url`)
**All URLs must be absolute:**
```python
from urllib.parse import urljoin, quote

# Convert relative to absolute
relative_url = "/opinions/2024/case.pdf"
case_dict["url"] = urljoin(self.base_url, relative_url)

# Encode special characters (preserve URL structure)
url_with_spaces = "/opinions/Case Name.pdf"
case_dict["url"] = urljoin(
    self.base_url,
    quote(url_with_spaces, safe="/:@?=&")
)
```

## Modern Scraper Patterns (OpinionSiteLinear)

### Example: JSON API with Authentication
```python
from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from datetime import date, timedelta
from urllib.parse import urlencode, urljoin

class Site(OpinionSiteLinear):
    base_url = "https://court.gov"
    api_path = "/api/opinions"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.end_date = date.today()
        self.start_date = self.end_date - timedelta(days=7)
        self.url = urljoin(self.base_url, "/search")
        self.make_backscrape_iterable(kwargs)

    def _download(self, request_dict=None):
        """Override to add authentication and call API."""
        # Test mode check
        if self.test_mode_enabled():
            return super()._download(request_dict)

        # Get auth token from main page
        self.html = super()._download()
        token = self.html.xpath("//input[@name='token']/@value")[0]

        # Set auth header
        self.request["headers"]["Authorization"] = f"Bearer {token}"

        # Call API
        params = {
            "start": self.start_date.isoformat(),
            "end": self.end_date.isoformat(),
        }
        self.url = f"{self.base_url}{self.api_path}?{urlencode(params)}"
        return super()._download(request_dict)

    def _process_html(self):
        """Parse JSON response into case dictionaries."""
        data = self.html  # JSON response

        for item in data.get("results", []):
            self.cases.append({
                "name": titlecase(item["title"]),
                "docket": item["docket_number"],
                "date": item["filed_date"],
                "url": urljoin(self.base_url, item["pdf_url"]),
                "status": self._normalize_status(item["type"]),
                "judge": item.get("author"),
            })

    def _normalize_status(self, raw_status: str) -> str:
        """Map API status values to standard values."""
        status_map = {
            "opinion": "Published",
            "memo": "Unpublished",
        }
        return status_map.get(raw_status.lower(), "Unknown")
```

### Pagination Handling
```python
def _process_html(self):
    """Process current page and fetch next if needed."""
    data = self.html

    # Process current page
    for item in data["results"]:
        self.cases.append({...})

    # Handle pagination (only when not in test mode)
    if not self.test_mode_enabled():
        next_page = data.get("next_page")
        if next_page:
            self.url = urljoin(self.base_url, next_page)
            self.html = super()._download()
            self._process_html()  # Recursive call
```

### Backscraping Implementation
```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # ... other initialization ...
    self.make_backscrape_iterable(kwargs)

def _download_backwards(self, dates: tuple[date, date]) -> None:
    """Custom date range request for backscraping.

    :param dates: (start_date, end_date) tuple
    """
    self.start_date, self.end_date = dates
    logger.info(
        "Backscraping for range %s to %s",
        self.start_date,
        self.end_date
    )

    # Reset URL if needed for fresh auth
    self.url = urljoin(self.base_url, "/search")
    self.html = self._download()
    self._process_html()
```

## Common Patterns & Best Practices

### URL Handling
```python
from urllib.parse import urljoin, quote

# Make relative URLs absolute
absolute_url = urljoin(self.base_url, relative_path)

# Encode special characters in URLs (preserve URL structure)
safe_url = urljoin(
    self.base_url,
    quote(file_path, safe="/:@?=&")
)
```

### Text Cleaning
```python
from juriscraper.lib.html_utils import get_visible_text

# Extract text from HTML, removing tags
html_content = "<p>Some <em>text</em></p>"
clean_text = get_visible_text(html_content).strip()

# Normalize whitespace
text = " ".join(text.split())
```

### Date Range Generation
```python
def make_backscrape_iterable(self, kwargs):
    """Generate date range tuples for backscraping."""
    super().make_backscrape_iterable(kwargs)
    if self.backwards:
        # Define your first opinion date and interval
        first_date = datetime(2000, 1, 1)
        interval = 30  # days

        self.back_scrape_iterable = [
            (start, min(start + timedelta(days=interval), date.today()))
            for start in date_range(
                first_date,
                date.today(),
                timedelta(days=interval)
            )
        ]
```

### Logging
```python
from juriscraper.AbstractSite import logger

# Info level for normal operations
logger.info("Processing page %d of %d", current_page, total_pages)

# Error for unexpected conditions
logger.error("Unexpected response format: %s", response)
```

### Type Hints (Modern Scrapers)
```python
from typing import Optional
from datetime import date

def _build_api_url(
    self,
    start_date: Optional[date],
    end_date: Optional[date],
    page: int = 0,
) -> str:
    """Build API URL with parameters.

    :param start_date: Start date for query
    :param end_date: End date for query
    :param page: Page number (0-indexed)
    :return: Complete API URL
    """
    # Implementation
```

## Testing Requirements

### Creating Example Files

1. **Navigate to the court's website** and capture the HTML/JSON response
2. **Save to:** `tests/examples/opinions/united_states/[jurisdiction]/[court_id]_example*.html`
3. **Naming convention:**
   - `ariz_example.html` - Basic example
   - `ariz_example_1.html` - First variation
   - `ariz_example_empty.html` - Edge case: no opinions

### Generating Compare Files

Run the test suite to auto-generate `.compare.json`:
```bash
python3 -m unittest discover -s tests -p "test_ScraperExampleTest.py"  
```

The test will create `ariz_example.compare.json` with extracted metadata.

### Verify Test Output

Check that `.compare.json` contains:
- Correct number of cases
- Properly formatted case names (no all-caps unless intentional)
- Valid dates (YYYY-MM-DD format)
- Absolute URLs (starting with http/https)
- Normalized status values (Published/Unpublished/Unknown)
- No empty required fields

### Running Specific Tests
```bash
# Test all opinion scrapers
python3 -m unittest discover -s tests -p "test_Scraper*.py"

# For full test suite (before submitting PR)
tox -e py313
```

### Testing extract_from_text (If Implemented)

If your scraper implements `extract_from_text()` for PDF metadata extraction, **you MUST add test cases:**

**Where to add tests:**
- File: `tests/local/test_ScraperExtractFromTextTest.py`
- Add entries to the `test_data` dictionary

**The test will fail if:**
- You implement `extract_from_text()` but don't add test data
- Your extraction doesn't match the expected output

**Example:**
```python
"juriscraper.opinions.united_states.state.ariz": [
    ("PDF text here...", {"expected": "output"}),
]
```

See the [Advanced Topics > Testing extract_from_text](#testing-extract_from_text) section for detailed instructions.

## Code Review Checklist

When creating or reviewing opinion scrapers, verify:

### Documentation
- [ ] Complete docstring with CourtID, Court Short Name, Author, Reviewer, History
- [ ] Clear comments for complex logic or non-obvious code
- [ ] Type hints for methods in new scrapers

### Implementation
- [ ] **Uses `OpinionSiteLinear` or `OpinionSiteLinearWebDriven`** (NOT OpinionSite)
- [ ] `_process_html()` method implemented and populates `self.cases`
- [ ] All case dictionaries include required fields: `name`, `date`, `url`, `status`
- [ ] `titlecase()` used **only** when source data is ALL UPPERCASE
- [ ] Dates parsed with `convert_date_string()` or datetime objects
- [ ] Status normalized to exactly: "Published", "Unpublished", or "Unknown"
- [ ] URLs are absolute (using `urljoin()`)
- [ ] Text properly cleaned and whitespace normalized

### Quality
- [ ] No hardcoded credentials, API keys, or sensitive data
- [ ] Proper error handling for network issues
- [ ] Logging used appropriately (info/warning/error levels)
- [ ] `test_mode_enabled()` checked before pagination/multi-page fetches
- [ ] Performance acceptable (no excessive delays or speed warnings)

### Testing
- [ ] Example file(s) added to `tests/examples/opinions/`
- [ ] `.compare.json` generated and committed
- [ ] Test output verified for correctness
- [ ] If `extract_from_text()` implemented: test cases added to `test_ScraperExtractFromTextTest.py`
- [ ] Tests pass locally (`python3 -m unittest` for quick checks, `tox` for full suite)

### Security
- [ ] No command injection vulnerabilities
- [ ] No XPath injection vulnerabilities
- [ ] URLs properly encoded
- [ ] No unvalidated redirects

## Common Pitfalls to Avoid

### 1. Over-using titlecase()
```python
# WRONG: Applying titlecase to properly cased names
case_name = "McDonald v. Smith"
result = titlecase(case_name)  # → "Mcdonald v. Smith" (WRONG!)

# RIGHT: Only use titlecase when source is uppercase
case_name = "MCDONALD V. SMITH"
result = titlecase(case_name)  # → "McDonald v. Smith" (correct)
```

### 2. Forgetting test_mode_enabled()
```python
# WRONG: Pagination runs during tests
def _process_html(self):
    # Process page...
    if self.html.get("next_page"):
        self._fetch_next_page()  # Will break tests!

# RIGHT: Check test mode first
def _process_html(self):
    # Process page...
    if not self.test_mode_enabled() and self.html.get("next_page"):
        self._fetch_next_page()  # Only fetch in production
```

### 3. Relative URLs in Output
```python
# WRONG: Returning relative URLs
def _get_download_urls(self):
    return ["/opinions/2024/case.pdf"]  # Relative URL

# RIGHT: Convert to absolute URLs
from urllib.parse import urljoin

def _get_download_urls(self):
    paths = self.html.xpath("//a/@href")
    return [urljoin(self.base_url, path) for path in paths]
```

### 4. Not Handling Empty Results
```python
# WRONG: Returns None when XPath finds nothing
def _get_judges(self):
    return self.html.xpath("//td[@class='judge']/text()")  # Returns []

# RIGHT: Return None or handle empty list
def _get_judges(self):
    judges = self.html.xpath("//td[@class='judge']/text()")
    return judges if judges else None
```

### 5. Implementing Unused Methods
```python
# WRONG: Method that always returns None
def _get_citations(self):
    """Citations not available on this site."""
    return None  # Don't implement if not available!

# RIGHT: Simply don't implement the method
# (comment in docstring if you want to explain why)
```

### 6. Hardcoding Indices
```python
# WRONG: Fragile code that breaks if page structure changes
case_name = self.html.xpath("//tr")[5].xpath(".//td")[2].text

# RIGHT: Use specific selectors
case_name = self.html.xpath("//td[@class='case-name']/text()")[0]
```

## Advanced Topics

### PDF Content Extraction
Some scrapers need to extract metadata from downloaded PDFs:
```python
def extract_from_text(self, scraped_text: str) -> dict:
    """Extract metadata from opinion text.

    This is called by CourtListener after downloading the PDF.

    :param scraped_text: The extracted text from the PDF
    :return: Dictionary with extracted metadata
    """
    import re

    result = {}

    # Extract lower court info
    pattern = r"Appeal from the (?P<court>[^\\n]+)"
    if match := re.search(pattern, scraped_text):
        result["Docket"] = {"appeal_from_str": match.group("court")}

    return result
```

#### Testing extract_from_text

**CRITICAL: If you implement `extract_from_text`, you MUST add test cases to `tests/local/test_ScraperExtractFromTextTest.py`.**

The test suite will **automatically fail** if you implement `extract_from_text` without adding tests.

**Step 1: Add test data to the test_data dictionary**

Open `tests/local/test_ScraperExtractFromTextTest.py` and add your scraper to the `test_data` dictionary:

```python
test_data = {
    # ... existing entries ...

    "juriscraper.opinions.united_states.state.ariz": [
        (
            # First test case: actual text extracted from a PDF
            """
ARIZONA SUPREME COURT
Opinion No. 2024-001

Appeal from the Superior Court in Maricopa County
The Honorable Jane Smith, Judge
No. CV-2022-001234

JOHN DOE, Petitioner,
v.
STATE OF ARIZONA, Respondent.
            """,
            # Expected extraction result
            {
                "Docket": {
                    "appeal_from_str": "Superior Court in Maricopa County"
                },
                "OriginatingCourtInformation": {
                    "assigned_to_str": "Jane Smith",
                    "docket_number": "CV-2022-001234"
                },
            },
        ),
        (
            # Second test case (optional - add multiple test cases)
            """Another example with different format...""",
            {
                # Expected result for second case
            },
        ),
    ],
}
```

**Step 2: Test structure**

Each scraper entry is a **list of tuples**, where each tuple contains:
1. **Input text** (str) - Actual text from a real PDF
2. **Expected output** (dict) - What `extract_from_text()` should return

**Step 3: Run the tests**

```bash
# Test all extract_from_text implementations
python3 -m unittest tests.local.test_ScraperExtractFromTextTest.ScraperExtractFromText.test_extract_from_text

# Test that all implementations have tests
python3 -m unittest tests.local.test_ScraperExtractFromTextTest.ScraperExtractFromText.test_extract_from_text_properly_implemented
```

**Common extraction patterns:**

| Field | Dictionary Key | Example |
|-------|---------------|---------|
| Lower court name | `Docket["appeal_from_str"]` | "Superior Court of Los Angeles" |
| Lower court judge | `OriginatingCourtInformation["assigned_to_str"]` | "Jane Smith" |
| Lower court docket | `OriginatingCourtInformation["docket_number"]` | "CV-2022-001234" |
| Docket number | `OpinionCluster["docket_number"]` | "S-1-SC-39283" |
| Filing date | `OpinionCluster["date_filed"]` | "2024-01-15" |

**Important notes:**
- Use **actual PDF text** from real opinions, not made-up examples
- Include edge cases (different formatting, missing fields, etc.)
- The test ensures `extract_from_text()` returns a dict even for unparseable text
- Date format must be `YYYY-MM-DD` if extracting dates

### Custom cleanup_content()
Strip court headers/footers from downloaded HTML:
```python
@staticmethod
def cleanup_content(content: str) -> str:
    """Remove headers, footers, and navigation from opinion HTML.

    :param content: Raw HTML content
    :return: Cleaned HTML with only opinion text
    """
    tree = html.fromstring(content)

    # Remove navigation
    for nav in tree.xpath("//div[@class='navigation']"):
        nav.getparent().remove(nav)

    # Extract only opinion content
    opinion = tree.xpath("//div[@class='opinion-content']")[0]
    return html.tostring(opinion, encoding="unicode")
```

### Session Management
For scrapers requiring cookies or session state:
```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.court_id = self.__module__

    # Session persists across requests
    self.request["session"] = requests.Session()

    # Set persistent cookies
    self.request["session"].cookies.set("preference", "value")
```

## Legacy Pattern (For Reference Only)

### OpinionSite (DO NOT USE FOR NEW SCRAPERS)

The `OpinionSite` base class is **deprecated for new development**. It's documented here only to help you understand existing scrapers.

**Why not to use OpinionSite:**
- Harder to maintain and debug
- Cannot handle pagination elegantly
- Requires implementing many individual getter methods
- Less flexible for modern data sources
- Project is moving away from this pattern

**If you need to modify an existing OpinionSite scraper:**
- Follow the existing pattern in that file
- Consider whether it's worth refactoring to OpinionSiteLinear
- Do not create new OpinionSite scrapers

**OpinionSite pattern (for reference):**
```python
from juriscraper.OpinionSite import OpinionSite

class Site(OpinionSite):
    # Must implement these separate methods:
    def _get_download_urls(self):
        return list(self.html.xpath("//a/@href"))

    def _get_case_names(self):
        return list(self.html.xpath("//td[@class='name']/text()"))

    def _get_case_dates(self):
        return [
            convert_date_string(d)
            for d in self.html.xpath("//td[@class='date']/text()")
        ]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self._get_download_urls())
```

**If you see this pattern in a PR, request that it be rewritten using OpinionSiteLinear.**

## References

- **Template:** [`opinion_template.py`](opinion_template.py) - Start here for new scrapers
- **Base Classes:**
  - [`OpinionSiteLinear.py`](../OpinionSiteLinear.py) - ✅ Use this for new scrapers
  - [`OpinionSite.py`](../OpinionSite.py) - ⚠️ Legacy only, do not use
- **Example Modern Scraper:** [`united_states/state/ariz.py`](united_states/state/ariz.py)
- **Contributing Guide:** [`CONTRIBUTING.md`](../../CONTRIBUTING.md)
- **Testing:** `python3 -m unittest discover -s tests -p "test_ScraperExampleTest.py"` (see CONTRIBUTING.md for tox)


---

**Last Updated:** 2026-02-17
**Scope:** `juriscraper/opinions/` module only
**Base Class:** OpinionSiteLinear (required for all new scrapers)
