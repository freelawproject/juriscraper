import pathlib
import sys
import time
import unittest

import jsondate3 as json
import pydantic_core
from pydantic import BaseModel

from juriscraper.lib.test_utils import warn_or_crash_slow_parser


class PacerParseTestCase(unittest.TestCase):
    """A mixin to add a parsing test."""

    def parse_files(self, path_root, file_ext, test_class):
        """Can we do a simple query and parse?"""
        paths = sorted(pathlib.Path(path_root).rglob(file_ext))
        path_max_len = max(len(str(path)) for path in paths) + 2
        for i, path in enumerate(paths):
            t1 = time.time()
            sys.stdout.write(f"{i}. Doing {str(path).ljust(path_max_len)}")
            filename = path.name
            filename_sans_ext = filename.split(".")[0]
            json_path = path.parent / f"{filename_sans_ext}.json"

            court = filename_sans_ext.split("_")[0]
            report = test_class(court)

            # Try to read the file using utf-8.
            # If it fails fallback on iso-8859-1
            try:
                with path.open("rb") as f:
                    report._parse_text(f.read().decode("utf-8"))
            except UnicodeDecodeError:
                with path.open("rb") as f:
                    report._parse_text(f.read().decode("iso-8859-1"))

            # Does the metadata function work too? It usually, but not always,
            # gets called by report.data
            try:
                _ = report.metadata
            except AttributeError:
                # Some reports don't have this method.
                pass
            data = report.data
            if isinstance(data, BaseModel) or (
                isinstance(data, list)
                and data
                and isinstance(data[0], BaseModel)
            ):
                data = pydantic_core.to_jsonable_python(data)
            if not json_path.exists():
                with json_path.open("w") as f:
                    print(f"Creating new file at {json_path}")
                    json.dump(data, f, indent=2, sort_keys=True)
                continue
            data = json.loads(json.dumps(data, sort_keys=True))
            with json_path.open() as f:
                j = json.load(f)
                with self.subTest(
                    "Parsing PACER", file=filename, klass=test_class
                ):
                    self.assertEqual(j, data)
            t2 = time.time()
            duration = t2 - t1
            warn_or_crash_slow_parser(duration, max_duration=2)

            sys.stdout.write("✓\n")
