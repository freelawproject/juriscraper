# Contributing to Juriscraper

Thank you for your interest in contributing!

This document contains everything developers need to contribute code, create scrapers, run tests, and understand our code style and deployment process.

## Code Style & Linting

We use [Ruff](https://docs.astral.sh/ruff/) for code formatting and linting. Ruff replaces tools like flake8, isort, black, and autoflake with a single fast tool.

### Pre-commit Hooks

Ruff is run automatically via [pre-commit hooks](https://pre-commit.com), which you can set up like this:


```bash
uv tool install pre-commit --with pre-commit-uv
pre-commit install
```

To run Ruff manually on all files:

```bash
pre-commit run ruff-format --all-files
pre-commit run ruff --all-files
```

To run only on staged files:
```bash
pre-commit run ruff-format
pre-commit run ruff
```

You can also [integrate Ruff into your editor](https://docs.astral.sh/ruff/editors/setup/) for automatic formatting and diagnostics.

### Formatting Guidelines

Beyond what Ruff catches:

- If you manually make whitespace or formatting changes, **do them in a separate commit** from logic changes.
- Avoid combining formatting and logic in the same commit to keep code review clean.

---

## Joining the Project as a Developer

When contributing new scrapers or other changes:

- Automated tests must pass. The test suite will be run automatically by Github Actions.
- If modifying PACER-related code, PACER tests must also pass. These are skipped by default unless `PACER_USERNAME` and `PACER_PASSWORD` are set.
- Add a `*_example*` file to `tests/examples` to enable test coverage of your scraper.
- Follow [PEP 8](https://peps.python.org/pep-0008/) and ensure no major Ruff or IDE inspection issues.
- Scraper performance must be reasonable with no speed warnings or unhandled exceptions during test runs on a modern machine.

### Want to contribute a scraper?

Reach out to us so we can find a scraper that you can work on and that nobody else is currently working on. You can also browse our [wiki list of court websites](https://github.com/freelawproject/juriscraper/wiki/Court-Websites).

Templates for scrapers:

- [Opinion scraper template](https://github.com/freelawproject/juriscraper/blob/master/juriscraper/opinions/opinion_template.py)
- [Oral argument scraper template](https://github.com/freelawproject/juriscraper/blob/master/juriscraper/oral_args/oral_argument_template.py)

### Contributing Workflow

1. Fork this repository.
2. Update `__init__.py` to register new scrapers.
3. Include your example files and generated `.compare.json` in your commit.
4. Update CHANGES.md file
5. Push your changes to your fork.
6. Submit a pull request.
### Contributor License Agreement (CLA)

Before we can accept your contribution, you must sign the Contributor License Agreement found at the root of this repository. It protects both your rights and those of the Free Law Project.

---

## Development Setup

### Requirements

- Python 3.9+
- [`uv`](https://github.com/astral-sh/uv): modern Python package manager
- Git
- (Optional) Docker for running Selenium tests

### Installing `uv`

#### Ubuntu/Debian:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Arch:

```bash
sudo pacman -S uv
```

#### macOS:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Clone & Setup Environment
Create a development environment using uv and the included pyproject.toml and uv.lock files:

```bash
git clone https://github.com/freelawproject/juriscraper.git
cd juriscraper
uv venv
source .venv/bin/activate
```

---

## Running Tests

We use [`tox`](https://tox.readthedocs.io) to manage test environments.

Install `tox` with [`uv`](https://docs.astral.sh/uv/) as a [`tool`](https://docs.astral.sh/uv/concepts/tools/), adding the [`tox-uv` extension](https://github.com/tox-dev/tox-uv):

```bash
uv tool install tox --with tox-uv
```

Run tests for all Python versions:

```bash
tox
```

Run tests for a single Python version, such as for Python 3.13:

```bash
tox -e py313
```

Add extra args to `pytest`, add them after a ``--`` separator,:

```bash
tox -e py313 -- --pdb
```

### Running Network (PACER) Tests

The tests in ``tests/network`` interact with PACER.
By default, they are skipped, as they require working credentials.
To run them, set the environment variables ``PACER_USERNAME`` and ``PACER_PASSWORD`` to your PACER credentials, for example:

```bash
export PACER_USERNAME=your_username
export PACER_PASSWORD=your_password
tox -e py313
```

To run only the PACER tests:

```bash
tox -e py313 -- tests/network
```

### Example Runner
The `sample_caller.py` script demonstrates how to use Juriscraper.

You can see the required options by running:
```bash
uv run sample_caller.py
```

For example, to test `ca1`, run:

```bash
uv run sample_caller.py -c juriscraper.opinions.united_states.state.kan_p
```

---

## Usage

The scrapers are written in Python, and can scrape a court as follows:

```python
from juriscraper.opinions.united_states.federal_appellate import ca1

# Create a site object
site = ca1.Site()

# Populate it with data, downloading the page if necessary
site.parse()

# Print out the object
print(str(site))

# Print it out as JSON
print(site.to_json())

# Iterate over the items
for opinion in site:
    print(opinion)
```

That will print out all the current meta data for a site, including
links to the objects you wish to download (typically opinions or oral
arguments). If you download those opinions, we also recommend running the
`cleanup_content()` method against the items that you download (PDFs,
HTML, etc.). See the `sample_caller.py` for an example and see
`cleanup_content()` for an explanation of what it does.
Note that if cleanup_content() is not implemented in the scraper,
it will simply return the original content unchanged.

It's also possible to iterate over all courts in a Python package, even if they're not known before starting the scraper. For example:

```python
# Start with an import path. This will do all federal courts.
court_id = 'juriscraper.opinions.united_states.federal'

# Import all the scrapers
scrapers = __import__(
    court_id,
    globals(),
    locals(),
    ['*']
).__all__

for scraper in scrapers:
    mod = __import__(
        f'{court_id}.{scraper}',
        globals(),
        locals(),
        [scraper]
    )
    # Create a Site instance, then get the contents
    site = mod.Site()
    site.parse()
    print(str(site))
```

This can be useful if you wish to create a command line scraper that
iterates over all courts of a certain jurisdiction that is provided by a
script. See ``lib/importer.py`` for an example that's used in
the sample caller.

### District Court Parser

A sample driver to run the PACER District Court parser on an html file is included.
It takes HTML file(s) as arguments and outputs JSON to stdout.

Example usage:

```bash
   PYTHONPATH=`pwd` python juriscraper/pacerdocket.py tests/examples/pacer/dockets/district/nysd.html
```

## Tests

Each scraper should have:

- A `*_example*` file in `tests/examples` (HTML/XML/etc.). When creating a new scraper,
or covering a new use case for an existing scraper, you will have to create an
example file yourself.  Please see the files under `tests/examples/` to see
for yourself how the naming structure works.  What you want to put in your new
example file is the HTML/json/xml that the scraper in question needs to test
parsing.  Sometimes creating these files can be tricky, but more often than not,
it is as simple as getting the data to display in your browser, viewing then copying
the page source, then pasting that text into your new example file.
- A matching `*_example*.compare.json` file, generated automatically when tests run. This
file contains a json data object that represents the data extracted when parsing
the corresponding `*_example*` file.  These are used to ensure that each scraper
parses the exact data we expect from each of its `*_example*` files.

**How to create test files:**

1. Save page source from your browser.
2. Create a `*_example*` file with the raw content.
3. Run the test suite once, it will generate the `.compare.json`.
4. Review that data in `.compare.json` is correct.
5. Re-run tests. If all pass, include both files in your PR.

Individual tests can be run with:

```bash
tox -e py -- tests/local/test_DateTest.py::DateTest::test_date_range_creation
```

To run and drop to the Python debugger if it fails, but you must install `nost` to have `nosetests`:

```bash
uv run nosetests -v --pdb tests/local/test_DateTest.py:DateTest.test_date_range_creation
```

---

## Future Goals
-  Support for additional PACER pages and utilities
-  Support opinions from for all courts of U.S. territories (Guam, American Samoa, etc.)
-  Support opinions from for all federal district courts with non-PACER opinion listings
-  For every court above where a backscraper is possible, it is implemented.
-  Support video, additional oral argument audio, and transcripts everywhere available

---

## Deployment

Deployment to PyPI is automatic when a tagged release (e.g., `v2.6.80`) is pushed to `main`.

Steps:

1. Update the version in `pyproject.toml`.
2. Tag your commit with the correct tag: `v*.*.*`
3. Push the tag and open a PR if needed.

---

Thanks for contributing to Juriscraper!