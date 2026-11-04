#!/usr/bin/env python
import asyncio
import re
import unittest
from datetime import date

from lxml import html

from juriscraper.AbstractSite import logger
from juriscraper.opinions.united_states.administrative_agency import cbca
from juriscraper.opinions.united_states.state import nev, nevapp


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

    def test_cbca_messy_rows(self):
        """Rows missing <tr>, repeated links, bad hrefs and odd judges

        The rows are copied verbatim from cbca.gov/decisions/cda-cases.html
        (2026-11-04), with leading whitespace and blank lines removed. Only
        a few rows are kept from each year's table, and the <table> and
        <html> tags around them are simplified.
        """
        page = """<html><body>
<table id="AppealsDecisions2026" class="tablesorter"><tbody>
<tr>
<td>09/15/2026</td>
<td>CBCA 8821, 8829</td>
<td>
<a href="../files/decisions/2026/VOLK_09-15-26_8821__THE_GILCHRIST_LAW_FIRM_PA (DISMISSAL).pdf">The Gilchrist Law Firm, P.A.</a>
</td>
<td>Volk</td>
<td>Dismissal</td>
</tr>
<!-- Week Upload -->
<tr>
<td>09/15/2026</td>
<td>CBCA 8821, 8829</td>
<td>
<a href="../files/decisions/2026/VOLK_09-15-26_8821__THE_GILCHRIST_LAW_FIRM_PA (DISMISSAL).pdf">The Gilchrist Law Firm, P.A.</a>
</td>
<td>Volk</td>
<td>Dismissal</td>
</<tr>
</tbody></table>
<table id="AppealsDecisions2024" class="tablesorter"><tbody>
<tr><td>05/21/2024  </td><td>CBCA 7934</td><td><a href="../files/decisions/2024/OROURKE_05-21-24_7934__RLS_CONSTRUCTION_GROUP (DISMISSAL).pdf"> RLS Construction Group</td><td>O\u2019Rourke</td><td> Dismissal</td></tr
<tr><td>05/10/2024  </td><td>CBCA 8091</td><td><a href="../files/decisions/2024/BEARDSLEY_05-10-24_8091__FHC_CONTRACTING_INC (DISMISSAL).pdf"> FHC Contracting, Inc. </td><td>Beardsley</td><td> Dismissal</td></tr>
</tbody></table>
<table id="AppealsDecisions2023" class="tablesorter"><tbody>
<tr><td>06/08/2023  </td><td>CBCA 7529 </td><td><a href="../files/decisions/2023/KULLBERG_06-08-23_7529__INGLEWOOD_INVESTMENTS_A_DIVISION_OF_HELLENICS_LLC (DISMISSAL).pdf"> Inglewood Investments, A Division of Hellenics, LLC    </td><td> Kullburg</td><td> Dismissal</td></tr>
</tbody></table>
<table id="AppealsDecisions2022" class="tablesorter"><tbody>
<tr><td>04/04/2022  </td><td>CBCA 6802 </td><td><a href="../files/decisions/2022/SULLIVAN_04-04-22_6802__ROY_ANDERSON_CORP (Dismissal).pdf"> Roy Anderson Corp   </td><td> Sullivan </td><td > Dismissal</td></tr>
<td>03/16/2022  </td><td>CBCA 6400, 6401, 6700 </td><td><a href="../files/decisions/2022/CHADWICK_03-18-22_6400__INTERNATIONAL_DEVELOPMENT_SOLUTIONS_LLC (Decision).pdf"> International Development Solutions, LLC   </td><td> Chadwick </td><td > Decision</td></tr>
<tr><td>03/22/2022  </td><td>CBCA 5826, 6861, 6897, 7049 </td><td><a href="../files/decisions/2022/CHADWICK_03-22-22_5826__CTA_I_LLC (Decision).pdf"> CTA I, LLC   </td><td> Chadwick </td><td > Decision</td></tr>
</tbody></table>
<table id="AppealsDecisions2020" class="tablesorter"><tbody>
<tr><td>02/19/2020 </td><td>CBCA 5698-R </td><td><a href="../files/decisions/2020/RUSSELL_02-19-20_5698-R__STOBIL_ENTERPRISE (Decision).pdf"> Stobil Enterprise</a></td><td> Russell </td><td> Decision </td></tr>
<tr><td>02/19/2020 </td><td>CBCA 5698-R </td><td><a href="../files/decisions/2020/RUSSELL_02-20-20_5698-R__STOBIL_ENTERPRISE (Decision).pdf"> Stobil Enterprise</a></td><td> Per Curiam </td><td> Decision </td></tr>
</tbody></table>
<table id="AppealsDecisions2019" class="tablesorter"><tbody>
<tr><td>12/30/2019 </td><td>CBCA 6531 </td><td><a href="../files/decisions/2020/VERGILIO_12-30-19_6531__FMS_INVESTMENT_CORPORATION (Dismissal).pdf"> FMS Investment Corporation</a></td><td> Vergilio </td><td> Dismissal </td></tr>
<tr><td>12/30/2019 </td><td>CBCA 6531 </td><td><a href="files/decisions/2020/VERGILIO_12-30-19_6531__FMS_INVESTMENT_CORPORATION.pdf"> FMS Investment Corporation</a></td><td> Vergilio </td><td> Dismissal </td></tr>
<tr><td>12/05/2019 </td><td> CBCA 6517, 6601 </td><td><a href="../files/decisions/2019/SHERIDAN_12-05-19_6517, 6601__CH2M-WG_IDAHO,_LLC (Dismissal).pdf"> CH2M\uf05fWG Idaho, LLC</a></td><td> Sheridan </td><td> Dismissal </td></tr>
</tbody></table>
<table id="AppealsDecisions2016" class="tablesorter"><tbody>
<tr><td>09/16/2016</td><td> CBCA 5291 </td><td><a href="../files/decisions/2016/O'ROURKE_09-16-16_5291__BULLSEYE_INTERNATIONAL_SDVOB_INC_V_VA.pdf "> Bullseye International SDVOB, Inc. </a></td><td> O'Rourke </td><td> Decision </td></tr>
</tbody></table>
<table id="AppealsDecisions2014" class="tablesorter"><tbody>
<tr><td>03/10/2014</td><td> CBCA 2878</td><td><a href="../files/decisions/2014/DANIELS_03-10-14_2878__JANE_MOBLEY_ASSOCIATES_INC.pdf"> Jane Mobley Associates, Inc </a></td><td> Full Board </td></tr>
</tbody></table>
<table id="AppealsDecisions2012" class="tablesorter"><tbody>
<tr><td>7/11/2012</td><td>CBCA 2821</td><td><a href="../files/decisions/2012/MCCANN_07-11-12_2561__MEDICAL_CONSTRUCTION_GROUP_INC_508.pdf">Energy Enterprise Solutions, LLC</a></td><td>McCann</td></tr>
<tr><td>7/11/2012</td><td>CBCA 2800</td><td><a href="../files/decisions/2012/SHERIDAN_07-11-12_2800__JOINT_VENTURE_BETWEEN_WACKENHUT_PUERTO_RICO_INC_V_DEPARTMENT_OF_STATE_508.pdf">Joint Venture Between Wackenhut Puerto Rico, Inc., Wackenhut International, Inc., And Wackenhut Paraguay S.A.</a></td><td>Sheridan</td></tr>
<tr><td>7/11/2012</td><td>CBCA 2561</td><td><a href="../files/decisions/2012/MCCANN_07-11-12_2561__MEDICAL_CONSTRUCTION_GROUP_INC_508.pdf">Medical Construction Group, Inc.</a></td><td>McCann</td></tr>
</tbody></table>
</body></html>"""
        site = cbca.Site()
        site.html = html.fromstring(page)
        years = [2026, 2024, 2023, 2022, 2020, 2019, 2016, 2014, 2012]
        with self.assertLogs(logger, level="INFO") as logs:
            for year in years:
                site._parse_year(year)
        log = " ".join(logs.output)
        self.assertNotIn("ERROR", log)
        self.assertEqual(
            [c["docket"] for c in site.cases],
            [
                # Same row twice: kept once
                "CBCA 8821, 8829",
                # Row ending in "</tr" and the row after it
                "CBCA 7934",
                "CBCA 8091",
                "CBCA 7529",
                # The 6400 row has no opening <tr>
                "CBCA 6802",
                "CBCA 6400, 6401, 6700",
                "CBCA 5826, 6861, 6897, 7049",
                "CBCA 5698-R",
                "CBCA 5698-R",
                # 6531 is listed twice, once with a link missing "../"
                "CBCA 6531",
                "CBCA 6531",
                "CBCA 6517, 6601",
                "CBCA 5291",
                "CBCA 2878",
                # CBCA 2821 links to the CBCA 2561 file and is dropped
                "CBCA 2561",
                "CBCA 2800",
            ],
        )
        self.assertIn("CBCA 2821", log)
        by_docket = {}
        for c in site.cases:
            by_docket.setdefault(c["docket"], []).append(c)
        # The table date, not the date in the filename (03-18-22)
        self.assertEqual(
            by_docket["CBCA 6400, 6401, 6700"][0]["date"], "03/16/2022"
        )
        self.assertEqual(
            by_docket["CBCA 6531"][1]["url"],
            "https://www.cbca.gov/files/decisions/2020/VERGILIO_12-30-19_6531__FMS_INVESTMENT_CORPORATION.pdf",
        )
        self.assertEqual(
            by_docket["CBCA 5291"][0]["url"],
            "https://www.cbca.gov/files/decisions/2016/O'ROURKE_09-16-16_5291__BULLSEYE_INTERNATIONAL_SDVOB_INC_V_VA.pdf",
        )
        self.assertEqual(
            by_docket["CBCA 6517, 6601"][0]["name"], "CH2M-WG Idaho, LLC"
        )
        # The Judge column is passed through, misspelling and all (the PDF
        # is signed Kullberg)
        self.assertEqual(by_docket["CBCA 7529"][0]["judge"], "Kullburg")
        self.assertEqual(
            [(c["judge"], c["per_curiam"]) for c in by_docket["CBCA 5698-R"]],
            [("Russell", False), ("", True)],
        )
        self.assertEqual(
            (
                by_docket["CBCA 2878"][0]["judge"],
                by_docket["CBCA 2878"][0]["per_curiam"],
            ),
            ("", False),
        )
        self.assertNotIn("disposition", site.cases[0])

        # A missing table is an error, not an empty result
        with self.assertLogs(logger, level="ERROR"):
            site._parse_year(2011)
        # A row with no link is reported (made-up row)
        site.html = html.fromstring(
            '<table id="AppealsDecisions2013"><tr><td>1/2/2013</td>'
            "<td>CBCA 1</td><td>No Link</td><td>Judge</td></tr></table>"
        )
        with self.assertLogs(logger, level="ERROR"):
            site._parse_year(2013)

    def test_cbca_bad_rows_are_skipped(self):
        """An impossible date or a name that cleans to nothing is logged
        and the row skipped; the rest of the table is kept

        The first two rows are synthetic (made up for this test); the third
        is copied verbatim from cbca.gov/decisions/cda-cases.html.
        """
        page = """<html><body>
<table id="AppealsDecisions2024"><tbody>
<tr><td>02/30/2024</td><td>CBCA 1</td><td><a href="../files/decisions/2024/synthetic1.pdf">Synthetic Bad Date</a></td><td>Judge</td></tr>
<tr><td>05/01/2024</td><td>CBCA 2</td><td><a href="../files/decisions/2024/synthetic2.pdf"> , </a></td><td>Judge</td></tr>
<tr><td>05/10/2024  </td><td>CBCA 8091</td><td><a href="../files/decisions/2024/BEARDSLEY_05-10-24_8091__FHC_CONTRACTING_INC (DISMISSAL).pdf"> FHC Contracting, Inc. </td><td>Beardsley</td><td> Dismissal</td></tr>
</tbody></table>
</body></html>"""
        site = cbca.Site()
        site.html = html.fromstring(page)
        with self.assertLogs(logger, level="ERROR") as logs:
            site._parse_year(2024)
        errors = [line for line in logs.output if line.startswith("ERROR")]
        self.assertEqual(len(errors), 2)
        self.assertIn("02/30/2024", errors[0])
        self.assertIn("CBCA 2", errors[1])
        self.assertEqual([c["docket"] for c in site.cases], ["CBCA 8091"])

    def test_cbca_backscrape_date_range(self):
        """A backscrape downloads the page once and keeps only decisions
        dated inside the range, both ends inclusive

        The rows are copied verbatim from cbca.gov/decisions/cda-cases.html;
        only a few rows are kept from each table.
        """
        page = """<html><body>
<table id="AppealsDecisions2015" class="tablesorter"><tbody>
<tr><td>07/01/2015</td><td> CBCA 4358 </td><td><a href="../files/decisions/2015/WALTERS_07-01-15_4358__JTS_CONSTRUCTION.pdf"> JTS Construction Company </a></td><td> Walters </td><td> Dismissal </td></tr>
<tr><td>06/26/2015</td><td> CBCA 4562 </td><td><a href="../files/decisions/2015/KULLBERG_06-26-15_4562__GWSI,_INC..pdf"> GWSI, Inc. </a></td><td> Kullberg </td><td> Dismissal </td></tr>
<tr><td>01/02/2015</td><td> CBCA 3809, 3811, 3812 </td><td><a href="../files/decisions/2015/VERGILIO_01-02-15_3812__DEVELOPMENT_ALTERNATIVES,_INC..pdf"> Development Alternatives, Inc. </a></td><td> Vergilio </td><td>Dismissal</td></tr>
</tbody></table>
<table id="AppealsDecisions2014" class="tablesorter"><tbody>
<tr><td>12/29/2014</td><td> CBCA 3224</td><td><a href="../files/decisions/2014/DRUMMOND_12-29-14_3224__JOHN_RANDALL_CLARK,_CLARK'S_WELDING.pdf"> John Randall Clark </a></td><td> Drummond </td></tr>
</tbody></table>
</body></html>"""
        ranges = [
            (
                ("2015/01/02", "2015/06/26"),
                ["CBCA 4562", "CBCA 3809, 3811, 3812"],
            ),
            (("2015/01/03", "2015/06/25"), []),
            (
                ("2014/12/29", "2015/01/02"),
                ["CBCA 3809, 3811, 3812", "CBCA 3224"],
            ),
            (
                ("2015", "2015"),
                ["CBCA 4358", "CBCA 4562", "CBCA 3809, 3811, 3812"],
            ),
        ]
        downloads = []

        async def download():
            downloads.append(1)
            return html.fromstring(page)

        for (start, end), expected in ranges:
            with self.subTest(start=start, end=end):
                downloads.clear()

                site = cbca.Site(backscrape_start=start, backscrape_end=end)
                site._download = download
                self.assertEqual(len(site.back_scrape_iterable), 1)
                asyncio.run(
                    site._download_backwards(site.back_scrape_iterable[0])
                )
                self.assertEqual(len(downloads), 1)
                self.assertEqual([c["docket"] for c in site.cases], expected)
