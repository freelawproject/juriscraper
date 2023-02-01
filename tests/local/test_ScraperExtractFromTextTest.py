import unittest

from juriscraper.lib.importer import build_module_list
from juriscraper.OpinionSite import OpinionSite


class ScraperExtractFromText(unittest.TestCase):
    """Adds specific tests to specific courts that are more-easily tested
    without a full integration test.
    """

    test_data = {
        "juriscraper.opinions.united_states.administrative_agency.bia": [
            (
                """Matter of Emmanuel LAGUERRE, Respondent \nDecided January 20, 2022 and more """,
                {
                    "OpinionCluster": {
                        "date_filed": "2022-01-20",
                        "date_filed_is_approximate": False,
                    }
                },
            ),
            (
                "Matter of Enrique ALDAY-DOMINGUEZ, Respondent\nDecided June 1, 2017",
                {
                    "OpinionCluster": {
                        "date_filed": "2017-06-01",
                        "date_filed_is_approximate": False,
                    }
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.nm": [
            (
                """Opinion Number: _______________ Filing Date: January 10, 2022\nNO. S-1-SC-38247\nCITIZENS FOR FAIR RATES""",
                {"OpinionCluster": {"docket_number": "S-1-SC-38247"}},
            )
        ],
        "juriscraper.opinions.united_states.state.nmctapp": [
            (
                """Opinion Number: _______________ Filing Date: January 10, 2022\nNo. A-1-CA-39059\nCITIZENS FOR FAIR RATES""",
                {"OpinionCluster": {"docket_number": "A-1-CA-39059"}},
            )
        ],
        "juriscraper.opinions.united_states.state.ark": [
            (
                """HONORABLE JODI RAINES DENNIS,\nCite as 2022 Ark. 19\nSUPREME COURT OF ARKANSAS No. CV-21-173\n  ARKANSAS DEPARTMENT OF CORRECTION""",
                {"OpinionCluster": {"docket_number": "CV-21-173"}},
            ),
            # Some opinions don't have dockets because Arkansas publishes important announcements.
            (
                """Cite as 2022 Ark. 14\nSUPREME COURT OF ARKANSAS Opinion Delivered: January 27, 2022""",
                {"OpinionCluster": {"docket_number": ""}},
            ),
        ],
        "juriscraper.opinions.united_states.state.arkctapp": [
            (
                """Cite as 2022 Ark. App. 51\nARKANSAS COURT OF APPEALS\nDIVISION II No. CV-20-579\n  ADDAM MAXWELL V.\nLORI MAXWELL""",
                {"OpinionCluster": {"docket_number": "CV-20-579"}},
            ),
            (
                """Cite as 2022 Ark. App. 43\nARKANSAS COURT OF APPEALS\nDIVISION IV No. E-21-215\n  FRED JACKSON""",
                {"OpinionCluster": {"docket_number": "E-21-215"}},
            ),
        ],
        "juriscraper.opinions.united_states.federal_appellate.ca4": [
            (
                """USCA4 Appeal: 22-6079      Doc: 17         Filed: 07/26/2022    Pg: 1 of 2\n\n\n\n\n                                            UNPUBLISHED \n\n                               UNITED STATES COURT OF APPEALS\n""",
                {"OpinionCluster": {"precedential_status": "Unpublished"}},
            ),
            (
                """USCA4 Appeal: 22-6079      Doc: 17         Filed: 07/26/2022    Pg: 1 of 2\n\n\n\n\n                                            PUBLISHED\n\n                               UNITED STATES COURT OF APPEALS\n""",
                {"OpinionCluster": {"precedential_status": "Published"}},
            ),
        ],
        "juriscraper.opinions.united_states.state.nyappterm_1st": [
            (
                """<br>PRESENT: Brigantti, J.P., Hagler, Tisch, JJ. \n\n <br>570410/22 \n and more and more """,
                {"Docket": {"docket_number": "570410/22"}},
            ),
        ],
        "juriscraper.opinions.united_states.state.nyappterm_2nd": [
            (
                """SUPREME COURT, APPELLATE TERM, FIRST DEPARTMENT \nPRESENT: Brigantti, J.P., Hagler, Tisch, JJ. \n 570613/17 """,
                {"Docket": {"docket_number": "570613/17"}},
            ),
        ],
        "juriscraper.opinions.united_states.state.nysupct": [
            (
                """<br>Index No. 154867/2022 Robert R. Reed, J. \nThe following """,
                {"Docket": {"docket_number": "154867/2022"}},
            ),
        ],
        "juriscraper.opinions.united_states.state.sd": [
            (
                """#30018-a-MES\n2023 S.D. 4""",
                {"Docket": {"docket_number": "#30018-a-MES"}},
            ),
        ],
        "juriscraper.opinions.united_states.attorney_general.connag": [
            (
                """OFFICE OF THE ATTORNEY GENERAL\nCONNECTICUT\n\nwilliam tong\nattorney general\n\nJanuary 24, 2023\nBy Email""",
                {
                    "OpinionCluster": {
                        "date_filed": "2023-01-24",
                        "date_filed_is_approximate": False,
                    }
                },
            ),
        ],
        "juriscraper.opinions.united_states.attorney_general.indianaag": [
            (
                """STATE OF INDIANA\n\nOFFICE OF THE ATTORNEY GENERAL\n\nTODD ROKITA\nINDIANA ATTORNEY GENERAL\n\nINDIANA GOVERNMENT CENTER SOUTH, FIFTH FLOOR\n302 WEST WASHINGTON STREET, INDIANAPOLIS, IN 46204-2770\nwww.AttorneyGeneral.IN.gov\n\nTELEPHONE: 317.232.6201\nFAX: 317.232.7979\n\nFebruary 23, 2022\nOFFICIAL OPINION 2022-1""",
                {
                    "OpinionCluster": {
                        "date_filed": "2022-02-23",
                        "date_filed_is_approximate": False,
                    }
                },
            ),
        ],
        "juriscraper.opinions.united_states.attorney_general.ohag": [
            (
                """January 11, 2023\n\nThe Honorable Bradford W. Bailey\nHardin County Prosecuting Attorney\nOne Courthouse Square, Suite 50""",
                {
                    "OpinionCluster": {
                        "date_filed": "2023-01-11",
                        "date_filed_is_approximate": False,
                    }
                },
            ),
        ],
        "juriscraper.opinions.united_states.attorney_general.paag": [
            (
                """COMMONWEALTH OF PENNSYLVANIA\nOFFICE OF ATTORNEY GENERAL 16TH FLOOR\n\nSTRAWBERRY SQUARE\nJosH SHAPIRO HarrisBurs, PA 17120\n\nATTORNEY GENERAL (717) 787-3391\n\nHARRISBURG, PA 17120\n\nDecember 16, 2019\n\nColonel Robert Evanchick\nCommissioner\nPennsylvania State Police\n1800 Elmerton Avenue""",
                {
                    "OpinionCluster": {
                        "date_filed": "2019-12-16",
                        "date_filed_is_approximate": False,
                    }
                },
            ),
        ],
        "juriscraper.opinions.united_states.attorney_general.vaag": [
            (
                """COMMONWEALTH of VIRGINIA\n\nOffice of the Attorney General\nJason S. Miyares 202 North Ninth Street\nAttorney General Richmond, Virginia 23219\n804-786-2071\nFax 804-786-1991\nVirginia Relay Services\n\n800-828-1120\nJanuary 26, 2023 Tl-1\n\nThe Honorable James A. Leftwich, Jr.\nMember, """,
                {
                    "OpinionCluster": {
                        "date_filed": "2023-01-26",
                        "date_filed_is_approximate": False,
                    }
                },
            ),
        ],
        "juriscraper.opinions.united_states.attorney_general.tennag": [
            (
                """STATE OF TENNESSEE\n\nOFFICE OF THE ATTORNEY GENERAL\nJanuary 19, 2023\nOpinion No. 23-001\nElected School""",
                {
                    "OpinionCluster": {
                        "date_filed": "2023-01-19",
                        "date_filed_is_approximate": False,
                    }
                },
            ),
        ],
        "juriscraper.opinions.united_states.attorney_general.nevag": [
            (
                """AARON D. FORD JESSICA L. ADAIR.\nChief of Staff\n\nAttorney General\n\nKYLE E, N. GEORGE LESLIE NINO PIRO\n\nFirst Assistant Attorney General General Counsel\nCHRISTINE JONES BRADY STATE OF NEVADA HEIDI PARRY STERN\n\nSecond Assistant Attorney General OFFICE OF THE ATTORNEY GENERAL Solicitor General\n\n100 North Carson Street\nCarson City, Nevada 89701\nJuly 28, 2021\nOPINION NO. 2021-04 OFFICE OF""",
                {
                    "OpinionCluster": {
                        "date_filed": "2021-07-28",
                        "date_filed_is_approximate": False,
                    }
                },
            ),
        ],
        "juriscraper.opinions.united_states.attorney_general.coloag": [
            (
                """PHIL WEISER\nAttorney General\n\nRALPH L. CARR\nCOLORADO JUDICIAL CENTER\n1300 Broadway, 10th Floor\nDenver, Colorado 80203\nPhone (720) 508-6000\n\nNATALIE HANLON LEH\nChief Deputy Attorney General\nERIC R. OLSON\nSolicitor General\nERIC T. MEYER\nChief Operating Officer\n\nSTATE OF COLORADO\nDEPARTMENT OF LAW\n\n.\n\nFORMAL\nOPINION\nOF\nPHILIP J. WEISER\nAttorney General\n\n)\n)\n)\n)\n)\n)\n)\n\nOffice of the Attorney General\n\nNo. 21-01\nMarch 5, 2021\n\nKara Veitch, Executive Director""",
                {
                    "OpinionCluster": {
                        "date_filed": "2021-03-05",
                        "date_filed_is_approximate": False,
                    }
                },
            ),
        ],
        "juriscraper.opinions.united_states.attorney_general.nhag": [
            (
                """ATTORNEY GENERAL\nDEPARTMENT OF JUSTICE\n\n33 CAPITOL STREET\nCONCORD, NEW HAMPSHIRE 03301-6397\n\nJOHN M. FORMELLA\nATTORNEY GENERAL\n\nJAMES T. BOFFETTI\nDEPUTY ATTORNEY GENERAL\n\nATTORNEY GENERAL OPINION NO. 2022-01\n\nSeptember 1, 2022\n\nRobert L. Quinn,""",
                {
                    "OpinionCluster": {
                        "date_filed": "2022-09-01",
                        "date_filed_is_approximate": False,
                    }
                },
            ),
        ],
        "juriscraper.opinions.united_states.attorney_general.njag": [
            (
                """~~P~pF THE:\n~\nw\n~c7\nu>\ny\ny\n\nS'Tq~~oo\n~m\nE\nm\xcc\x80\n7~/f\n'7~r;\n5\n~\nF\n\n~5~~~e .4# ~.e~r Je~s~~\nCHRIS CHRISTIE\n\nOFFICE OF THE ATTORNEY GENERAL\n\nGovernor-\n\nDEPARTMENT OF LAW AMID PUBLIC SAFETY\n\nKIM GUADAGNO\n\nPO Box 080\nTRENTON NJO862S-0080\n\nLt. Governor\n\nCHRISTOPHER S. PORRINO\n\nAttorney General\n\nMay 11, 2017\n\nGregory L. Acquaviva\nChief Counsel""",
                {
                    "OpinionCluster": {
                        "date_filed": "2017-05-11",
                        "date_filed_is_approximate": False,
                    }
                },
            ),
        ],
        "juriscraper.opinions.united_states.attorney_general.nmiag": [
            (
                """Commonwealth of the Northern Mariana Islands\n\nOffice of the Attorney General\n2 floor Hon. Juan A. Sablan Memoriul Bldg.\nCaller Box 10007. Capitol Hill\nSaipan, MP 96950\n\nEDWARD MANIBUSAN\nAttorney General\n\nLILLIAN A. TENORIO\nDeputy Attorney General\n\nOAG 18-02\nSeptember 21, 2018\n\nSubject:""",
                {
                    "OpinionCluster": {
                        "date_filed": "2018-09-21",
                        "date_filed_is_approximate": False,
                    }
                },
            ),
        ],
        "juriscraper.opinions.united_states.attorney_general.vtag": [
            (
                """WILLIAM H. SORRELL TEL: (802) 828-3171\nATTORNEY GENERAL FAX: (802) 828-3187\nTTY: (802) 828-3665\nSUSANNE R. YOUNG\nDEPUTY ATTORNEY GENERAL http://www.atg.state.vt.us\nWILLIAM E. GRIFFIN\nCHIEF ASST. ATTORNEY\nGENERAL\n\nSTATE OF VERMONT\nOFFICE OF THE ATTORNEY GENERAL\n109 STATE STREET\nMONTPELIER, VT\n05609-1001\n\nFormal Opinion #2014-1\nMay 13, 2014\n\nHon. Jim Condos\nSecretary of State""",
                {
                    "OpinionCluster": {
                        "date_filed": "2014-05-13",
                        "date_filed_is_approximate": False,
                    }
                },
            ),
        ],
        "juriscraper.opinions.united_states.federal_special.cavc": [
            (
                """           UNITED STATES COURT OF APPEALS FOR VETERANS CLAIMS\n\n                                             NO. 22-3306\n\n                               GEORGE D. PREWITT, JR., PETITIONER,\n\n                                                  V.\n\n                                     DENIS MCDONOUGH,\n                         SECRETARY OF VETERANS AFFAIRS, RESPONDENT.\n\n                       Before""",
                {
                    "OpinionCluster": {
                        "case_name": "George D. Prewitt, Jr. v. Denis McDonough"
                    }
                },
            ),
            (
                """          UNITED STATES COURT OF APPEALS FOR VETERANS CLAIMS\n\n                                            No. 17-1428\n\n                                  JESUS G. ATILANO, APPELLANT,\n\n                                                 V.\n\n                                    DENIS MCDONOUGH,\n                          SECRETARY OF VETERANS AFFAIRS, APPELLEE.\n\n               On Remand""",
                {
                    "OpinionCluster": {
                        "case_name": "Jesus G. Atilano v. Denis McDonough"
                    }
                },
            ),
            (
                """                UNITED STATES COURT OF APPEALS FOR VETERANS CLAIMS\n\nNO. 20-4372\n\nSHERRY CRAIG-DAVIDSON,                                                            APPELLANT,\n\n         V.\n\nDENIS MCDONOUGH,\nSECRETARY OF VETERANS AFFAIRS,                                                    APPELLEE.\n\n                      Before GREENBERG, MEREDITH, and LAURER, Judges.""",
                {
                    "OpinionCluster": {
                        "case_name": "Sherry Craig-Davidson v. Denis McDonough"
                    }
                },
            ),
        ],
    }

    def test_extract_from_text(self):
        """Test that extract_from_text returns the expected data."""
        for module_string, test_cases in self.test_data.items():
            package, module = module_string.rsplit(".", 1)
            mod = __import__(
                f"{package}.{module}", globals(), locals(), [module]
            )
            site = mod.Site()
            for test_case in test_cases:
                self.assertEqual(
                    site.extract_from_text(test_case[0]), test_case[1]
                )

    def test_extract_from_text_properly_implemented(self):
        """Ensure that extract_from_text is properly implemented."""

        module_strings = build_module_list(
            "juriscraper.opinions.united_states"
        )
        for module_string in module_strings:
            package, module = module_string.rsplit(".", 1)
            mod = __import__(
                f"{package}.{module}", globals(), locals(), [module]
            )
            site = mod.Site()
            if mod.Site.extract_from_text == OpinionSite.extract_from_text:
                # Method is not overridden, so skip it.
                continue
            self.assertIn(
                module_string,
                self.test_data.keys(),
                msg=f"{module_string} not yet added to extract_from_text test data.",
            )
