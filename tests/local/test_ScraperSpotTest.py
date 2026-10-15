#!/usr/bin/env python
import asyncio
import re
import unittest
from datetime import date

from juriscraper.AbstractSite import logger
from juriscraper.opinions.united_states.state import (
    fladistctapp_1,
    nev,
    nevapp,
)


class ScraperSpotTest(unittest.TestCase):
    """Adds specific tests to specific courts that are more-easily tested
    without a full integration test.
    """

    def test_mass(self):
        strings = {
            "Massachusetts State Automobile Dealers Association, Inc. v. Tesla Motors MA, Inc. (SJC 11545) (September 15, 2014)": [
                "Massachusetts State Automobile Dealers Association, Inc. v. Tesla Motors MA, Inc.",
                "SJC 11545",
            ],
            "Bower v. Bournay-Bower (SJC 11478) (September 15, 2014)": [
                "Bower v. Bournay-Bower",
                "SJC 11478",
            ],
            "Commonwealth v. Holmes (SJC 11557) (September 12, 2014)": [
                "Commonwealth v. Holmes",
                "SJC 11557",
            ],
            "Superintendent-Director of Assabet Valley Regional School District v. Speicher (SJC 11563) (September 11, 2014)": [
                "Superintendent-Director of Assabet Valley Regional School District v. Speicher",
                "SJC 11563",
            ],
            "Commonwealth v. Quinn (SJC 11554) (September 11, 2014)": [
                "Commonwealth v. Quinn",
                "SJC 11554",
            ],
            "Commonwealth v. Wall (SJC 09850) (September 11, 2014)": [
                "Commonwealth v. Wall",
                "SJC 09850",
            ],
            "Commonwealth v. Letkowski (SJC 11556) (September 9, 2014)": [
                "Commonwealth v. Letkowski",
                "SJC 11556",
            ],
            "Commonwealth v. Sullivan (SJC 11568) (September 9, 2014)": [
                "Commonwealth v. Sullivan",
                "SJC 11568",
            ],
            "Plumb v. Casey (SJC 11519) (September 8, 2014)": [
                "Plumb v. Casey",
                "SJC 11519",
            ],
            "A.J. Properties, LLC v. Stanley Black and Decker, Inc. (SJC 11424) (September 5, 2014)": [
                "A.J. Properties, LLC v. Stanley Black and Decker, Inc.",
                "SJC 11424",
            ],
            "Massachusetts Electric Co. v. Department of Public Utilities (SJC 11526, 11527, 11528) (September 4, 2014)": [
                "Massachusetts Electric Co. v. Department of Public Utilities",
                "SJC 11526, 11527, 11528",
            ],
            "Commonwealth v. Doe (SJC-11861) (October 22, 2015)": [
                "Commonwealth v. Doe",
                "SJC-11861",
            ],
            "Commonwealth v. Teixeira; Commonwealth v. Meade (SJC 11929; SJC 11944) (September 16, 2016)": [
                "Commonwealth v. Teixeira; Commonwealth v. Meade",
                "SJC 11929; SJC 11944",
            ],
        }
        for s in strings.items():
            m = re.search(r"(.*?) \((.*?)\)( \((.*?)\))?", s[0])
            name, docket, _, date = m.groups()
            self.assertEqual([name, docket], s[1])

    def test_massappct(self):
        strings = {
            "Commonwealth v. Forbes (AC 13-P-730) (August 26, 2014)": [
                "Commonwealth v. Forbes",
                "AC 13-P-730",
            ],
            "Commonwealth v. Malick (AC 09-P-1292, 11-P-0973) (August 25, 2014)": [
                "Commonwealth v. Malick",
                "AC 09-P-1292, 11-P-0973",
            ],
            "Litchfield's Case (AC 13-P-1044) (August 28, 2014)": [
                "Litchfield's Case",
                "AC 13-P-1044",
            ],
            "Rose v. Highway Equipment Company (AC 13-P-1215) (August 27, 2014)": [
                "Rose v. Highway Equipment Company",
                "AC 13-P-1215",
            ],
            "Commonwealth v. Alves (AC 13-P-1183) (August 27, 2014)": [
                "Commonwealth v. Alves",
                "AC 13-P-1183",
            ],
            "Commonwealth v. Dale (AC 12-P-1909) (August 25, 2014)": [
                "Commonwealth v. Dale",
                "AC 12-P-1909",
            ],
            "Kewley v. Department of Elementary and Secondary Education (AC 13-P-0833) (August 22, 2014)": [
                "Kewley v. Department of Elementary and Secondary Education",
                "AC 13-P-0833",
            ],
            "Hazel's Cup & Saucer, LLC v. Around The Globe Travel, Inc. (AC 13-P-1371) (August 22, 2014)": [
                "Hazel's Cup & Saucer, LLC v. Around The Globe Travel, Inc.",
                "AC 13-P-1371",
            ],
            "Becker v. Phelps (AC 13-P-0951) (August 22, 2014)": [
                "Becker v. Phelps",
                "AC 13-P-0951",
            ],
            "Barrow v. Dartmouth House Nursing Home, Inc. (AC 13-P-1375) (August 18, 2014)": [
                "Barrow v. Dartmouth House Nursing Home, Inc.",
                "AC 13-P-1375",
            ],
            "Zimmerling v. Affinity Financial Corp. (AC 13-P-1439) (August 18, 2014)": [
                "Zimmerling v. Affinity Financial Corp.",
                "AC 13-P-1439",
            ],
            "Lowell v. Talcott (AC 13-P-1053) (August 18, 2014)": [
                "Lowell v. Talcott",
                "AC 13-P-1053",
            ],
            "Copley Place Associates, LLC v. Tellez-Bortoni (AC 16-P-165) (January 01, 2017)": [
                "Copley Place Associates, LLC v. Tellez-Bortoni",
                "AC 16-P-165",
            ],
        }
        for s in strings.items():
            m = re.search(r"(.*?) \((.*?)\)( \((.*?)\))?", s[0])
            name, docket, _, date = m.groups()
            self.assertEqual([name, docket], s[1])

    def test_nytrial_build_url(self):
        from juriscraper.opinions.united_states.state import (
            nysupct,
            nysupct_commercial,
        )

        root = "https://nycourts.gov/reporter"
        expected = [
            (nysupct, date(2026, 4, 10), "slipidx/miscolo_2026_april"),
            (nysupct, date(2026, 5, 10), "current/index/miscolo_2026_may"),
            (
                nysupct_commercial,
                date(2026, 3, 10),
                "slipidx/com_div_idxtable_2026_march",
            ),
            (
                nysupct_commercial,
                date(2026, 4, 10),
                "current/index/com_div_idxtable_2026_april",
            ),
            (nysupct, date.today(), "current/index/miscolo"),
            (nysupct, None, "current/index/miscolo"),
        ]
        for module, target_date, path in expected:
            site = module.Site()
            self.assertEqual(
                site.build_url(target_date), f"{root}/{path}.shtml"
            )

    def test_nytrial_page_not_found(self):
        from lxml.html import fromstring

        from juriscraper.lib.exceptions import ParsingException
        from juriscraper.opinions.united_states.state import nysupct

        site = nysupct.Site()
        # minimal copy of the page served, with a 200 status code, for
        # https://nycourts.gov/reporter/slipidx/miscolo_2026_may.shtml
        site.html = fromstring(
            b'<?xml version="1.0" encoding="utf-8"?>\n'
            b'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML Basic 1.1//EN" '
            b'"http://www.w3.org/TR/xhtml-basic/xhtml-basic11.dtd">\n'
            b'<html xmlns="http://www.w3.org/1999/xhtml"><head>'
            b"<title>404 ERROR - N.Y. State Courts</title></head><body><main>"
            b"<h2>404 ERROR - File Not Found</h2>"
            b"<h1>Sorry, but the page you requested cannot be found.</h1>"
            b"</main></body></html>"
        )
        with self.assertRaises(ParsingException):
            asyncio.run(site._process_html())

    def test_nytrial_metadata_from_stub(self):
        from lxml.html import fromstring

        from juriscraper.opinions.united_states.state import nytrial

        # minimal copies of the stub page headers of
        # https://www.nycourts.gov/reporter/current/3dseries/2026/2026_32223.shtml
        # https://www.nycourts.gov/reporter/current/3dseries/2023/2023_35460.shtml
        # https://www.nycourts.gov/reporter/current/3dseries/2026/2026_32204.shtml
        stub = (
            '<main id="main"><div class="current-legal-document">'
            '<div class="case-info"><h1>{name}</h1>'
            "<p>{slip}</p><p>{date}</p><p>{court}</p>"
            "<p>{docket}</p><p>{judge}</p>"
            "<p>Published by New York State Law Reporting Bureau pursuant "
            "to Judiciary Law &sect; 431.</p></div>"
            '<h2 class="center"><a href="https://www.nycourts.gov/reporter/'
            'pdfs/2026/2026_32223.pdf">Full Decision: {slip} (PDF)</a></h2>'
            "</div></main>"
        )
        expected = [
            (
                {
                    "name": "Harbour v Acme Mkts. Inc.",
                    "slip": "2026 NY Slip Op 32223(U)",
                    "date": "September 9, 2026",
                    "court": "Supreme Court, Westchester County",
                    "docket": "Index No. 56892/2026",
                    "judge": "Charles D. Wood, J.",
                },
                ("Charles D. Wood", "Index No. 56892/2026"),
            ),
            (
                {
                    "name": "Telfair v State of New York",
                    "slip": "2023 NY Slip Op 35460(U)",
                    "date": "August 24, 2023",
                    "court": "Court of Claims",
                    "docket": "Claim No. 136668",
                    "judge": "Catherine E. Leahy-Scott, J.",
                },
                ("Catherine E. Leahy-Scott", "Claim No. 136668"),
            ),
            (
                {
                    "name": "Matter of Dinshaw",
                    "slip": "2026 NY Slip Op 32204(U)",
                    "date": "August 31, 2026",
                    "court": "Surrogate's Court, New York County",
                    "docket": "Index No. 1970-1950/B",
                    "judge": "Rita Mella, J.",
                },
                ("Rita Mella", "Index No. 1970-1950/B"),
            ),
        ]
        for values, (judge, docket) in expected:
            header = fromstring(stub.format(**values)).xpath(
                "//h1/parent::div"
            )
            self.assertEqual(nytrial.Site.get_judge_from_header(header), judge)
            self.assertEqual(
                nytrial.Site.get_docket_from_header(header), docket
            )

    def test_nev_judge_initials(self):
        """Panel initials resolve by court and filed date"""
        supreme, appeals = nev.Site(), nevapp.Site()

        self.assertEqual(
            supreme.resolve_initials("MG", "2018-05-01"), "Mark Gibbons"
        )
        self.assertEqual(
            appeals.resolve_initials("MG", "2018-05-01"), "Michael P. Gibbons"
        )

        with self.assertLogs(logger, level="ERROR"):
            self.assertEqual(supreme.resolve_initials("MG", "2022-05-01"), "")
        with self.assertLogs(logger, level="ERROR"):
            metadata = supreme.parse_description(
                "Majority: Stiglich/ZZ/Lee.", "2026-06-18"
            )
        self.assertEqual(metadata["judge"], "Stiglich, Lee")

    def test_nev_majority_panel(self):
        """Panel parsing tolerates a "Before:" prefix and spaced slashes"""
        site = nev.Site()
        tests = [
            (
                "Majority: Before: Parraguirre/Bell/Stiglich. 141 Nev.",
                "Parraguirre, Bell, Stiglich",
            ),
            (
                "Majority:  Parraguirre/Hardesty/ Cadish.  136 Nev.",
                "Parraguirre, Hardesty, Cadish",
            ),
            (
                "Majority: Hardesty/Parraguirre /Douglas. 124 Nev.",
                "Hardesty, Parraguirre, Douglas",
            ),
            (
                "Majority: Pickering/Gibbons/ /Hardesty. 129 Nev.",
                "Pickering, Gibbons, Hardesty",
            ),
            (
                "Majority: Herndon/Lee/Parraguirre 139 Nev. SNP23-DH/PL/RP.",
                "Herndon, Lee, Parraguirre",
            ),
            ("Majority: En Banc. 141 Nev.", ""),
        ]
        for description, judges in tests:
            with self.subTest(description=description):
                metadata = site.parse_description(description, "2026-06-18")
                self.assertEqual(metadata["judge"], judges)

    def test_nev_backscrape_past_last_page(self):
        """A backscrape stops on the empty page after the last one"""
        result = {
            "docketEntryHeader": {
                "filedDate": "2000-05-08T07:00:00.000+00:00",
                "docketEntryDescription": "Majority: Rose/Young/Maupin.",
            },
            "caseHeader": {
                "caseNumber": "33018",
                "caseTitle": "STATE VS. DOE",
                "caseInstanceUUID": "case-uuid",
            },
            "documentLinkUUID": "document-uuid",
        }
        pages = [
            {"_embedded": {"results": [result]}},
            # The API leaves out "_embedded" past the last page
            {"page": {"size": 100, "totalElements": 1, "number": 1}},
        ]

        async def download():
            return pages.pop(0)

        site = nev.Site(backscrape_start="2000/01/01")
        site._download = download
        asyncio.run(site._download_backwards(site.back_scrape_iterable[0]))
        self.assertEqual(len(site.cases), 1)
        self.assertEqual(pages, [])

    def test_fladistctapp_1_get_citation(self):
        """Citations are taken from the 1st DCA `note` field"""
        site = fladistctapp_1.Site()
        tests = [
            # Disposition, then a citation on its own line
            ("Affirmed\r\n433 So. 3d 1007", "433 So. 3d 1007"),
            ("Dismissed\r\n428 So. 3d 1285", "428 So. 3d 1285"),
            ("Denied\r\n433 So. 3d 472", "433 So. 3d 472"),
            ("Reversed\r\n433 So. 3d 454", "433 So. 3d 454"),
            (
                "Affirmed in Part/Reversed in Part\r\n433 So. 3d 458",
                "433 So. 3d 458",
            ),
            (
                "Affirmed - Corrected 9/20/24\r\n393 So. 3d 289",
                "393 So. 3d 289",
            ),
            # No citation yet
            ("Affirmed", ""),
            ("Affirmed - Per Curiam Affirmed", ""),
            ("Affirmed in Part/Reversed in Part", ""),
            ("", ""),
            ("Affirmed;  WITHDRAWN 05-13-2026", ""),
            ("Reversed - Corrected 9/16/2025", ""),
            ("Affirmed\r\nWithdrawn 11-06-24", ""),
            # Malformed citations are returned as written
            ("Affirmed\r\n432 So. 3d  1204", "432 So. 3d  1204"),
            ("Affirmed\r\n376 so. 3d 709", "376 so. 3d 709"),
            ("Affirmed\r\n400 S. 3d 797", "400 S. 3d 797"),
            ("Reversed\r\n432 So. 3d1080", "432 So. 3d1080"),
            ("Affirmed\r\n381 So . 3d 648", "381 So . 3d 648"),
            ("Affirmed\r\n373 So 3d 851", "373 So 3d 851"),
            # Citation before the disposition
            ("379 So. 3d 494\r\nAffirmed", "379 So. 3d 494"),
            # A later edition of the reporter (not in the source yet)
            ("Affirmed\r\n12 So. 4d 345", "12 So. 4d 345"),
            # Citations to other cases, quoted in the court's text
            (
                "Transf to Leon Co to Cons as Extraord Writ ~ See Bush v. "
                "State, 945 So. 2d 1207, 1213-14 (Fla. 2006).",
                "",
            ),
            (
                "Accordingly, we direct the Clerk to forward a certified copy "
                "of this opinion to the Florida Department of Corrections. "
                "See Ibarra v. State, 45 So. 3d 911, 914 (Fla. 4th DCA 2010).",
                "",
            ),
        ]
        for note, citation in tests:
            with self.subTest(note=note):
                self.assertEqual(site.get_citation(note), citation)
