"""Test harness for KentParser implementations.

Coverage is discovering by convention. Every
concrete ``KentParser`` subclass is found via ``__subclasses__`` (after
importing every ``parsers.py`` under ``juriscraper/`` or python file
in a ``parsers/`` directory) and matched to a fixture directory by
convention:

* Mirror the scraper package tree under ``tests/examples/``. Parsers
  defined in ``juriscraper/<x>/parsers.py`` get their fixtures under
  ``tests/examples/<x>/``.
* Within that directory, give each parser a subdirectory named *exactly*
  after its class — ``tests/examples/<x>/DocketDetailParser/`` holds the
  fixtures for ``DocketDetailParser``.
* Drop a ``<fixture>.html`` in that subdirectory. The harness runs the
  parser's ``from_file`` against it, serializes each returned
  ``DeferredValidation``'s ``raw_data`` to a list of plain dicts, and
  compares against a paired ``<fixture>.compare.json``.

The matching is enforced both ways, so neither side can silently drop
coverage: a parser with no fixture directory fails, and an example
subdirectory that doesn't name a real parser fails.

If the ``.compare.json`` file is missing, the harness writes one from
the current parser output so a new fixture can be staged with a single
test run, then committed once eyeballed. A generated baseline is *not*
a verification — ``warn_generated_compare_file`` fires so the run makes
it loud that the output was blessed, not checked.
"""

from __future__ import annotations

import fnmatch
import importlib
import inspect
import os
import sys
import time
import unittest
from pathlib import Path
from typing import TYPE_CHECKING

import jsondate3 as json
import pydantic_core

from juriscraper.lib.test_utils import (
    warn_generated_compare_file,
    warn_or_crash_slow_parser,
)
from tests import TESTS_ROOT_EXAMPLES

if TYPE_CHECKING:
    from kent.common.parser import KentParser


class KentParserTestCase(unittest.TestCase):
    """A mixin to add KentParser fixture testing."""

    def assert_kent_parsers_have_examples(self) -> None:
        """Run every discovered ``KentParser`` against its fixtures.

        Imports every ``parsers.py`` under ``juriscraper/`` so that all
        concrete ``KentParser`` subclasses are registered, then enforces
        the fixture convention in both directions:

        * Forward — each parser must have an example directory holding at
          least one ``*.html`` fixture, else the test fails (a brand-new
          parser can't ship untested).
        * Reverse — each example subdirectory under a scraper's examples
          root must name a discovered parser, else the test fails (a
          renamed/deleted parser can't leave a stale fixture dir behind).
        """
        from kent.common.parser import KentParser

        self._import_parser_modules()
        parsers = sorted(
            (
                cls
                for cls in self._all_subclasses(KentParser)
                if not inspect.isabstract(cls)
            ),
            key=lambda c: (c.__module__, c.__name__),
        )
        self.assertTrue(
            parsers, "Discovered no concrete KentParser subclasses to test"
        )

        # scraper examples root -> parser class names expected under it
        expected_by_root: dict[Path, set[str]] = {}
        for cls in parsers:
            examples_dir = self._example_dir_for(cls)
            expected_by_root.setdefault(examples_dir.parent, set()).add(
                cls.__name__
            )
            with self.subTest(parser=f"{cls.__module__}.{cls.__name__}"):
                self.assertTrue(
                    examples_dir.is_dir()
                    and any(examples_dir.rglob("*.html")),
                    f"{cls.__name__} has no fixtures — add at least one "
                    f"<fixture>.html under {examples_dir}",
                )
                self.parse_examples(examples_dir, cls)

        # Reverse check: no orphan example dirs under any scraper root.
        for root, expected in sorted(expected_by_root.items()):
            if not root.is_dir():
                continue
            actual = {p.name for p in root.iterdir() if p.is_dir()}
            with self.subTest(
                scraper=str(root.relative_to(TESTS_ROOT_EXAMPLES))
            ):
                self.assertEqual(
                    set(),
                    actual - expected,
                    f"Example dirs under {root} name no KentParser: "
                    f"{sorted(actual - expected)}",
                )

    @staticmethod
    def _import_parser_modules() -> None:
        """Import every scraper's parser modules so subclasses register.

        Parsers live either in a ``parsers.py`` module or, once a scraper
        outgrows that, in a ``parsers/`` package of per-step modules
        (``parsers/docket_detail.py`` etc.). Import both shapes.
        """
        import juriscraper

        package_root = Path(juriscraper.__file__).resolve().parent
        modules = set(package_root.rglob("parsers.py"))
        modules |= set(package_root.rglob("parsers/*.py"))
        for path in sorted(modules):
            rel = path.relative_to(package_root.parent).with_suffix("")
            dotted = ".".join(rel.parts)
            if dotted.endswith(".__init__"):
                dotted = dotted[: -len(".__init__")]
            importlib.import_module(dotted)

    @classmethod
    def _all_subclasses(cls, klass: type) -> set[type]:
        """All transitive subclasses of ``klass``."""
        found: set[type] = set()
        for sub in klass.__subclasses__():
            found.add(sub)
            found |= cls._all_subclasses(sub)
        return found

    @staticmethod
    def _example_dir_for(parser_class: type) -> Path:
        """Fixture directory for a parser: its scraper tree + class name.

        The scraper root is the package that holds the parsers, whether
        they sit in ``<scraper>/parsers.py`` or ``<scraper>/parsers/*.py``
        — i.e. everything in the module path up to (but not including) the
        ``parsers`` component. Fixtures live one directory below that, in
        ``<scraper>/<ParserClass>/``, regardless of which file defines it.
        """
        parts = parser_class.__module__.split(".")
        # parts[0] == "juriscraper"; drop it and everything from "parsers".
        scraper_parts = parts[1 : parts.index("parsers")]
        return TESTS_ROOT_EXAMPLES.joinpath(*scraper_parts) / (
            parser_class.__name__
        )

    def parse_examples(
        self,
        path_root: Path,
        parser_class: type[KentParser],
    ) -> None:
        """Run ``parser_class`` over every ``*.html`` fixture under
        ``path_root`` and compare against paired ``*.compare.json``.

        If no fixtures exist at ``path_root`` the test is skipped — this
        lets new parser directories live in source control before any
        fixtures have been captured.
        """
        if not path_root.exists():
            self.skipTest(f"No fixture directory: {path_root}")

        html_paths: list[str] = []
        compare_paths: list[str] = []
        for root, _, filenames in os.walk(path_root):
            for filename in fnmatch.filter(filenames, "*.html"):
                html_paths.append(os.path.join(root, filename))
            for filename in fnmatch.filter(filenames, "*.compare.json"):
                compare_paths.append(os.path.join(root, filename))

        if not html_paths:
            self.skipTest(f"No *.html fixtures under {path_root}")

        # Every expected file must be backed by a fixture that produces
        # it. An orphan ``.compare.json`` (its ``.html`` was renamed or
        # deleted) is dead weight that is never re-verified — fail loudly
        # rather than let a stale expectation pass by being ignored.
        expected_compare = {
            html_path[: -len(".html")] + ".compare.json"
            for html_path in html_paths
        }
        orphans = sorted(set(compare_paths) - expected_compare)
        self.assertEqual(
            [],
            [os.path.relpath(p, path_root) for p in orphans],
            "Orphan .compare.json files have no matching .html fixture",
        )

        html_paths.sort()
        path_max_len = max(len(p) for p in html_paths) + 2
        for i, html_path in enumerate(html_paths):
            sys.stdout.write(f"{i}. Comparing {html_path.ljust(path_max_len)}")
            with self.subTest(fixture=os.path.relpath(html_path, path_root)):
                self._run_one(html_path, parser_class)
            sys.stdout.write("✓\n")

    def _run_one(
        self,
        html_path: str,
        parser_class: type[KentParser],
    ) -> None:
        compare_path = html_path[: -len(".html")] + ".compare.json"

        t1 = time.time()
        results = parser_class.from_file(html_path)
        actual = [
            pydantic_core.to_jsonable_python(dv.raw_data) for dv in results
        ]
        actual = json.loads(json.dumps(actual, sort_keys=True))
        warn_or_crash_slow_parser(time.time() - t1, max_duration=2)

        if not os.path.exists(compare_path):
            with open(compare_path, "w") as f:
                print(f"Creating new fixture at {compare_path}")
                json.dump(actual, f, indent=2, sort_keys=True)
            # A freshly written baseline was blessed, not verified.
            warn_generated_compare_file(compare_path)
            return

        with open(compare_path) as f:
            expected = json.load(f)
        self.assertEqual(expected, actual)
