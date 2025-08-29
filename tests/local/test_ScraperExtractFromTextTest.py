import logging
import unittest
from datetime import date, datetime

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
            (
                "Matter of O-A-R-G-, et al., Respondents\nDecided as amended April 16, 2025 1\n",
                {
                    "OpinionCluster": {
                        "date_filed": "2025-04-16",
                        "date_filed_is_approximate": False,
                    }
                },
            ),
            (
                "Matter of Leobardo DE JESUS-PLATON, Respondent\nDecided by Board January 17, 2025 1\n",
                {
                    "OpinionCluster": {
                        "date_filed": "2025-01-17",
                        "date_filed_is_approximate": False,
                    }
                },
            ),
            (
                "Matter of Foo, Respondent\nDecided by Attorney General April 30, 2025\n",
                {
                    "OpinionCluster": {
                        "date_filed": "2025-04-30",
                        "date_filed_is_approximate": False,
                    }
                },
            ),
            (
                "Matter of Bar, Respondent\nDecided by Acting Attorney General April 30, 2025\n",
                {
                    "OpinionCluster": {
                        "date_filed": "2025-04-30",
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
                {},
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
        "juriscraper.opinions.united_states.state.sd": [
            (
                # https://www.courtlistener.com/opinion/9456271/mcgee-v-spencer-quarries-inc/pdf/
                """#29901-aff in pt & rev in pt-PJD & SRJ\n2023 S.D. 66\nIN THE SUPREME COURT""",
                {
                    "Docket": {"docket_number": "29901"},
                    "OpinionCluster": {
                        "disposition": "Affirmed in part and reversed in part",
                        "judges": "Patricia J. DeVaney, Steven R. Jensen",
                    },
                },
                """#30354-SRJ\n2024 S.D. 58\nIN THE SUPREME COURT\nOF THE""",
                {
                    "Docket": {"docket_number": "30354"},
                    "OpinionCluster": {"judges": "Steven R. Jensen"},
                },
                # https://www.courtlistener.com/opinion/9406747/estate-of-beadle/?q=court_id%3Asd&page=8
                """#30086, #30094-r-SPM\n2023 S.D. 26\nIN THE SUPREME COURT\nOF THE\nSTATE OF SOUTH DAKOTA""",
                {
                    "Docket": {"docket_number": "30086, 30094"},
                    "OpinionCluster": {
                        "judges": "Scott P. Myren",
                        "disposition": "Reversed and remanded",
                    },
                },
            ),
        ],
        "juriscraper.opinions.united_states.territories.nmariana": [
            (
                """#E-FILED\nCNMI SUPREME COURT\nE-filed: Apr 18 2022 06:53AM\nClerk Review: Apr 18 2022 06:54AM Filing ID: 67483376\nCase No.: 2021-SCC-0017-CIV\nJudy Aldan""",
                {"Docket": {"docket_number": "2021-SCC-0017-CIV"}},
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
        "juriscraper.opinions.united_states.federal_bankruptcy.bap1": [
            (
                """UNITED STATES BANKRUPTCY APPELLATE PANEL\n           FOR THE FIRST CIRCUIT\n                      _______________________________\n\n                            BAP No. MW 00-005\n                      _______________________________\n\n              IN RE: INDIAN MOTOCYCLE CO., INC. ,\n       INDIAN MOTOCYCLE APPAREL AND ACCESSORIES, INC.\n              INDIAN MOTOCYCLE MANUF CO., INC.,\n                              Debtors.\n                  _______________________________\n\n                      UNITED STATES OF AMERICA,\n                               Appellant,\n\n                                       v.\n\n        STERLING CONSULTING CORP., COLORADO RECEIVER\n          and STEVEN M. RODOLAKIS, CHAPTER 7 TRUSTEE,\n                             Appellees.\n                  _______________________________\n\n               Appeal from the United States Bankruptcy Court\n                 for the District of Massachusetts (Worcester)\n                (Hon. Henry J. Boroff, U.S. Bankruptcy Judge)\n\n                      _______________________________\n\n                             Before\n         GOODMAN, DE JESÚS, VAUGHN, U.S. Bankruptcy Judges\n                _______________________________\n\n  Peter Sklarew, U.S. Department of Justice, and Donald K. Stern, U.S. Attorney, on\n  brief for the Appellant.\n\n  Joseph H. Baldiga, Paul W. Carey of Mirick, O’Connell, DeMallie & Lougee and\n  Stephan M. Rodolakis, Mark S. Foss of Peters Massad & Rodolakis, on brief for the\n  Appellees.\n\n                      _______________________________\n\n                               April 26, 2001\n                      _______________________________\n\n""",
                {
                    "OpinionCluster": {"date_filed": date(2001, 4, 26)},
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.nysupct_commercial": [
            (
                # https://nycourts.gov/reporter/3dseries/2023/2023_51345.htm
                """<table width="80%" border="1" cellspacing="2" cellpadding="5">\n<tbody><tr>\n<td align="center"><b>1125 Morris Ave. Realty LLC v Title Issues Agency\nLLC</b></td>\n</tr>\n<tr>\n<td align="center">2023 NY Slip Op 51345(U) [81 Misc 3d 1215(A)]</td>\n</tr>\n<tr>\n<td align="center">Decided on December 12, 2023</td>\n</tr>\n<tr>\n<td align="center">Supreme Court, Bronx County</td>\n</tr>\n<tr>\n<td align="center">Gomez, J.</td>\n</tr>\n<tr>\n<td align="center"><font color="#FF0000">Published by <a href="https://www.courts.state.ny.us/reporter/">New York State Law Reporting\nBureau</a> pursuant to Judiciary Law § 431.</font></td>\n</tr>\n<tr>\n<td align="center"><font color="#FF0000">This opinion is uncorrected and will not be\npublished in the printed Official Reports.</font></td></tr>\n</tbody></table><br><table width="75%" border="1" cellspacing="1" cellpadding="4" align="center"><tbody><tr><td><br><div align="center"><b><font size="+1">1125 Morris\nAvenue Realty LLC, Plaintiff(s),\n\n<br><br>against<br><br>Title Issues Agency LLC, MARTIN E. KOFMAN,\nSTEVEN LOWENTHAL, ESQ., and LOWENTHAL PC, "JOHN DOE," "JANE DOE,"\n"ABC CORPORATION," AND "XYZ CORPORATION,"\nDefendant(s).</font></b></div><br><br>\n\n</td></tr></tbody></table><br><br>Index No. 809156/23E\n<br><br><br>\n<br>Counsel for plaintiff: Law Office of Jan V Farensbach<br><br>Counsel for\ndefendants: Rosenberg &amp; Steinmetz PC<br>\n<br>\n\n\n<br>Fidel E. Gomez, J.\n\n<p>In this action for, <i>inter alia</i>, breach of contract, defendants TITLE ISSUES""",
                {
                    "Docket": {
                        "docket_number": "Index No. 809156/23E",
                        "case_name_full": '1125 Morris Avenue Realty LLC, Plaintiff(s), against Title Issues Agency LLC, MARTIN E. KOFMAN, STEVEN LOWENTHAL, ESQ., and LOWENTHAL PC, "JOHN DOE," "JANE DOE," "ABC CORPORATION," AND "XYZ CORPORATION," Defendant(s).',
                    },
                    "Opinion": {"author_str": "Fidel E. Gomez"},
                    "Citation": "81 Misc 3d 1215(A)",
                    "OpinionCluster": {
                        "case_name_full": '1125 Morris Avenue Realty LLC, Plaintiff(s), against Title Issues Agency LLC, MARTIN E. KOFMAN, STEVEN LOWENTHAL, ESQ., and LOWENTHAL PC, "JOHN DOE," "JANE DOE," "ABC CORPORATION," AND "XYZ CORPORATION," Defendant(s).'
                    },
                },
            )
        ],
        "juriscraper.opinions.united_states.state.nysupct": [
            (
                # https://www.nycourts.gov/reporter/pdfs/2019/2019_32654.pdf
                """Deboer v Friedman\n2019 NY Slip Op 32654(U)\nSeptember 4, 2019\nSupreme Court, New York County\nDocket Number: 654329/2018\nJudge: Arthur F. Engoron""",
                {
                    "Docket": {"docket_number": "654329/2018"},
                    "Opinion": {"author_str": "Arthur F. Engoron"},
                },
            ),
            (
                # https://www.nycourts.gov/reporter/pdfs/2019/2019_30152.pdf
                """1809 Emns Ave Inc. v American Signcrafters LLC\n2019 NY Slip Op 30152(U)\nJanuary 10, 2019\nSupreme Court, Kings County\nDocket Number: 517955/18\nJudge: Leon Ruchelsman""",
                {
                    "Docket": {"docket_number": "517955/18"},
                    "Opinion": {"author_str": "Leon Ruchelsman"},
                },
            ),
            (
                # https://www.nycourts.gov/reporter/pdfs/2021/2021_33275.pdf
                """Ciardiello v Village of New Paltz\n2021 NY Slip Op 33275(U)\nMarch 8, 2021\nSupreme Court, Ulster County\nDocket Number: Index No. EF18-3323\nJudge: Christopher E. Cahill""",
                {
                    "Docket": {"docket_number": "Index No. EF18-3323"},
                    "Opinion": {"author_str": "Christopher E. Cahill"},
                },
            ),
            (
                # https://www.nycourts.gov/reporter/pdfs/2018/2018_33709.pdf
                """Matter of Micklas v Town of Halfmoon Planning Bd.\n2018 NY Slip Op 33709(U)\nJanuary 10, 2018\nSupreme Court, Saratoga County\n Docket Number: 20171554\nJudge: Thomas D. Buchanan\nCases posted with a "30000""",
                {
                    "Docket": {"docket_number": "20171554"},
                    "Opinion": {"author_str": "Thomas D. Buchanan"},
                },
            ),
            (
                # https://www.nycourts.gov/reporter/pdfs/2023/2023_32445.pdf
                """Rothman v Puretz\n2023 NY Slip Op 32445(U)\nJuly 18, 2023\nSupreme Court, Monroe County\nDocket Number: Index No. E2023001856\nJudge: J. Scott Odorisi\nCases posted with a "30000" identifier, i""",
                {
                    "Docket": {"docket_number": "Index No. E2023001856"},
                    "Opinion": {"author_str": "Scott Odorisi"},
                },
            ),
            (
                # https://www.nycourts.gov/reporter/pdfs/2021/2021_30613.pdf
                """Dodaj v Lofti\n2021 NY Slip Op 30613(U)\nJanuary 13, 2021\nSupreme Court, Bronx County\nDocket Number: 20240/2019E\nJudge: Veronica G. Hummel""",
                {
                    "Docket": {"docket_number": "20240/2019E"},
                    "Opinion": {"author_str": "Veronica G. Hummel"},
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.nycountyct": [
            (
                # https://www.nycourts.gov/reporter/pdfs/2018/2018_33955.pdf
                """People v Wiltshire\n2018 NY Slip Op 33955(U)\nAugust 15, 2018\nCounty Court, Westchester County\nDocket Number: 18-0465-01\nJudge: Larry J. Schwartz""",
                {
                    "Docket": {"docket_number": "18-0465-01"},
                    "Opinion": {"author_str": "Larry J. Schwartz"},
                },
            ),
            (
                # https://www.nycourts.gov/reporter/3dseries/2020/2020_50084.htm  Docket number seems to be censored
                """<table width="80%" border="1" cellspacing="2" cellpadding="5" align="center">\n<tr>\n<td align="center"><b>People v J.S.</b></td>\n</tr>\n<tr>\n<td align="center">2020 NY Slip Op 50084(U) [66 Misc 3d 1213(A)]</td>\n</tr>\n<tr>\n<td align="center">Decided on January 17, 2020</td>\n</tr>\n<tr>\n<td align="center">County Court, Nassau County</td>\n</tr>\n<tr>\n<td align="center">Singer, J.</td>\n</tr>\n<tr>\n<td align="center">Published by New York State Law Reporting Bureau\npursuant to Judiciary Law § 431.</td>\n</tr>\n<tr>\n<td align="center">This opinion is uncorrected and will not be\npublished in the printed Official Reports.</td></tr>\n</table>\n<br><br>\n\nDecided on January 17, 2020\n<br><div align="center">County Court, Nassau County</div>\n\n<br><table width="75%" border="1" cellspacing="1" cellpadding="4" align="center"><tr><td><br><div align="center"><b>The People of the\nState of New York, Plaintiff,\n\n<br><br>against<br><br>J.S., Adolescent Offender.</b></div><br><br>\n\n</td></tr></table><br><br>FYC-00000-00\n<br><br>\n<br><br>N. Scott Banks, Attorney in Chief, Legal Aid Society of Nassau County, \n<br><br>Max Sullivan, Esq. \n<br><br>Hon. Madeline Singas, Nassau County District Attorney, \n<br><br>Christopher Mango, Esq. <p></p>\n\n\n<br>Conrad D. Singer, J.\n\n<br><br>The following paper""",
                {
                    "Docket": {
                        "docket_number": "FYC-00000-00",
                        "case_name_full": "The People of the State of New York, against J.S., Adolescent Offender.",
                    },
                    "Opinion": {"author_str": "Conrad D. Singer"},
                    "Citation": "66 Misc 3d 1213(A)",
                    "OpinionCluster": {
                        "case_name_full": "The People of the State of New York, against J.S., Adolescent Offender."
                    },
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.nycivct": [
            (
                # https://www.nycourts.gov/reporter/3dseries/2023/2023_23397.htm
                """<table width="80%" border="1" cellspacing="2" cellpadding="5" align="center">\n<tr>\n<td align="center"><b>City of New York v "Doe"</b></td>\n</tr>\n<tr>\n<td align="center">2023 NY Slip Op 23397</td>\n</tr>\n<tr>\n<td align="center">Decided on December 18, 2023</td>\n</tr>\n<tr>\n<td align="center">Civil Court Of The City Of New York, Bronx County</td>\n</tr>\n<tr>\n<td align="center">Zellan, J.</td>\n</tr>\n<tr>\n<td align="center">Published by New York State Law Reporting Bureau pursuant to Judiciary Law § 431.</td>\n</tr>\n<tr>\n<td align="center">This opinion is uncorrected and subject to revision before publication in the printed Official Reports.</td></tr>\n</table>\n<br><br>\nDecided on December 18, 2023\n<br><div align="center">Civil Court of the City of New York, Bronx County</div>\n\n<br><table width="75%" border="1" cellspacing="1" cellpadding="4" align="center"><tr><td><br><div align="center"><b>City \n\tof New York, Petitioner(s),\n\n<br><br>against<br><br>"John" "Doe" et al., Respondents.</b></div><br><br>\n\n</td></tr></table><br><br>Index No. LT-300755-22/BX\n<br><br><br>Maurice Dobson, Special Assistant Corporation Counsel, New York City Department of Housing Preservation &amp; Development (Isidore Scipio, of counsel), New York, NY, for petitioner.<br><br>April Whitehead, Irvington, NY, for respondents Alexander Aqel and Aqel Sheet Metal Inc.<p></p><br>Jeffrey S. Zellan, J. <p>Recitation, as required by CPLR 2219(a), of the papers considered in the review of this motion:</p>""",
                {
                    "Docket": {
                        "docket_number": "Index No. LT-300755-22/BX",
                        "case_name_full": 'City of New York, Petitioner(s), against "John" "Doe"',
                    },
                    "Opinion": {"author_str": "Jeffrey S. Zellan"},
                    "OpinionCluster": {
                        "case_name_full": 'City of New York, Petitioner(s), against "John" "Doe"'
                    },
                },
            ),
            (
                # https://www.nycourts.gov/reporter/3dseries/2023/2023_51315.htm
                """n<table width="80%" border="1" cellspacing="2" cellpadding="5" align="center">\n<tr>\n<td align="center"><b>201 E. 164th St. Assoc., LLC v Calderon</b></td>\n</tr>\n<tr>\n<td align="center">2023 NY Slip Op 51315(U) [81 Misc 3d 1211(A)]</td>\n</tr>\n<tr>\n<td align="center">Decided on December 4, 2023</td>\n</tr>\n<tr>\n<td align="center">Civil Court Of The City Of New York, Bronx County</td>\n</tr>\n<tr>\n<td align="center">Ibrahim, J.</td>\n</tr>\n<tr>\n<td align="center">Published by New York State Law Reporting\nBureau pursuant to Judiciary Law § 431.</td>\n</tr>\n<tr>\n<td align="center">This opinion is uncorrected and will not be\npublished in the printed Official Reports.</td></tr>\n</table>\n<br><br>\n\nDecided on December 4, 2023\n<br><div align="center">Civil Court of the City of New York, Bronx County</div>\n\n<br><table width="75%" border="1" cellspacing="1" cellpadding="4" align="center"><tr><td><br><div align="center"><b>201 East 164th\nStreet Associates, LLC, Petitioner,\n\n<br><br>against<br><br>Pastora Calderon &amp; ROSA IDALIA\nABDELNOUR, Respondents, \n     <br>"JOHN DOE" &amp; "JANE DOE" A/K/A DUNIA GOMEZ\nRespondents-Undertenants.</b></div><br><br>\n\n</td></tr></table><br><br>Index No. 11523/2020\n<br><br>\n<br>For Petitioner: Hertz, Cherson &amp; Rosenthal, PC<br><br>For Respondent:\nThe Bronx Defenders by Adam Markovics, Esq.<p></p>\n\n\nShorab Ibrahim, J.\n\n<p>Recitation, as required by C.P.L.R. § 2219(a), of the papers considered in\nreview of this motion.</p>""",
                {
                    "Docket": {
                        "docket_number": "Index No. 11523/2020",
                        "case_name_full": '201 East 164th Street Associates, LLC, against Pastora Calderon & ROSA IDALIA ABDELNOUR, "JOHN DOE" & "JANE DOE" A/K/A DUNIA GOMEZ Respondents-Undertenants.',
                    },
                    "Opinion": {"author_str": "Shorab Ibrahim"},
                    "OpinionCluster": {
                        "case_name_full": '201 East 164th Street Associates, LLC, against Pastora Calderon & ROSA IDALIA ABDELNOUR, "JOHN DOE" & "JANE DOE" A/K/A DUNIA GOMEZ Respondents-Undertenants.'
                    },
                    "Citation": "81 Misc 3d 1211(A)",
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.nysurct": [
            (
                # https://www.nycourts.gov/reporter/3dseries/2023/2023_50144.htm
                """<table width="80%" border="1" cellspacing="2" cellpadding="5" align="center">\n<tr>\n<td align="center"><b>Matter of Pia Jeong Yoon</b></td>\n</tr>\n<tr>\n<td align="center">2023 NY Slip Op 50144(U) [78 Misc 3d 1203(A)]</td>\n</tr>\n<tr>\n<td align="center">Decided on February 28, 2023</td>\n</tr>\n<tr>\n<td align="center">Surrogate\'s Court, Queens County</td>\n</tr>\n<tr>\n<td align="center">Kelly, S.</td>\n</tr>\n<tr>\n<td align="center">Published by New York State Law Reporting\nBureau pursuant to Judiciary Law § 431.</td>\n</tr>\n<tr>\n<td align="center">This opinion is uncorrected and will not be\npublished in the printed Official Reports.</td></tr>\n</table>\n<br><br>\n\nDecided on February 28, 2023\n<br><div align="center">Surrogate\'s Court, Queens County</div>\n\n<br><table width="75%" border="1" cellspacing="1" cellpadding="4" align="center"><tr><td><br><div align="center"><b>Probate\nProceeding, Will of Pia Jeong Yoon, a/k/a PIA JEONG AE YOON, \n     <br>a/k/a PIA J. YOON, a/k/a JEONG YOON, a/k/a JEONG AE YOON,\nDeceased.\n</b></div><br><br>\n</td></tr></table><br><br>File No. 2021-31/C\n<br><br>\n<br>Petitioner\'s Attorney: J. John Kim. Esq<br><br>\n<br>Petitioner's Attorney: J. John Kim. Esq.<br>Pashman Stein Walder Hayden,\nPC<br>2900 Westchester Avenue, Suite 204, Purchase, New York 10577<br>(201)\n270-5470<br><br>Respondent's Attorney: Charlotte C. Lee, Esq.<br>277\nBroadway, Suite 400<br>New York, NY 10007<br>(212) 732-3366<p></p>\n\n\nPeter J. Kelly, S.\n\n<p>Petitioner moves for summary judgment in this proceeding which seeks leave to""",
                {
                    "Docket": {
                        "docket_number": "File No. 2021-31/C",
                        "case_name_full": "Probate Proceeding, Will of Pia Jeong Yoon, a/k/a PIA JEONG AE YOON, a/k/a PIA J. YOON, a/k/a JEONG YOON, a/k/a JEONG AE YOON",
                    },
                    "Opinion": {"author_str": "Peter J. Kelly"},
                    "Citation": "78 Misc 3d 1203(A)",
                    "OpinionCluster": {
                        "case_name_full": "Probate Proceeding, Will of Pia Jeong Yoon, a/k/a PIA JEONG AE YOON, a/k/a PIA J. YOON, a/k/a JEONG YOON, a/k/a JEONG AE YOON"
                    },
                },
            ),
            (
                # https://www.nycourts.gov/reporter/pdfs/2020/2020_34495.pdf
                """Matter of Christopher J. A.\n2020 NY Slip Op 34495(U)\nMarch 16, 2020\nSurrogate\'s Court, Bronx County\nDocket Number: 81G1998/K\nJudge: Nelida Malave-Gonzalez\nCases posted with a "30000" identifier, i.e., 2013 NY Slip\nOp 30001(U)""",
                {
                    "Docket": {"docket_number": "81G1998/K"},
                    "Opinion": {"author_str": "Nelida Malave-Gonzalez"},
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.nyfamct": [
            (
                # https://www.nycourts.gov/reporter/3dseries/2020/2020_50049.htm
                """<table width="80%" border="1" cellspacing="2" cellpadding="5" align="center">\n<tr>\n<td align="center"><b>Matter of Robyn C. v William M.J.</b></td>\n</tr>\n<tr>\n<td align="center">2020 NY Slip Op 50049(U) [66 Misc 3d 1210(A)]</td>\n</tr>\n<tr>\n<td align="center">Decided on January 16, 2020</td>\n</tr>\n<tr>\n<td align="center">Family Court, Kings County</td>\n</tr>\n<tr>\n<td align="center">Vargas, J.</td>\n</tr>\n<tr>\n<td align="center">Published by New York State Law Reporting Bureau\npursuant to Judiciary Law § 431.</td>\n</tr>\n<tr>\n<td align="center">This opinion is uncorrected and will not be\npublished in the printed Official Reports.</td></tr>\n</table>\n<br><br>\n\nDecided on January 16, 2020\n<br><div align="center">Family Court, Kings County</div>\n\n<br><table width="75%" border="1" cellspacing="1" cellpadding="4" align="center"><tr><td><br><div align="center"><b>In the Matter of a\nProceeding Under Article 6 of the Family Court Act Robyn C., Petitioner,\n\n<br><br>against<br><br>William M. J. (Deceased) and EVA JANE P.,\nRespondent.</b></div><br><br>\n\n</td></tr></table><br><br>G-10994-19\n<br><br><br>The mother was represented by Elaine McKnight, Esq., 457 56th Street, Brooklyn,\nNY 11220, Tel. (917) 476-2900; Paramour was represented by Sharyn M. Duncan, Esq., 32\nCourt St., Suite 707, Brooklyn, NY 11201, sharynmdrushing@msn.com, Phone: (718)\n625-6777; and the Child is represented by Alyana Love, Esq, Children's Law Center.<p></p>\n\n\n<br>Javier E. Vargas, J.\n\n<br><br>Papers Numbered<br><br>Summons, Petition, Affidavit &amp; Exhibits Annexed\n1<br><br>Notice of Motion, Affirmation &amp; Exhibits Annexed 2<br><br>Notice of""",
                {
                    "Docket": {
                        "docket_number": "G-10994-19",
                        "case_name_full": "In the Matter of a Proceeding Under Article 6 of the Family Court Act Robyn C., against William M. J. (Deceased) and EVA JANE P.",
                    },
                    "Opinion": {"author_str": "Javier E. Vargas"},
                    "Citation": "66 Misc 3d 1210(A)",
                    "OpinionCluster": {
                        "case_name_full": "In the Matter of a Proceeding Under Article 6 of the Family Court Act Robyn C., against William M. J. (Deceased) and EVA JANE P."
                    },
                },
            ),
            (
                # https://www.nycourts.gov/reporter/3dseries/2022/2022_50020.htm
                """<table width="80%" border="1" cellspacing="2" cellpadding="5" align="center">\n<tr>\n<td align="center"><b>Matter of Michelle B. v Thomas Y.</b></td>\n</tr>\n<tr>\n<td align="center">2022 NY Slip Op 50020(U) [73 Misc 3d 1238(A)]</td>\n</tr>\n<tr>\n<td align="center">Decided on January 11, 2022</td>\n</tr>\n<tr>\n<td align="center">Family Court, Kings County</td>\n</tr>\n<tr>\n<td align="center">Vargas, J.</td>\n</tr>\n<tr>\n<td align="center">Published by New York State Law Reporting Bureau\npursuant to Judiciary Law § 431.</td>\n</tr>\n<tr>\n<td align="center">This opinion is uncorrected and will not be\npublished in the printed Official Reports.</td></tr>\n</table>\n<br><br>\n\nDecided on January 11, 2022\n<br><div align="center">Family Court, Kings County</div>\n\n<br><table width="75%" border="1" cellspacing="1" cellpadding="4" align="center"><tr><td><br><div align="center"><b>In the Matter of a\nProceeding for Support Under Article 4 of the Family Court Act Michelle B., Petitioner,\n\n<br><br>against<br><br>Thomas Y., Respondent.</b></div><br><br>\n\n</td></tr></table><br><br>Docket No. F-30317/2004/19F\n<br><br><br>\n<br><br>The mother was represented by Rena C. Dawson, Esq., Karasayk &amp; Moschella,\nLLP, 233 Broadway, suite 2340, New York, NY 10006, Phone: (212) 233-3800,\nrdawson@kmattorneys.com ; the Father was unrepresented.<p></p>\n\n\n<br>Javier E. Vargas, J.\n""",
                {
                    "Docket": {
                        "docket_number": "Docket No. F-30317/2004/19F",
                        "case_name_full": "In the Matter of a Proceeding for Support Under Article 4 of the Family Court Act Michelle B., against Thomas Y.",
                    },
                    "Opinion": {"author_str": "Javier E. Vargas"},
                    "Citation": "73 Misc 3d 1238(A)",
                    "OpinionCluster": {
                        "case_name_full": "In the Matter of a Proceeding for Support Under Article 4 of the Family Court Act Michelle B., against Thomas Y."
                    },
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.nycrimct": [
            (
                # https://www.nycourts.gov/reporter/3dseries/2018/2018_50128.htm
                """<table width="80%" border="1" cellspacing="2" cellpadding="5" align="center">\n<tr>\n<td align="center"><b>People v Hot</b></td>\n</tr>\n<tr>\n<td align="center">2018 NY Slip Op 50128(U) [58 Misc 3d 1215(A)]</td>\n</tr>\n<tr>\n<td align="center">Decided on January 18, 2018</td>\n</tr>\n<tr>\n<td align="center">Criminal Court Of The City Of New York, Kings County</td>\n</tr>\n<tr>\n<td align="center">Leo, J.</td>\n</tr>\n<tr>\n<td align="center">Published by New York State Law Reporting Bureau\npursuant to Judiciary Law § 431.</td>\n</tr>\n<tr>\n<td align="center">This opinion is uncorrected and will not be\npublished in the printed Official Reports.</td></tr>\n</table>\n<br><br>\n\nDecided on January 18, 2018\n<br><div align="center">Criminal Court of the City of New York, Kings County</div>\n\n<br><table width="75%" border="1" cellspacing="1" cellpadding="4" align="center"><tr><td><br><div align="center"><b>The People of the\nState of New York\n\n<br><br>against<br><br>Amela Hot, Defendant.</b></div><br><br>\n\n</td></tr></table><br><br>2017KN054132\n<br><br><br>Labe M. Richman, 305 Broadway, Suite 100, New York, New York, 10007, attorney\nfor defendant Amela Hot<br><br>Eric Gonzalez, District Attorney, Kings County, by Sapna\nKishnani Esq., Assistant District Attorney, Brooklyn, of Counsel for the People<p></p>\n\n\n<br>Donald Leo, J.\n""",
                {
                    "Docket": {
                        "docket_number": "2017KN054132",
                        "case_name_full": "The People of the State of New York against Amela Hot",
                    },
                    "Opinion": {"author_str": "Donald Leo"},
                    "Citation": "58 Misc 3d 1215(A)",
                    "OpinionCluster": {
                        "case_name_full": "The People of the State of New York against Amela Hot"
                    },
                },
            ),
            (
                # https://www.nycourts.gov/reporter/3dseries/2018/2018_50503.htm
                """<table width="80%" border="1" cellspacing="2" cellpadding="5" align="center">\n<tr>\n<td align="center"><b>People v Smith</b></td>\n</tr>\n<tr>\n<td align="center">2018 NY Slip Op 50503(U) [59 Misc 3d 1211(A)]</td>\n</tr>\n<tr>\n<td align="center">Decided on March 16, 2018</td>\n</tr>\n<tr>\n<td align="center">Criminal Court Of The City Of New York, Queens County</td>\n</tr>\n<tr>\n<td align="center">Drysdale, J.</td>\n</tr>\n<tr>\n<td align="center">Published by New York State Law Reporting Bureau\npursuant to Judiciary Law § 431.</td>\n</tr>\n<tr>\n<td align="center">This opinion is uncorrected and will not be\npublished in the printed Official Reports.</td></tr>\n</table>\n<br><br>\n\nDecided on March 16, 2018\n<br><div align="center">Criminal Court of the City of New York, Queens County</div>\n\n<br><table width="75%" border="1" cellspacing="1" cellpadding="4" align="center"><tr><td><br><div align="center"><b>The People of the\nState of New York, Plaintiff,\n\n<br><br>against<br><br>James Smith, Defendant.</b></div><br><br>\n\n</td></tr></table><br><br>CR-024874-17QN\n<br><br>\n<br><br>ADA Mattew Powers, ADA Kevin Timpone &amp; ADA Latoya Cryder, for the\nPeople<br><br>Virginia A. Conroy, Esq., for the Defendant<p></p>\n\n\n<br>Althea E. Drysdale, J.\n\n<p>The defendant, James Smith, is charged with driving while intoxicated (VTL §""",
                {
                    "Docket": {
                        "docket_number": "CR-024874-17QN",
                        "case_name_full": "The People of the State of New York, against James Smith",
                    },
                    "Opinion": {"author_str": "Althea E. Drysdale"},
                    "Citation": "59 Misc 3d 1211(A)",
                    "OpinionCluster": {
                        "case_name_full": "The People of the State of New York, against James Smith"
                    },
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.nyclaimsct": [
            (
                # https://www.nycourts.gov/reporter/pdfs/2018/2018_34469.pdf
                """Lawrence v State of N.Y. Dept. of\nCommunity Supervision\n2018 NY Slip Op 34469(U)\nJanuary 10, 2018\nCourt of Claims\nDocket Number: Index No. 2010-038-505\nJudge: W. Brooks DeBow""",
                {
                    "Docket": {"docket_number": "Index No. 2010-038-505"},
                    "Opinion": {"author_str": "W. Brooks Debow"},
                },
            ),
            (
                # https://www.nycourts.gov/reporter/3dseries/2023/2023_50204.htm
                """<div>\n\nMartinaj v State of New York (2023 NY Slip Op 50204(U))\n<table width="80%" border="1" cellspacing="2" cellpadding="5" align="center">\n<tr>\n<td align="center"><b>Martinaj v State of New York</b></td>\n</tr>\n<tr>\n<td align="center">2023 NY Slip Op 50204(U) [78 Misc 3d 1211(A)]</td>\n</tr>\n<tr>\n<td align="center">Decided on March 2, 2023</td>\n</tr>\n<tr>\n<td align="center">Court Of Claims</td>\n</tr>\n<tr>\n<td align="center">Vargas, J.</td>\n</tr>\n<tr>\n<td align="center">Published by New York State Law Reporting\nBureau pursuant to Judiciary Law § 431.</td>\n</tr>\n<tr>\n<td align="center">This opinion is uncorrected and will not be\npublished in the printed Official Reports.</td></tr>\n</table>\n<br><br>\n\nDecided on March 2, 2023\n<br><div align="center">Court of Claims</div>\n\n<br><table width="75%" border="1" cellspacing="1" cellpadding="4" align="center"><tr><td><br><div align="center"><b>Bernardo\nMartinaj, Claimant,\n\n<br><br>against<br><br>State of New York, Defendant.</b></div><br><br>\n\n</td></tr></table><br><br>Claim No. 136323-A\n<br><br><br>\n<br>For Claimant:<br>Bernardo Martinaj, Pro se<br><br>For Defendant:<br>Hon. Letitia James, Attorney General of the State of New York<br>By: Douglas R.\nKemp, Esq. Assistant Attorney General<p></p>\n\n\nJavier E. Vargas, J.\n\n<p>This Court having presided over the instant trial on February 7, 2023, heard the""",
                {
                    "Docket": {
                        "docket_number": "Claim No. 136323-A",
                        "case_name_full": "Bernardo Martinaj, against State of New York",
                    },
                    "Opinion": {"author_str": "Javier E. Vargas"},
                    "OpinionCluster": {
                        "case_name_full": "Bernardo Martinaj, against State of New York"
                    },
                    "Citation": "78 Misc 3d 1211(A)",
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.nydistct": [
            (
                # https://nycourts.gov/reporter/3dseries/2023/2023_51308.htm
                """<table width="80%" border="1" cellspacing="2" cellpadding="5" align="center">\n<tr>\n<td align="center"><b>Sims v Regis</b></td>\n</tr>\n<tr>\n<td align="center">2023 NY Slip Op 51308(U) [81 Misc 3d 1210(A)]</td>\n</tr>\n<tr>\n<td align="center">Decided on November 30, 2023</td>\n</tr>\n<tr>\n<td align="center">District Court Of Nassau County, Second District</td>\n</tr>\n<tr>\n<td align="center">Montesano, J.</td>\n</tr>\n<tr>\n<td align="center">Published by New York State Law Reporting\nBureau pursuant to Judiciary Law § 431.</td>\n</tr>\n<tr>\n<td align="center">This opinion is uncorrected and will not be\npublished in the printed Official Reports.</td></tr>\n</table>\n<br><br>\n\nDecided on November 30, 2023\n<br><div align="center">District Court of Nassau County, Second District</div>\n\n<br><table width="75%" border="1" cellspacing="1" cellpadding="4" align="center"><tr><td><br><div align="center"><b>Alistair Sims,\nClaimant,\n\n<br><br>against<br><br>Lance Frantz Regis A/K/A LANCE REGIS A/K/A\nLANCE F. REGIS A/K/A FRANTZ L. REGISTRE A/K/A REGISTRE FRANTZ\nA/K/A VANCE REGIS A/K/A REGIS LANCE A/K/A REGIS L. FRANTZ,\nDefendant(s).</b></div><br><br>\n\n</td></tr></table><br><br>Index No. SC-000830-23/NA \n<<br><br>\n<br>Alistair Sims; Lance Regis<br>\n\n\n<br>Michael A. Montesano, J.\n\n<p class="auto-style1">Papers Considered:</p>""",
                {
                    "Docket": {
                        "docket_number": "Index No. SC-000830-23/NA",
                        "case_name_full": "Alistair Sims, against Lance Frantz Regis A/K/A LANCE REGIS A/K/A LANCE F. REGIS A/K/A FRANTZ L. REGISTRE A/K/A REGISTRE FRANTZ A/K/A VANCE REGIS A/K/A REGIS LANCE A/K/A REGIS L. FRANTZ, Defendant(s).",
                    },
                    "Opinion": {"author_str": "Michael A. Montesano"},
                    "Citation": "81 Misc 3d 1210(A)",
                    "OpinionCluster": {
                        "case_name_full": "Alistair Sims, against Lance Frantz Regis A/K/A LANCE REGIS A/K/A LANCE F. REGIS A/K/A FRANTZ L. REGISTRE A/K/A REGISTRE FRANTZ A/K/A VANCE REGIS A/K/A REGIS LANCE A/K/A REGIS L. FRANTZ, Defendant(s)."
                    },
                },
            )
        ],
        "juriscraper.opinions.united_states.state.nyjustct": [
            (
                # https://nycourts.gov/reporter/3dseries/2023/2023_51421.htm
                """<table width="80%" border="1" cellspacing="2" cellpadding="5" align="center">\n<tr>\n<td align="center"><b>People v Brennan</b></td>\n</tr>\n<tr>\n<td align="center">2023 NY Slip Op 51421(U)</td>\n</tr>\n<tr>\n<td align="center">Decided on December 22, 2023</td>\n</tr>\n<tr>\n<td align="center">Justice Court Of The Village Of Piermont, Rockland County</td>\n</tr>\n<tr>\n<td align="center">Ruby, J.</td>\n</tr>\n<tr>\n<td align="center">Published by New York State Law Reporting Bureau pursuant to Judiciary Law § 431.</td>\n</tr>\n<tr>\n<td align="center">This opinion is uncorrected and will not be published in the printed Official Reports.</td></tr>\n</table>\n<br><br>\n\nDecided on December 22, 2023\n<br><div align="center">Justice Court of the Village of Piermont, Rockland County</div>\n\n<br><table width="75%" border="1" cellspacing="1" cellpadding="4" align="center"><tr><td><br><div align="center"><b>People of the State of New York, Plaintiff,\n\n<br><br>against<br><br>Matthew Brennan, Defendant.</b></div><br><br>\n\n</td></tr></table><br><br>Case No. 23-050020\n<br><br>\n<br><br>For the People:Denise L. Weiss, Esq., Deputy Town Attorney, Town of Clarkstown \n<br><br>For the Defendant:Matthew Brennan, pro se<p></p>\n\n\n<br>Marc R. Ruby, J.\n\n<p class="auto-style1">RELEVANT FACTS AND PROCEDURAL HISTORY</p>\n<p>This action was tra""",
                {
                    "Docket": {
                        "docket_number": "Case No. 23-050020",
                        "case_name_full": "People of the State of New York, against Matthew Brennan",
                    },
                    "Opinion": {"author_str": "Marc R. Ruby"},
                    "OpinionCluster": {
                        "case_name_full": "People of the State of New York, against Matthew Brennan"
                    },
                },
            )
        ],
        "juriscraper.opinions.united_states.state.nycityct": [
            (
                # https://nycourts.gov/reporter/3dseries/2023/2023_23374.htm
                """<div>\n\nPotentia Mgt. Group, LLC v D.W. (2023 NY Slip Op 23374)\n\n\n\n\n[*1]\n<table width="80%" border="1" cellspacing="2" cellpadding="5" align="center">\n<tr>\n<td align="center"><b>Potentia Mgt. Group, LLC v D.W.</b></td>\n</tr>\n<tr>\n<td align="center">2023 NY Slip Op 23374</td>\n</tr>\n<tr>\n<td align="center">Decided on December 1, 2023</td>\n</tr>\n<tr>\n<td align="center">Utica City Court</td>\n</tr>\n<tr>\n<td align="center">Giruzzi, J.</td>\n</tr>\n<tr>\n<td align="center">Published by New York State Law Reporting Bureau pursuant to Judiciary Law § 431.</td>\n</tr>\n<tr>\n<td align="center">This opinion is uncorrected and subject to revision before publication in the printed Official Reports.</td></tr>\n</table>\n<br><br>\nDecided on December 1, 2023\n<br><div align="center">Utica City Court</div>\n\n<br><table width="75%" border="1" cellspacing="1" cellpadding="4" align="center"><tr><td><br><div align="center"><b>Potentia Management Group, LLC\n\n<br><br>against<br><br>D.W.</b></div><br><br>\n\n</td></tr></table><br><br>Docket No. CV-00357-23\n<<br><br>Ralph W. Fusco, Esq., for the Plaintiff<br><br>Benjamin M. Burdick, Esq., for the Defendant<p></p>\n\n\n<br>F. Christopher Giruzzi, J.\n\n<p class="auto-style1">Procedural History</p>\n<i>a. Initial Filings</i><p>On February 10, 2023, Potentia Management Group, LLC, (hereinafter referred to as Potentia Management and / o""",
                {
                    "Docket": {
                        "docket_number": "Docket No. CV-00357-23",
                        "case_name_full": "Potentia Management Group, LLC against D.W.",
                    },
                    "Opinion": {"author_str": "F. Christopher Giruzzi"},
                    "OpinionCluster": {
                        "case_name_full": "Potentia Management Group, LLC against D.W."
                    },
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.nd": [
            (
                # Case without paragraph numbers
                # https://www.courtlistener.com/api/rest/v3/opinions/10473075/
                """IN THE SUPREME COURT\n                  STATE OF NORTH DAKOTA\n\n                                2024 ND 143\n\nRonald Wayne Wootan,                                 Petitioner and Appellant\n      v.\nState of North Dakota,                              Respondent and Appellee\n\n                                No. 20240025\n\nAppeal from the District Court of Rolette County, Northeast Judicial District,\nthe Honorable Anthony S. Benson, Judge.\n\nAFFIRMED.\n\nPer Curiam.\n\nKiara C. Kraus-Parr, Grand Forks, ND, for petitioner and appellant.\n\nBrian D. Grosinger, State’s Attorney, Rolla, ND, for respondent and appellee.\n\f                               Wootan v. State\n                                No. 20240025\n\nPer Curiam.\n\n      Ronald Wootan appeals from an order denying his postconviction relief\napplication entered after the district court held an evidentiary hearing on\nremand. See Wootan v. State,""",
                {
                    "Citation": "2024 ND 143",
                },
            ),
            (
                # Example of a consolidated case
                # https://www.courtlistener.com/api/rest/v3/opinions/10473085/
                """IN THE SUPREME COURT\n                        STATE OF NORTH DAKOTA\n\n                                      2024 ND 141\n\nRenae Irene Gerszewski,                                           Petitioner and Appellee\n      v.\nConrad Keith Rostvet,                                          Respondent and Appellant\n\n\n\n                                     No. 20230361\n\n\n\nConrad Keith Rostvet,                                            Petitioner and Appellant\n      v.\nRenae Irene Gerszewski,                                         Respondent and Appellee\n\n\n\n                                     No. 20230362\n\n\n\nConrad Rostvet,                                                  Petitioner and Appellant\n      v.\nWayne Gerszewski,                                               Respondent and Appellee\n\n\n\n                                     No. 20230363\n\n\n\nAppeal from the District Court of Walsh County, Northeast Judicial District, the Honorable\nBarbara L. Whelan, Judge.\n\fAFFIRMED.\n\nOpinion of the Court by Tufte, Justice.\n\nSamuel A. Gereszek, Grand Forks, N.D., for appellees.\n\nTimothy C. Lamb, Grand Forks, N.D., for appellant.\n\f                                 Gerszewski v. Rostvet\n                                Nos. 20230361–20230363\n\nTufte, Justice.\n\n[¶1] Conrad Rostvet appeals from a district court’s order""",
                {
                    "Citation": "2024 ND 141",
                    "OpinionCluster": {"case_name": "Gerszewski v. Rostvet"},
                    "Docket": {
                        "case_name": "Gerszewski v. Rostvet",
                        "docket_number": "Nos. 20230361-20230363",
                    },
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.wis": [
            (
                # https://www.wicourts.gov/sc/opinion/DisplayDocument.pdf?content=pdf&seqNo=669658
                """2023 WI 50\nS C W\nUPREME OURT OF ISCONSIN\nCASE NO.: 2021AP938-CR\nCOMPLETE TITLE: State of Wisconsin,""",
                {
                    "Citation": "2023 WI 50",
                },
            )
        ],
        "juriscraper.opinions.united_states.state.wisctapp": [
            (
                # https://www.wicourts.gov/ca/opinion/DisplayDocument.pdf?content=pdf&seqNo=799325
                """2024 WI App 36\nCOURT OF APPEALS OF WISCONSIN\nPUBLISHED OPINION""",
                {
                    "Citation": "2024 WI App 36",
                },
            )
        ],
        "juriscraper.opinions.united_states.state.conn": [
            # Example with Syllabus https://www.courtlistener.com/opinion/9505807/markley-v-state-elections-enforcement-commission/
            (
                """   2                                     ,0                          0 Conn. 1\n                    Markley v. State Elections Enforcement Commission\n\n\n              JOE MARKLEY ET AL. v. STATE ELECTIONS\n                   ENFORCEMENT COMMISSION\n                           (SC 20726)\n             Robinson, C. J., and McDonald, Mullins, Ecker and Alexander, Js.\n\n                                            Syllabus\n\n         The plaintiffs, M and S, candidates for state legislative offices in the 2014\n            general election, appealed to the trial court from the decision of the\n            defendant, the State Elections Enforcement Commission, which\n            assessed fines against the plaintiffs upon determining that they had\n            violated certain state statutes and regulations governing campaign\n            financing and the Citizens’ Election Program (program) (§ 9-700 et seq.).\n            The plaintiffs’ respective campaign committees had each applied for\n            and received public funding grants through the program. During the 2014\n            election cycle, the plaintiffs’ campaign committees published certain\n            communications and advertisements that made various references to\n            the record and policies of D, then the governor, who was running for\n            reelection at that time. The communications both touted the plaintiffs’\n            respective accomplishments and positions and referred to their opposi-\n            tion to the agenda advanced by D and D’s Democratic allies, including\n            tax hikes and increased spending. One of the communications high-\n            lighted votes taken by S’s opponent in the 2014 election, C, when C\n            was serving as a state representative. C filed a complaint with the\n            commission, alleging that the communications were impermissible cam-\n            paign expenditures under the program. C relied on an advisory opinion\n            previously issued by the commission, in which it interpreted the statutes\n            (§§ 9-601b and 9-607 (g)) defining the term ‘‘expenditure’’ and governing\n            the permissibility of campaign expenditures, as well as the state regula-\n            tions (§§ 9-706-1 and 9-706-2) implementing the program, and concluded\n            that, in the absence of a statutory exception to the definition of ‘‘expendi-\n            ture,’’ funds in a candidate committee’s account may not be used to\n            make a communication that is not directly related to the candidate’s\n            own electoral race and that also promotes the defeat of or attacks a\n            candidate who is not a direct opponent of the candidate sponsoring the\n            communication but who is running in a different race. After a hearing,\n            the commission found that the plaintiffs had violated the applicable\n            statutes and regulations by using their candidate committee funds to\n            pay for communications that criticized D in the course of promoting\n            their opposition to D’s policies. On appeal to the trial court, the plaintiffs\n            claimed that the statutes and regulations imposing expenditure limita-\n            tions as a condition of receiving public funding violated their rights\n            under the first amendment to the United States constitution by restricting\n            their ability to speak about other, nonopposing candidates. The trial\n            court agreed with the commission’s conclusion that the plaintiffs had\n\x0c0, 0                         CONNECTICUT LAW JOURNAL                                       Page 1\n\n\n\n\n       0 Conn. 1                             ,0                                       3\n                  Markley v. State Elections Enforcement Commission\n           violated the applicable statutes and regulations, insofar as the communi-\n           cations constituted the functional equivalent of express advocacy for\n           the defeat of D in his reelection bid, and the trial court further concluded\n           that the program constituted a valid, alternative route by which the\n           plaintiffs voluntarily had elected to exercise their first amendment rights\n           and that the program’s conditions did not abridge those rights. Accord-\n           ingly, the trial court rendered judgment upholding the commission’s\n           decision, from which the plaintiffs appealed. On appeal, the plaintiffs\n           claimed, inter alia, that the commission’s enforcement of the applicable\n           statutes and regulations to preclude publicly funded candidates from\n           using their candidate committee funds to pay for campaign communica-\n           tions, which, as a rhetorical device, invoke the name of a candidate in\n           a different electoral race to refer more broadly to the policies or political\n           party associated with that candidate, violated their first amendment\n           rights.\n\n       Held that the commission’s enforcement of the applicable statutes and\n          regulations in accordance with its advisory opinion imposed an unconsti-\n          tutional condition in violation of the first amendment to the extent that\n          it penalized the plaintiffs for mentioning D’s name in a manner that was\n          not the functional equivalent of speech squarely directed at D’s reelection\n          campaign, and, accordingly, this court reversed the trial court’s judgment\n          and remanded the case with direction to sustain the plaintiffs’ adminis-\n          trative appeal:\n\n          Following an examination of the United States Supreme Court’s decisions\n          considering the constitutionality of various campaign finance reform\n          laws under the first amendment and a discussion of the unconstitutional\n          conditions doctrine, pursuant to which the government may not deny a\n          benefit to a person on a basis that infringes his or her constitutionally\n          protected freedom of speech, even if that person is not otherwise entitled\n          to such a benefit, this court observed that, although laws that burden\n          political speech, including expenditure limitations, ordinarily are subject\n          to strict scrutiny, candidates who voluntarily accept public campaign\n          funding also accept reasonable terms and conditions attendant to such\n          programs that otherwise may abridge their free speech rights.\n\n          Nevertheless, the fact that a candidate voluntarily participates in a gov-\n          ernment program is not dispositive of the first amendment issue, when, as\n          in the present case, the program restrictions at issue are not generalized\n          expenditure limits but, rather, directly govern the specific content of\n          a publicly financed candidate’s communications, and, because public\n          campaign financing laws that restrict political expression operate to\n          burden a candidate’s core first amendment speech, the court must look\n          beyond voluntariness and apply strict scrutiny to determine whether the\n          restrictions are narrowly tailored to achieve the traditional goals of public\n          campaign financing, namely, promoting participation in the campaign\n          financing program, reducing fundraising burdens and the corrupting\n\x0cPage 2                          CONNECTICUT LAW JOURNAL                                       0, 0\n\n\n\n\n         4                                      ,0                          0 Conn. 1\n                     Markley v. State Elections Enforcement Commission\n             effects of contributions and the pursuit of contributions on government\n             decision making, facilitating candidate communications with the elector-\n             ate, and protecting the fiscal integrity of the program.\n\n             Prohibiting publicly funded candidates from engaging in campaign\n             speech concerning other electoral races survives strict scrutiny if it is\n             narrowly tailored to protect the public fisc by enforcing the limitations\n             of the program, and limitations on campaign speech that refer to a\n             candidate in another race are narrowly tailored to achieve that compel-\n             ling state interest only when the speech at issue is unquestionably the\n             functional equivalent of express advocacy or campaign speech concern-\n             ing the candidate involved in the other race, rather than a rhetorical\n             device intended to communicate where the speaker stands on the issues.\n\n             Moreover, this court recognized that candidates must be able to commu-\n             nicate where they stand on issues in relation to other candidates and\n             public officials, and invoking prominent political figures by name will\n             sometimes provide the most meaningful and effective way for a candidate\n             to explain to voters their political ideals, policy commitments, and the\n             values they hope to bring to the office they seek, even if some of those\n             political figures may happen to be candidates elsewhere on the ballot\n             in a particular election, and the rhetorical value of being able to categorize\n             oneself in relation to other political candidates is especially great in\n             state legislative races.\n\n             Nonetheless, the commission could apply the standard articulated in its\n             advisory opinion to preclude publicly funded candidates from using\n             committee funds to promote the defeat of or to attack a candidate who\n             is not a direct opponent of the candidate sponsoring the communication\n             but who is engaged in a different electoral race, as that standard was\n             not, on its face, an unconstitutional condition in violation of the first\n             amendment, to the extent that it ensured that public funds are spent\n             only on qualifying campaigns without exceeding the amount of the grant\n             allotted per race, but, if that standard is applied in a way that muzzles\n             a publicly funded candidate’s political speech beyond that necessary to\n             prevent the funding of campaign speech with respect to a clearly identi-\n             fied candidate running in a different electoral race, it is a content based\n             restriction that is an unconstitutional condition in violation of the\n             first amendment.\n\n             In determining whether campaign communications by a publicly funded\n             candidate who uses the name of a candidate engaged in a different\n             electoral race as a rhetorical device to refer to a set of policies opposed\n             or supported by the publicly funded candidate constitutes impermissible\n             electoral communications, rather than a constitutionally protected mes-\n             sage in direct furtherance of the publicly funded candidate’s own cam-\n             paign for office, this court relied on the opinion announcing the judgment\n             of the United States Supreme Court in Federal Election Commission v.\n\x0c0, 0                        CONNECTICUT LAW JOURNAL                                      Page 3\n\n\n\n\n       0 Conn. 1                           ,0                                       5\n                Markley v. State Elections Enforcement Commission\n         Wisconsin Right to Life, Inc. (551 U.S. 449), which held that a court\n         should find that a campaign communication is the functional equivalent\n         of express advocacy of election or defeat of a candidate, rather than\n         permissible discussion of issues and candidates who are intimately tied\n         to public issues, only if the communication is susceptible of no reasonable\n         interpretation other than as an appeal to vote for or against a specific can-\n         didate.\n\n         Furthermore, the functional equivalent of express advocacy standard is\n         objective and focuses on the substance of the communication rather\n         than on its effect or considerations of the speaker’s intent to affect the\n         election, and, although the distinction between permissible discussion\n         of issues and candidates, on the one hand, and prohibited advocacy of\n         election or defeat of candidates, on the other, may often dissolve in\n         practical application, the functional equivalency standard gives the bene-\n         fit of the doubt to protecting rather than stifling speech, such that, when\n         the first amendment is implicated, the tie goes to the speaker rather\n         than the censor.\n\n         With respect to the communications and advertisements at issue, this\n         court concluded that they were not the functional equivalent of express\n         advocacy with respect to D’s reelection, insofar as they could not reason-\n         ably be construed as anything more than a rhetorical device intended\n         to communicate the merits of the plaintiffs’ candidacies as bulwarks\n         against the policies endorsed by D and his Democratic allies.\n\n         Three of the communications at issue revealed nothing that rendered\n         them the functional equivalent of express advocacy with respect to D’s\n         reelection, as they lacked any express references thereto, did not suggest\n         that a vote for C would be tantamount to a vote for D or Democratic\n         Party policies, and did not indicate in any way that D was running for\n         reelection in 2014 or that support for the plaintiffs would be integral to\n         defeating the candidacy of D or any other Democrat seeking office,\n         and, instead, those communications highlighted the plaintiffs’ role as a\n         legislative check and balance against policies endorsed by D and his\n         Democratic allies, such that the communications did not convey a differ-\n         ent meaning in 2014, when D was running for reelection as an incumbent,\n         than they would have conveyed during the 2012 or 2016 midterm election\n         cycles, when D was simply serving as the governor.\n\n         Although the remaining two communications presented a closer question,\n         insofar as they either used words somewhat evocative of an ongoing\n         negative campaign against D, such as promoting a new direction and\n         imploring voters to ‘‘change course’’ and stop D’s agenda, or expressly\n         referred to D’s campaign for governor, this court could not concluded\n         that those communications were the functional equivalent of express\n         advocacy with respect to D’s reelection because they reasonably might\n         be understood as urging electoral resistance to the leadership and initia-\n\x0cPage 4                         CONNECTICUT LAW JOURNAL                                      0, 0\n\n\n\n\n         6                                     ,0                         0 Conn. 1\n                    Markley v. State Elections Enforcement Commission\n             tives of D and his Democratic allies, and, to the extent that the references\n             to ‘‘change’’ and a ‘‘campaign’’ could be understood to be the functional\n             equivalent of express advocacy, the tie went to the speakers, that is,\n             the plaintiffs.\n                Argued September 13, 2023—officially released May 21, 2024\n\n                                      Procedural History\n\n            Appeal from a decision of the defendant finding the\n         plaintiffs in violation of state election laws and regula-\n         tions, brought to the Superior Court in the judicial dis-\n         trict of New Britain, where the court, Joseph M. Shortall,\n         judge trial referee, granted the defendant’s motion to\n         dismiss and, exercising the powers of the Superior\n         Court, rendered judgment dismissing the action, from\n         which the plaintiffs appealed; thereafter, this court\n         reversed the trial court’s judgment and remanded the\n         case for further proceedings; subsequently, the case\n         was and tried to the court, Hon. Joseph M. Shortall,\n         judge trial referee, who, exercising the powers of the\n         Superior Court, rendered judgment affirming the deci-\n         sion of the defendant, from which the plaintiffs appealed.\n         Reversed; judgment directed.\n           Charles Miller, pro hac vice, with whom were Mario\n         Cerame and, on the brief, Adam J. Tragone, pro hac\n         vice, for the appellants (plaintiffs).\n            Maura Murphy Osborne, deputy associate attorney\n         general, with whom, on the brief, was William Tong,\n         attorney general, for the appellee (defendant).\n                                            Opinion\n\n            ROBINSON, C. J. This appeal presents an issue of\n         first impression under the first amendment to the United\n         States constitution, namely, the extent to which the stat-\n         utes and regulations governing the public funding of\n         state elections in connection with the Citizens’ Election\n         Program (program), General Statutes § 9-700 et seq.,\n         may be applied to preclude publicly funded candidates\n\x0c0, 0                         CONNECTICUT LAW JOURNAL                                     Page 5\n\n\n\n\n       0 Conn. 1                            ,0                                      7\n                  Markley v. State Elections Enforcement Commission\n\n       from using their candidate committee funds to pay for\n       campaign advertisements that, as a rhetorical device,\n       invoke the name of a candidate in a different race to refer\n       more broadly to the policies or political party associated\n       with that candidate. The defendant, the State Elections\n       Enforcement Commission (commission), imposed fines\n       on the plaintiffs, Joe Markley and Rob Sampson, who\n       were publicly funded candidates for state legislative\n       office during the 2014 general election cycle, on the\n       ground that they had violated the statutes and regula-\n       tions governing the program when they utilized their\n       candidate committee funds to pay for communications\n       that criticized then Governor Dannel Malloy, who was\n       seeking reelection to that office in that same election\n       cycle, in the course of promoting their opposition to\n       his policies. The plaintiffs now appeal1 from the judg-\n       ment of the trial court upholding the decision of the\n       commission, claiming that the commission’s enforce-\n       ment of the state election laws in that manner violated\n       their first amendment rights. Although a compelling\n       governmental interest is served by a condition that pre-\n       cludes publicly funded candidates from using program\n       funds to support or oppose candidates in other races,\n       we conclude that the commission violated the plaintiffs’\n       first amendment rights with respect to the five adver-\n       tisements at issue in this case because they could rea-\n       sonably be understood to be something other than an\n       appeal to vote against Governor Malloy. Accordingly,\n       we reverse the judgment of the trial court.\n         The record reveals the following undisputed facts\n       and procedural history. During the 2014 general election\n       cycle, Markley was an unopposed candidate for state\n       senator from the Sixteenth Senatorial District and regis-\n       tered the candidate committee ‘‘Joe Markley for State\n          1\n            The plaintiffs appealed from the judgment of the trial court to the Appel-\n       late Court, and we transferred the appeal to this court pursuant to General\n       Statutes § 51-199 (c) and Practice Book § 65-1.\n\x0cPage 6                    CONNECTICUT LAW JOURNAL                          0, 0\n\n\n\n\n         8                             ,0                      0 Conn. 1\n                 Markley v. State Elections Enforcement Commission\n\n         Senate 2014.’’ Sampson, who was an incumbent state\n         representative from the Eightieth General Assembly\n         District, was seeking reelection to that office during the\n         2014 general election cycle and registered the candidate\n         committee ‘‘Sampson for CT.’’ Sampson’s opponent in\n         that race was John ‘‘Corky’’ Mazurek, who is the com-\n         plainant before the commission in this case. Each of\n         the plaintiffs’ campaign committees applied for and\n         received public funding grants from the program, Mar-\n         kley in the amount of $56,814, and Sampson in the\n         amount of $27,850.\n            During the 2014 general election cycle, the plaintiffs\n         published five communications or advertisements that\n         are at issue in this appeal. The first communication,\n         exhibit 2 before the commission, was a large, double-\n         sided postcard, jointly paid for by the plaintiffs’ respec-\n         tive committees, the back side of which stated that\n         the plaintiffs ‘‘are who we need to turn Connecticut\n         around!’’ In addition to touting the plaintiffs’ work as\n         state legislators on behalf of Southington’s schools,\n         seniors, and veterans, and their opposition to criminal\n         justice reforms and the New Britain""",
                {
                    "OpinionCluster": {
                        "date_filed": date(2024, 5, 21),
                        "date_filed_is_approximate": False,
                        "judges": "Robinson; McDonald; Mullins; Ecker; Alexander",
                        "syllabus": "The plaintiffs, M and S, candidates for state legislative offices in the 2014 general election, appealed to the trial court from the decision of the defendant, the State Elections Enforcement Commission, which assessed fines against the plaintiffs upon determining that they had violated certain state statutes and regulations governing campaign financing and the Citizens' Election Program (program) (§ 9-700 et seq.). The plaintiffs' respective campaign committees had each applied for and received public funding grants through the program. During the 2014 election cycle, the plaintiffs' campaign committees published certain communications and advertisements that made various references to the record and policies of D, then the governor, who was running for reelection at that time. The communications both touted the plaintiffs' respective accomplishments and positions and referred to their opposi- tion to the agenda advanced by D and D's Democratic allies, including tax hikes and increased spending. One of the communications high- lighted votes taken by S's opponent in the 2014 election, C, when C was serving as a state representative. C filed a complaint with the commission, alleging that the communications were impermissible cam- paign expenditures under the program. C relied on an advisory opinion previously issued by the commission, in which it interpreted the statutes (§§ 9-601b and 9-607 (g)) defining the term ''expenditure'' and governing the permissibility of campaign expenditures, as well as the state regula- tions (§§ 9-706-1 and 9-706-2) implementing the program, and concluded that, in the absence of a statutory exception to the definition of ''expendi- ture,'' funds in a candidate committee's account may not be used to make a communication that is not directly related to the candidate's own electoral race and that also promotes the defeat of or attacks a candidate who is not a direct opponent of the candidate sponsoring the communication but who is running in a different race. After a hearing, the commission found that the plaintiffs had violated the applicable statutes and regulations by using their candidate committee funds to pay for communications that criticized D in the course of promoting their opposition to D's policies. On appeal to the trial court, the plaintiffs claimed that the statutes and regulations imposing expenditure limita- tions as a condition of receiving public funding violated their rights under the first amendment to the United States constitution by restricting their ability to speak about other, nonopposing candidates. The trial court agreed with the commission's conclusion that the plaintiffs had violated the applicable statutes and regulations, insofar as the communi- cations constituted the functional equivalent of express advocacy for the defeat of D in his reelection bid, and the trial court further concluded that the program constituted a valid, alternative route by which the plaintiffs voluntarily had elected to exercise their first amendment rights and that the program's conditions did not abridge those rights. Accord- ingly, the trial court rendered judgment upholding the commission's decision, from which the plaintiffs appealed. On appeal, the plaintiffs claimed, inter alia, that the commission's enforcement of the applicable statutes and regulations to preclude publicly funded candidates from using their candidate committee funds to pay for campaign communica- tions, which, as a rhetorical device, invoke the name of a candidate in a different electoral race to refer more broadly to the policies or political party associated with that candidate, violated their first amendment rights. Held that the commission's enforcement of the applicable statutes and regulations in accordance with its advisory opinion imposed an unconsti- tutional condition in violation of the first amendment to the extent that it penalized the plaintiffs for mentioning D's name in a manner that was not the functional equivalent of speech squarely directed at D's reelection campaign, and, accordingly, this court reversed the trial court's judgment and remanded the case with direction to sustain the plaintiffs' adminis- trative appeal: Following an examination of the United States Supreme Court's decisions considering the constitutionality of various campaign finance reform laws under the first amendment and a discussion of the unconstitutional conditions doctrine, pursuant to which the government may not deny a benefit to a person on a basis that infringes his or her constitutionally protected freedom of speech, even if that person is not otherwise entitled to such a benefit, this court observed that, although laws that burden political speech, including expenditure limitations, ordinarily are subject to strict scrutiny, candidates who voluntarily accept public campaign funding also accept reasonable terms and conditions attendant to such programs that otherwise may abridge their free speech rights. Nevertheless, the fact that a candidate voluntarily participates in a gov- ernment program is not dispositive of the first amendment issue, when, as in the present case, the program restrictions at issue are not generalized expenditure limits but, rather, directly govern the specific content of a publicly financed candidate's communications, and, because public campaign financing laws that restrict political expression operate to burden a candidate's core first amendment speech, the court must look beyond voluntariness and apply strict scrutiny to determine whether the restrictions are narrowly tailored to achieve the traditional goals of public campaign financing, namely, promoting participation in the campaign financing program, reducing fundraising burdens and the corrupting effects of contributions and the pursuit of contributions on government decision making, facilitating candidate communications with the elector- ate, and protecting the fiscal integrity of the program. Prohibiting publicly funded candidates from engaging in campaign speech concerning other electoral races survives strict scrutiny if it is narrowly tailored to protect the public fisc by enforcing the limitations of the program, and limitations on campaign speech that refer to a candidate in another race are narrowly tailored to achieve that compel- ling state interest only when the speech at issue is unquestionably the functional equivalent of express advocacy or campaign speech concern- ing the candidate involved in the other race, rather than a rhetorical device intended to communicate where the speaker stands on the issues. Moreover, this court recognized that candidates must be able to commu- nicate where they stand on issues in relation to other candidates and public officials, and invoking prominent political figures by name will sometimes provide the most meaningful and effective way for a candidate to explain to voters their political ideals, policy commitments, and the values they hope to bring to the office they seek, even if some of those political figures may happen to be candidates elsewhere on the ballot in a particular election, and the rhetorical value of being able to categorize oneself in relation to other political candidates is especially great in state legislative races. Nonetheless, the commission could apply the standard articulated in its advisory opinion to preclude publicly funded candidates from using committee funds to promote the defeat of or to attack a candidate who is not a direct opponent of the candidate sponsoring the communication but who is engaged in a different electoral race, as that standard was not, on its face, an unconstitutional condition in violation of the first amendment, to the extent that it ensured that public funds are spent only on qualifying campaigns without exceeding the amount of the grant allotted per race, but, if that standard is applied in a way that muzzles a publicly funded candidate's political speech beyond that necessary to prevent the funding of campaign speech with respect to a clearly identi- fied candidate running in a different electoral race, it is a content based restriction that is an unconstitutional condition in violation of the first amendment. In determining whether campaign communications by a publicly funded candidate who uses the name of a candidate engaged in a different electoral race as a rhetorical device to refer to a set of policies opposed or supported by the publicly funded candidate constitutes impermissible electoral communications, rather than a constitutionally protected mes- sage in direct furtherance of the publicly funded candidate's own cam- paign for office, this court relied on the opinion announcing the judgment of the United States Supreme Court in Federal Election Commission v. Wisconsin Right to Life, Inc. (551 U.S. 449), which held that a court should find that a campaign communication is the functional equivalent of express advocacy of election or defeat of a candidate, rather than permissible discussion of issues and candidates who are intimately tied to public issues, only if the communication is susceptible of no reasonable interpretation other than as an appeal to vote for or against a specific can- didate. Furthermore, the functional equivalent of express advocacy standard is objective and focuses on the substance of the communication rather than on its effect or considerations of the speaker's intent to affect the election, and, although the distinction between permissible discussion of issues and candidates, on the one hand, and prohibited advocacy of election or defeat of candidates, on the other, may often dissolve in practical application, the functional equivalency standard gives the bene- fit of the doubt to protecting rather than stifling speech, such that, when the first amendment is implicated, the tie goes to the speaker rather than the censor. With respect to the communications and advertisements at issue, this court concluded that they were not the functional equivalent of express advocacy with respect to D's reelection, insofar as they could not reason- ably be construed as anything more than a rhetorical device intended to communicate the merits of the plaintiffs' candidacies as bulwarks against the policies endorsed by D and his Democratic allies. Three of the communications at issue revealed nothing that rendered them the functional equivalent of express advocacy with respect to D's reelection, as they lacked any express references thereto, did not suggest that a vote for C would be tantamount to a vote for D or Democratic Party policies, and did not indicate in any way that D was running for reelection in 2014 or that support for the plaintiffs would be integral to defeating the candidacy of D or any other Democrat seeking office, and, instead, those communications highlighted the plaintiffs' role as a legislative check and balance against policies endorsed by D and his Democratic allies, such that the communications did not convey a differ- ent meaning in 2014, when D was running for reelection as an incumbent, than they would have conveyed during the 2012 or 2016 midterm election cycles, when D was simply serving as the governor. Although the remaining two communications presented a closer question, insofar as they either used words somewhat evocative of an ongoing negative campaign against D, such as promoting a new direction and imploring voters to ''change course'' and stop D's agenda, or expressly referred to D's campaign for governor, this court could not concluded that those communications were the functional equivalent of express advocacy with respect to D's reelection because they reasonably might be understood as urging electoral resistance to the leadership and initia- tives of D and his Democratic allies, and, to the extent that the references to ''change'' and a ''campaign'' could be understood to be the functional equivalent of express advocacy, the tie went to the speakers, that is, the plaintiffs. Argued September 13, 2023—officially released May 21, 2024",
                        "procedural_history": "Appeal from a decision of the defendant finding the plaintiffs in violation of state election laws and regula- tions, brought to the Superior Court in the judicial dis- trict of New Britain, where the court, Joseph M. Shortall, judge trial referee, granted the defendant's motion to dismiss and, exercising the powers of the Superior Court, rendered judgment dismissing the action, from which the plaintiffs appealed; thereafter, this court reversed the trial court's judgment and remanded the case for further proceedings; subsequently, the case was and tried to the court, Hon. Joseph M. Shortall, judge trial referee, who, exercising the powers of the Superior Court, rendered judgment affirming the deci- sion of the defendant, from which the plaintiffs appealed. Reversed; judgment directed. Charles Miller, pro hac vice, with whom were Mario Cerame and, on the brief, Adam J. Tragone, pro hac vice, for the appellants (plaintiffs). Maura Murphy Osborne, deputy associate attorney general, with whom, on the brief, was William Tong, attorney general, for the appellee (defendant).",
                    }
                },
            ),
            # Example of secondary opinion where nothing can be extracted
            # https://www.courtlistener.com/opinion/9499073/northland-investment-corp-v-public-utilities-regulatory-authority/
            (
                """fPage 0                        CONNECTICUT LAW JOURNAL                                   0, 0\n\n\n\n\n         2                                   ,0                        0 Conn. 0\n             Northland Investment Corp. v. Public Utilities Regulatory Authority\n\n\n            ECKER, J., with whom ROBINSON, C. J., and MUL-\n         LINS, J., join, dissenting. As a matter of good govern-\n         ment, I have no quarrel with the majority’s conclusion\n         that the result it reaches today advances a legitimate\n         and even praiseworthy public policy. If a residential\n         landlord who pays the utility bill for a multiunit apart-\n         ment bui""",
                {"OpinionCluster": {}},
            ),
            # Example without syllabus
            # https://www.courtlistener.com/opinion/9447934/state-v-gamer
            (
                """The “officially released” date that appears near the be-\nginning of each opinion is the date the opinion will be pub-\nlished in the Connecticut Law Journal or the date it was\nreleased as a slip opinion. The operative date for the be-\nginning of all time periods for filing postopinion motions\nand petitions for certification is the “officially released”\ndate appearing in the opinion.\n\n   All opinions are subject to modification and technical\ncorrection prior to official publication in the Connecticut\nReports and Connecticut Appellate Reports. In the event of\ndiscrepancies between the advance release version of an\nopinion and the latest version appearing in the Connecticut\nLaw Journal and subsequently in the Connecticut Reports\nor Connecticut Appellate Reports, the latest version is to\nbe considered authoritative.\n\n   The syllabus and procedural history accompanying the\nopinion as it appears in the Connecticut Law Journal and\nbound volumes of official reports are copyrighted by the\nSecretary of the State, State of Connecticut, and may not\nbe reproduced and distributed without the express written\npermission of the Commission on Official Legal Publica-\ntions, Judicial Branch, State of Connecticut.\n***********************************************\n\x0c             STATE OF CONNECTICUT v.\n               CHARLES GAMER, JR.\n                    (SC 20771)\n           Robinson, C. J., and D’Auria, Mullins, Ecker,\n               Alexander, Dannehy and Alvord, Js.\n      Argued October 20—officially released December 5, 2023\n\n                       Procedural History\n\n   Information charging the defendant with violation of\nprobation, brought to the Superior Court in the judicial\ndistrict of Stamford-Norwalk, geographical area num-\nber twenty, where the case was tried to the court,\nMcLaughlin, J.; judgment revoking the defendant’s pro-\nbation, from which the defendant appealed to the Appel-\nlate Court, Bright, C. J., and Moll and Pellegrino, Js.,\nwhich affirmed the trial court’s judgment, and the defen-\ndant, on the granting of certification, appealed to this\ncourt. Appeal dismissed.\n  James B. Streeto, senior assistant public defender,\nwith whom, on the brief, was Meaghan Kirby, for the\nappellant (defendant).\n  Laurie N. Feldman, assistant state’s attorney, with\nwhom, on the brief, were Suzanne M. Vieux, supervi-\nsory assistant state’s attorney, and Elizabeth Moran,\nformer assistant state’s attorney, for the appellee (state).\n\x0c                          Opinion\n\n   PER CURIAM. The defendant, Charles Gamer, Jr""",
                {
                    "OpinionCluster": {
                        "date_filed": date(2023, 12, 5),
                        "date_filed_is_approximate": False,
                        "judges": "Robinson; D’Auria; Mullins; Ecker; Alexander; Dannehy; Alvord",
                        "procedural_history": "Information charging the defendant with violation of probation, brought to the Superior Court in the judicial district of Stamford-Norwalk, geographical area num- ber twenty, where the case was tried to the court, McLaughlin, J.; judgment revoking the defendant's pro- bation, from which the defendant appealed to the Appel- late Court, Bright, C. J., and Moll and Pellegrino, Js., which affirmed the trial court's judgment, and the defen- dant, on the granting of certification, appealed to this court. Appeal dismissed. James B. Streeto, senior assistant public defender, with whom, on the brief, was Meaghan Kirby, for the appellant (defendant). Laurie N. Feldman, assistant state's attorney, with whom, on the brief, were Suzanne M. Vieux, supervi- sory assistant state's attorney, and Elizabeth Moran, former assistant state's attorney, for the appellee (state).",
                    }
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.connappct": [
            (
                # https://www.courtlistener.com/opinion/9501662/coney-v-commissioner-of-correction/?q=court_id%3Aconnappct&type=o&order_by=dateFiled%20desc&stat_Published=on
                """Connecticut Law Jour-\nnal and subsequently in the Connecticut Reports or\nConnecticut Appellate Reports are copyrighted by the\nSecretary of the State, State of Connecticut, and may\nnot be reproduced or distributed without the express\nwritten permission of the Commission on Official Legal\nPublications, Judicial Branch, State of Connecticut.\n************************************************\n\x0cPage 0                        CONNECTICUT LAW JOURNAL                                    0, 0\n\n\n\n\n         2                         ,0                           0 Conn. App. 1\n                           Coney v. Commissioner of Correction\n\n\n         PAUL CONEY v. COMMISSIONER OF CORRECTION\n                         (AC 41747)\n                               Alvord, Cradle and Suarez, Js.\n\n                                           Syllabus\n\n         The petitioner, who had been convicted, following a jury trial, of the crimes\n            of murder and criminal possession of a pistol or revolver, filed a fourth\n            petition for a writ of habeas corpus. The habeas court, upon the request\n            of the respondent, the Commissioner of Correction, issued an order to\n            show cause why the petition should not be dismissed as untimely given\n            that it had been filed beyond the time limit for successive petitions set\n            forth in the applicable statute (§ 52-470 (d)). The court held an eviden-\n            tiary hearing, during which the petitioner testified that he had filed a\n            timely third habeas petition but withdrew it prior to trial on the advice\n            of his prior habeas counsel. The petitioner further testified that counsel\n            did not discuss § 52-470 (d) and that, if the petitioner had known that\n            withdrawing his third petition and refiling would result in an untimely\n            petition, he would not have done so. The habeas court dismissed the\n            fourth habeas petition as untimely, concluding that the petitioner had\n            failed to demonstrate good cause for the delay in filing the petition.\n            Thereafter, the petitioner, on the granting of certification, appealed to\n            this court, which affirmed the judgment of the habeas court. The peti-\n            tioner, on the granting of certification, appealed to the Supreme Court,\n            which granted the petition for certification, vacated the judgment of\n            this court, and remanded the case to this court for further consideration\n            in light of Rose v. Commissioner of Correction (348 Conn. 333). Held\n            that, after further consideration of the issue raised in this appeal, the\n            proper remedy was to remand the matter to the habeas court for a\n            new hearing and good cause determination under § 52-470 (d) and (e),\n            consistent with the principles set forth in Rose, Rapp v. Commissioner\n            of Correction (224 Conn. App. 336), and Hankerson v. Commissioner\n            of Correction (223 Conn. App. 562).\n                      Argued April 8—officially released May 14, 2024\n\n                                     Procedural History\n\n            Petition for a writ of habeas corpus, brought to the\n         Superior Court in the judicial district of Tolland, where\n         the court, Sferrazza, J., rendered judgment dismissing\n         the petition; thereafter, the petitioner, on the granting\n         of certification, appealed to this court, Alvord, Elgo and\n         Albis, Js., which affirmed the judgment of the habeas\n         court; subsequently, on the granting of certification,\n\x0c0, 0                    CONNECTICUT LAW JOURNAL                    Page 1\n\n\n\n\n       0 Conn. App. 1                       ,0                3\n                    Coney v. Commissioner of Correction\n\n       the petitioner appealed to the Supreme Court, which\n       granted the petition to appeal, vacated the judgment of\n       this court and remanded the case to this court for fur-\n       ther proceedings. Reversed; further proceedings.\n         Judie Marshall, assigned counsel, for the appellant\n       (petitioner).\n         Linda F. Rubertone, senior assistant state’s attorney,\n       for the appellee (respondent).\n                                 Opinion\n\n         SUAREZ, J. This appeal returns to this court on\n       remand from our Supreme Court with direction to fur-\n       ther consider the claim raised by the petitioner, Paul\n       Coney, that the habeas court erred in dismissing his\n       petition for a writ of habeas corpus as untimely pursu-\n       ant to General Statutes § 52-470 (d) and (e) because\n       he failed to demonstrate good cause to overcome the\n       statutory presumption of an unreasonable delay. See\n       Coney v. Commissioner of Correction, 348 Conn. 946,\n       308 A.3d 35 (2024). We reverse the judgment of the\n       habeas court and remand the matter for a new hearing\n       and good cause determinat""",
                {
                    "OpinionCluster": {
                        "date_filed": date(2024, 5, 14),
                        "date_filed_is_approximate": False,
                        "procedural_history": "Petition for a writ of habeas corpus, brought to the Superior Court in the judicial district of Tolland, where the court, Sferrazza, J., rendered judgment dismissing the petition; thereafter, the petitioner, on the granting of certification, appealed to this court, Alvord, Elgo and Albis, Js., which affirmed the judgment of the habeas court; subsequently, on the granting of certification, the petitioner appealed to the Supreme Court, which granted the petition to appeal, vacated the judgment of this court and remanded the case to this court for fur- ther proceedings. Reversed; further proceedings. Judie Marshall, assigned counsel, for the appellant (petitioner). Linda F. Rubertone, senior assistant state's attorney, for the appellee (respondent).",
                        "syllabus": "The petitioner, who had been convicted, following a jury trial, of the crimes of murder and criminal possession of a pistol or revolver, filed a fourth petition for a writ of habeas corpus. The habeas court, upon the request of the respondent, the Commissioner of Correction, issued an order to show cause why the petition should not be dismissed as untimely given that it had been filed beyond the time limit for successive petitions set forth in the applicable statute (§ 52-470 (d)). The court held an eviden- tiary hearing, during which the petitioner testified that he had filed a timely third habeas petition but withdrew it prior to trial on the advice of his prior habeas counsel. The petitioner further testified that counsel did not discuss § 52-470 (d) and that, if the petitioner had known that withdrawing his third petition and refiling would result in an untimely petition, he would not have done so. The habeas court dismissed the fourth habeas petition as untimely, concluding that the petitioner had failed to demonstrate good cause for the delay in filing the petition. Thereafter, the petitioner, on the granting of certification, appealed to this court, which affirmed the judgment of the habeas court. The peti- tioner, on the granting of certification, appealed to the Supreme Court, which granted the petition for certification, vacated the judgment of this court, and remanded the case to this court for further consideration in light of Rose v. Commissioner of Correction (348 Conn. 333). Held that, after further consideration of the issue raised in this appeal, the proper remedy was to remand the matter to the habeas court for a new hearing and good cause determination under § 52-470 (d) and (e), consistent with the principles set forth in Rose, Rapp v. Commissioner of Correction (224 Conn. App. 336), and Hankerson v. Commissioner of Correction (223 Conn. App. 562). Argued April 8—officially released May 14, 2024",
                        "judges": "Alvord; Cradle; Suarez",
                    }
                },
            ),
            (
                # 2 docket numbers
                # https://www.courtlistener.com/opinion/9497599/lepkowski-v-planning-commission/?q=court_id%3Aconnappct&type=o&order_by=dateFiled+desc&stat_Published=on&page=2
                """Connecticut Law Jour-\nnal and subsequently in the Connecticut Reports or\nConnecticut Appellate Reports are copyrighted by the\nSecretary of the State, State of Connecticut, and may\nnot be reproduced or distributed without the express\nwritten permission of the Commission on Official Legal\nPublications, Judicial Branch, State of Connecticut.\n************************************************\n\x0cPage 0                         CONNECTICUT LAW JOURNAL                                     0, 0\n\n\n\n\n         2                          ,0                            0 Conn. App. 1\n                             Lepkowski v. Planning Commission\n\n\n         BRIAN LEPKOWSKI v. PLANNING COMMISSION OF\n                THE TOWN OF EAST LYME ET AL.\n                         (AC 46146)\n                         (AC 46159)\n                          Bright, C. J., and Moll and Westbrook, Js.\n\n                                           Syllabus\n\n         Pursuant to a provision of the East Lyme Subdivision Regulations (§ 4-14-\n            3), ‘‘[s]ubdivisions of 20 lots or more where more than 50% of the\n            parcel(s) to be subdivided consist of environmentally sensitive resources\n            such as wetlands, steep slopes (>25%), watercourses, flood hazard areas\n            or ridge lines, shall be subject to an [Environmental Review Team]\n            evaluation . . . .’’\n         The plaintiff appealed to the Superior Court from a decision of the defendant\n            Planning Commission of the Town of East Lyme, approving the defen-\n            dant R Co.’s resubdivision application. The plaintiff, an abutting land-\n            owner, opposed the application, claiming, inter alia, that, pursuant to\n            § 4-14-3 of the subdivision regulations, the defendants were required to\n            obtain an evaluation to assess the natural resources on the property\n            before the application was approved. The defendants were unable to\n            obtain such an evaluation prior to the approval of the application\n            because, when the commission contacted E Co., the entity that per-\n            formed the evaluations, E Co. informed the commission that it was\n            forgoing such evaluations until it had time to develop a new protocol\n            for the reviews. E Co. did not specify a date on which it would resume\n            conducting the evaluations. In light of this, the commission determined\n            that it was impossible for R Co. to comply with § 4-14-3, and it approved\n            the application. The Superior Court sustained the plaintiff’s appeal only\n            with respect to his claim regarding R Co.’s failure to obtain an evaluation.\n            The court determined that § 4-14-3 applied to the application, that the\n            evaluation was a mandatory requirement pursuant to § 4-14-3, that the\n            subdivision regulations did not expressly convey to the commission the\n            authority to waive the requirement, and that, therefore, the commission\n            illegally waived § 4-14-3. On the granting of certification, the defendants\n            filed separate appeals to this court. Held that the Superior Court improp-\n            erly sustained the plaintiff’s appeal with respect to his claim premised\n            on § 4-14-3 of the subdivision regulations: the commission complied\n            with § 4-14-3 of the subdivision regulations, which required it to request\n            an evaluation in connection with R Co.’s application and to give E Co.\n            a reasonable opportunity to perform the evaluation but did not mandate\n            that the evaluation had to be completed, as, in contrast to other provi-\n            sions in § 4-14 of the East Lyme Subdivision Regulations, § 4-14-3 does\n            not indicate that a report with respect to an evaluation must be submitted\n            to the commission, nor does it restrict the commission’s ability to act\n\x0c0, 0                       CONNECTICUT LAW JOURNAL                                    Page 1\n\n\n\n\n       0 Conn. App. 1                               ,0                           3\n                         Lepkowski v. Planning Commission\n          on the application if an evaluation is not performed or assign the weight\n          that the commission must afford to such a report; moreover, the interpre-\n          tation that the evaluation was not mandatory aligned with the broader\n          dictionary definitions of the phrase ‘‘subject to’’ as used in § 4-14-3;\n          furthermore, as a municipal legislative enactment, § 4-14-3 was entitled\n          to a presumption of validity and construing the regulation to mandate\n          the completion of an evaluation would have rendered the provision\n          invalid as an impermissible delegation of authority by the commission\n          to E Co.; accordingly, by requesting the evaluation, the commission\n          complied with § 4-14-3 despite that E Co. did not perform the evaluation\n          and indicated that it had no intention of doing so until it established a\n          new protocol for such evaluations at some unspecified future date.\n                Argued January 10—officially released April 30, 2024\n\n                                  Procedural History\n\n          Appeal from the decision of the named defendant\n       approving a resubdivision application filed by the defen-\n       dant Real Estate Service of Conn., Inc., brought to the\n       Superior Court in the judicial district of New London\n       and tried to the court, O’Hanlan, J.; judgment sus-\n       taining in part the plaintiff’s appeal, from which the\n       defendants, on the granting of certification, filed sepa-\n       rate appeals to this court. Reversed in part; judgment\n       directed.\n         Mark S. Zamarka, for the appellant in Docket No.\n       AC 46146 and the appellee in Docket No. AC 46159\n       (named defendant).\n         Matthew Ranelli, with whom was Chelsea C. McCal-\n       lum, for the appellant in Docket No. AC 46159 and the\n       appellee in Docket No. AC 46146 (defendant Real Estate\n       Service of Conn., Inc.).\n          Paul H. D. Stoughton, with whom, on the brief, was\n       John F. Healey, for the appellee in both appeals (plain-\n       tiff).\n                                        Opinion\n\n          MOLL, J. The defendants, the Planning Commission\n       of the Town of East Lyme (commission) and Real Estate\n\x0cPage 2                        CONNECTICUT LAW JOURNAL                                     0, 0\n\n\n\n\n         4                 """,
                {
                    "OpinionCluster": {
                        "date_filed": date(2024, 4, 30),
                        "date_filed_is_approximate": False,
                        "procedural_history": "Appeal from the decision of the named defendant approving a resubdivision application filed by the defen- dant Real Estate Service of Conn., Inc., brought to the Superior Court in the judicial district of New London and tried to the court, O'Hanlan, J.; judgment sus- taining in part the plaintiff's appeal, from which the defendants, on the granting of certification, filed sepa- rate appeals to this court. Reversed in part; judgment directed. Mark S. Zamarka, for the appellant in Docket No. AC 46146 and the appellee in Docket No. AC 46159 (named defendant). Matthew Ranelli, with whom was Chelsea C. McCal- lum, for the appellant in Docket No. AC 46159 and the appellee in Docket No. AC 46146 (defendant Real Estate Service of Conn., Inc.). Paul H. D. Stoughton, with whom, on the brief, was John F. Healey, for the appellee in both appeals (plain- tiff).",
                        "syllabus": "Pursuant to a provision of the East Lyme Subdivision Regulations (§ 4-14- 3), ''[s]ubdivisions of 20 lots or more where more than 50% of the parcel(s) to be subdivided consist of environmentally sensitive resources such as wetlands, steep slopes (>25%), watercourses, flood hazard areas or ridge lines, shall be subject to an [Environmental Review Team] evaluation . . . .'' The plaintiff appealed to the Superior Court from a decision of the defendant Planning Commission of the Town of East Lyme, approving the defen- dant R Co.'s resubdivision application. The plaintiff, an abutting land- owner, opposed the application, claiming, inter alia, that, pursuant to § 4-14-3 of the subdivision regulations, the defendants were required to obtain an evaluation to assess the natural resources on the property before the application was approved. The defendants were unable to obtain such an evaluation prior to the approval of the application because, when the commission contacted E Co., the entity that per- formed the evaluations, E Co. informed the commission that it was forgoing such evaluations until it had time to develop a new protocol for the reviews. E Co. did not specify a date on which it would resume conducting the evaluations. In light of this, the commission determined that it was impossible for R Co. to comply with § 4-14-3, and it approved the application. The Superior Court sustained the plaintiff's appeal only with respect to his claim regarding R Co.'s failure to obtain an evaluation. The court determined that § 4-14-3 applied to the application, that the evaluation was a mandatory requirement pursuant to § 4-14-3, that the subdivision regulations did not expressly convey to the commission the authority to waive the requirement, and that, therefore, the commission illegally waived § 4-14-3. On the granting of certification, the defendants filed separate appeals to this court. Held that the Superior Court improp- erly sustained the plaintiff's appeal with respect to his claim premised on § 4-14-3 of the subdivision regulations: the commission complied with § 4-14-3 of the subdivision regulations, which required it to request an evaluation in connection with R Co.'s application and to give E Co. a reasonable opportunity to perform the evaluation but did not mandate that the evaluation had to be completed, as, in contrast to other provi- sions in § 4-14 of the East Lyme Subdivision Regulations, § 4-14-3 does not indicate that a report with respect to an evaluation must be submitted to the commission, nor does it restrict the commission's ability to act on the application if an evaluation is not performed or assign the weight that the commission must afford to such a report; moreover, the interpre- tation that the evaluation was not mandatory aligned with the broader dictionary definitions of the phrase ''subject to'' as used in § 4-14-3; furthermore, as a municipal legislative enactment, § 4-14-3 was entitled to a presumption of validity and construing the regulation to mandate the completion of an evaluation would have rendered the provision invalid as an impermissible delegation of authority by the commission to E Co.; accordingly, by requesting the evaluation, the commission complied with § 4-14-3 despite that E Co. did not perform the evaluation and indicated that it had no intention of doing so until it established a new protocol for such evaluations at some unspecified future date. Argued January 10—officially released April 30, 2024",
                        "judges": "Bright; Moll; Westbrook",
                    }
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.vt": [
            (
                # https://www.courtlistener.com/api/rest/v3/opinions/10566596/
                """NOTICE: This opinion is subject to motions for reargument under V.R.A.P. 40 as well as formal\nrevision before publication in the Vermont Reports. Readers are requested to notify the Reporter\nof Decisions by email at: JUD.Reporter@vtcourts.gov or by mail at: Vermont Supreme Court, 109\nState Street, Montpelier, Vermont 05609-0801, of any errors in order that corrections may be made\nbefore this opinion goes to press.\n\n\n                                            2024 VT 52\n\n                                          No. 23-AP-226\n\nState of Vermont   """,
                {
                    "Citation": "2024 VT 52",
                    "OpinionCluster": {"precedential_status": "Published"},
                },
            ),
            (
                # https://www.courtlistener.com/api/rest/v4/opinions/10823232/
                """VERMONT SUPREME COURT
                Case No.
                24-AP-136\n109 State Street\nMontpelier VT 05609-0801\n802-828-4774
                \nwww.vermontjudiciary.org\n\n\nNote: In the case title, an asterisk
                (*) indicates an appellant and a double asterisk (**) indicates a
                cross-\nappellant. Decisions of a three-justice panel are not to be considered as precedent before any tribunal.\n\n\n
                ENTRY ORDER\n\n
                in denying his request for a continuance and entering summary judgment for\ndefendants.\n\n       Affirmed.\n\n\n                                              BY THE COURT:\n\n\n\n                                              Harold E. Eaton, Jr., Associate Justice\n\n\n                                              William D. Cohen, Associate Justice\n\n\n                                              Nancy J. Waples, Associate Justice\n\n\n\n\n                                                6\n\f""",
                {
                    "OpinionCluster": {
                        "precedential_status": "Unpublished",
                        "judges": "Harold E. Eaton, Jr.; William D. Cohen; Nancy J. Waples",
                    }
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.vt_criminal": [
            (
                # https://www.courtlistener.com/api/rest/v3/clusters/7854285/
                """NOTICE: This opinion is subject to motions for reargument under V.R.A.P. 40 as well as formal\nrevision before publication in the Vermont Reports. Readers are requested to notify the Reporter\nof Decisions by email at: JUD.Reporter@vermont.gov or by mail at: Vermont Supreme Court, 109\nState Street, Montpelier, Vermont 05609-0801, of any errors in order that corrections may be made\nbefore this opinion goes to press.\n\n\n                                            2022 VT 35\n\n                                           No. 2021-059\n\nState of Vermont                                                 Supreme Court\n\n                                                                 On Appeal from\n   v.                                                            Superior Court, Chittenden Unit,\n                                                                 Criminal Division\n\nRandy F. Therrien    """,
                {
                    "Citation": "2022 VT 35",
                    "OpinionCluster": {"precedential_status": "Published"},
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.vtsuperct_environmental": [
            (
                # https://www.courtlistener.com/opinion/10274910/in-re-windham-windsor-housing-trust-jo-appeal-deborah-lazar-laura/
                """NOTICE: This opinion is subject to motions for reargument under V.R.A.P. 40 as well as formal\nrevision before publication in the Vermont Reports. Readers are requested to notify the Reporter\nof Decisions by email at: JUD.Reporter@vtcourts.gov or by mail at: Vermont Supreme Court,\n109 State Street, Montpelier, Vermont 05609-0801, of any errors in order that corrections may\nbe made before this opinion goes to press.\n\n\n                                        2024 VT 73\n\n                                       No. 24-AP-079\n\nIn re Windham  """,
                {
                    "Citation": "2024 VT 73",
                    "Docket": {"court_id": "vt"},
                    "OpinionCluster": {"precedential_status": "Published"},
                },
            )
        ],
        "juriscraper.opinions.united_states.state.vtsuperct_family": [
            (
                # https://www.courtlistener.com/opinion/4707491/jason-c-barrows-v-jessica-easton/
                """NOTICE: This opinion is subject to motions for reargument under V.R.A.P. 40 as well as formal\nrevision before publication in the Vermont Reports. Readers are requested to notify the Reporter\nof Decisions by email at: JUD.Reporter@vermont.gov or by mail at: Vermont Supreme Court, 109\nState Street, Montpelier, Vermont 05609-0801, of any errors in order that corrections may be made\nbefore this opinion goes to press.\n\n\n                                             2020 VT 2\n\n                                            No. 2019-149\n\nJason C. Barrows      """,
                {
                    "Citation": "2020 VT 2",
                    "OpinionCluster": {"precedential_status": "Published"},
                    "Docket": {"court_id": "vt"},
                },
            )
        ],
        "juriscraper.opinions.united_states.state.vtsuperct_probate": [
            (
                # haven't found a proper example yet
                """""",
                {},
            )
        ],
        "juriscraper.opinions.united_states.state.vtsuperct_civil": [
            (
                # haven't found a proper example yet, let's use a negative example
                # where a neutral citation is within the range of search
                """Guildhall VT 0590\n802-676-3910 .vermontjudiciary.org\n\nLisa Rote v. Town of Concord\n\nDECISION ON MOTION TO DISMISS\nIn this case, plaintiff Lisa Rote\nFactual Background\nThe well-pleaded factual allegations in this case are few. For the purpose of this motion, the court accepts as true the following facts, drawn from the complaint and incorporate documents. See Coutu v. Town of Cavendish, 2011 VT 27,""",
                {},
            )
        ],
        "juriscraper.opinions.united_states.state.ny": [
            (
                # https://www.nycourts.gov/reporter/3dseries/2024/2024_04236.htm
                '<div>\n\nStefanik v Hochul (2024 NY Slip Op 04236)\n\n\n\n<table width="80%" border="1" cellspacing="2" cellpadding="5" align="center">\n<tr>\n<td align="center"><b>Stefanik v Hochul</b></td>\n</tr>\n<tr>\n<td align="center">2024 NY Slip Op 04236</td>\n</tr>\n<tr>\n<td align="center">Decided on August 20, 2024</td>\n</tr>\n<tr>\n<td align="center">Court of Appeals</td>\n</tr>\n<tr>\n<td align="center">Wilson, Ch. J.</td>\n</tr>\n\n<tr>\n<td align="center">Published by New York State Law Reporting Bureau pursuant to Judiciary Law § 431.</td>\n</tr>\n<tr>\n<td align="center">This opinion is uncorrected and subject to revision before publication in the Official Reports.</td>\n</tr>\n</table>\n<br><br>\nDecided on August 20, 2024\n<div align="center"></div>\n<br>No. 86 \n\n<br><br><div align="center"><b>[*1]Elise Stefanik, et al., Appellants,\n<br><br>v<br><br>Kathy Hochul, &amp; c., et al., Respondents.\n</b></div><br><br>\n<br><br>\n<p>Michael Y. Hawrylchak, for appellants.</p>\n<p>Jeffrey W. Lang, for respondents Kathy Hochul et al.</p>\n<p>Nicholas J. Faso, for respondent Peter S. Kosinski.</p>\n<p>Aria C. Branch, for respondents Democratic Congressional Campaign Committee et al.</p>\n<p>Public Interest Legal Foundation, Common Cause New York, Richard Briffault, et al., Center for Election Confidence, Government Justice Center, Inc., amici curiae.</p>\n<br><br>\n\n<br>\n',
                {
                    "Docket": {
                        "docket_number": "No. 86",
                    },
                },
            )
        ],
        "juriscraper.opinions.united_states.state.nyappdiv_1st": [
            (
                # https://www.nycourts.gov/reporter/3dseries/2024/2024_04182.htm
                "Matter of Michael F.\n2024 NY Slip Op 04182\nDecided on August 08, 2024\nAppellate Division, First Department\nPublished by New York State Law Reporting Bureau pursuant to Judiciary Law § 431.\nThis opinion is uncorrected and subject to revision before publication in the Official Reports.\n\n\nDecided and Entered: August 08, 2024\nBefore: Kern, J.P., Oing, Kapnick, Higgitt, Michael, JJ.\n\n<br>Docket No. D-01854/23 Appeal No. 2333 Case No. 2023-05467\n\n[*1]In the Matter of Michael F., A Person Alleged to be a Juvenile Delinquent, Appellant.",
                {
                    "Docket": {
                        "docket_number": "Docket No. D-01854/23 Appeal No. 2333 Case No. 2023-05467",
                    },
                },
            )
        ],
        "juriscraper.opinions.united_states.state.nyappdiv_2nd": [
            (
                # https://www.nycourts.gov/reporter/3dseries/2024/2024_04118.htm
                "\nAWR Group, Inc. v 240 Echo Place Hous. Dev. Fund Corp.\n2024 NY Slip Op 04118\nDecided on August 7, 2024\nAppellate Division, Second Department\nPublished by New York State Law Reporting Bureau pursuant to Judiciary Law § 431.\nThis opinion is uncorrected and subject to revision before publication in the Official Reports.\n\n\nDecided on August 7, 2024 SUPREME COURT OF THE STATE OF NEW YORK Appellate Division, Second Judicial Department\nMARK C. DILLON, J.P.\nCHERYL E. CHAMBERS\nLARA J. GENOVESI\nLOURDES M. VENTURA, JJ.\n\n<br>2023-03266\n<br>(Index No. 705239/20)\n\n[*1]AWR Group, Inc., respondent,\n",
                {
                    "Docket": {
                        "docket_number": "2023-03266; Index No. 705239/20",
                    },
                },
            )
        ],
        "juriscraper.opinions.united_states.state.nyappdiv_3rd": [
            (
                # https://www.nycourts.gov/reporter/3dseries/2024/2024_04173.htm
                "\nMatter of Attorneys in Violation of Judiciary Law § 468-a (Miyazaki)\n2024 NY Slip Op 04173\nDecided on August 8, 2024\nAppellate Division, Third Department\nPublished by New York State Law Reporting Bureau pursuant to Judiciary Law § 431.\nThis opinion is uncorrected and subject to revision before publication in the Official Reports.\n\n\nDecided and Entered:August 8, 2024\n\n<br>PM-154-24\n\n[*1]In the Matter of Att",
                {
                    "Docket": {
                        "docket_number": "PM-154-24",
                    },
                },
            ),
            (
                # https://www.nycourts.gov/reporter/3dseries/2024/2024_04171.htm
                "\nMatter of First United Methodist Church in Flushing v Assessor, Town of Callicoon\n2024 NY Slip Op 04171\nDecided on August 8, 2024\nAppellate Division, Third Department\nPublished by New York State Law Reporting Bureau pursuant to Judiciary Law § 431.\nThis opinion is uncorrected and subject to revision before publication in the Official Reports.\n\n\nDecided and Entered:August 8, 2024\n\n<br>CV-23-1597\n\n",
                {
                    "Docket": {
                        "docket_number": "CV-23-1597",
                    },
                },
            ),
        ],
        "juriscraper.opinions.united_states.federal_special.uscfc_vaccine": [
            (
                # https://ecf.cofc.uscourts.gov/cgi-bin/show_public_doc?2018vv1562-53-0=   / https://www.courtlistener.com/api/rest/v3/opinions/5119138/
                "       In the United States Court of Federal Claims\n                          OFFICE OF SPECIAL MASTERS\n\n*********************\nLINDA WIRTSHAFTER,                    *\n                                      *      No. 18-1562V\n                  Petitioner,         *      Special Master Christian J. Moran\n                                      *\nv.                                    *      Filed: September 22, 2021\n                                      *\nSECRETARY OF HEALTH                   *      Attorneys’ fees and costs; remand\nAND HUMAN SERVICES,                   *\n                                      *\n                  Respondent.         *\n*********************\nHoward D. Mishkind, Mishkind Law Firm Co., L.P.A., Beachwood, OH, for\npetitioner;\nRyan D. Pyles, United States Dep’t of Justice, Washington, DC, for respondent.\n\nPUBLISHED DECISION AWARDING ATTORNEYS’ FEES AND COSTS1\n\n      An April 16, 2021 decision found that Linda Wirtshafter was not eligible for\nan award of attorneys’ fees and costs because she did not establish that a\nreasonable basis supported the claim that",
                {
                    "OpinionCluster": {
                        "precedential_status": "Published",
                    },
                },
            ),
            (
                # https://www.courtlistener.com/api/rest/v3/opinions/4184749/
                "                 In the United States Court of Federal Claims\n                                    OFFICE OF SPECIAL MASTERS\n                                            No. 15-1404V\n                                         (not to be published)\n\n*****************************\n                            *\nJEFFREY TREADWAY,           *                                            Special Master Corcoran\n                            *\n                            *\n                Petitioner, *                                            Filed: May 16, 2017\n                            *\n           v.               *                                            Decision; Attorney’s Fees and Costs.\n                            *\n                            *\nSECRETARY OF HEALTH AND     *\nHUMAN SERVICES,             *\n                            *\n                Respondent. *\n                            *\n*****************************\n\nWilliam E. Cochran, Black McLaren, et al., P.C., Memphis, TN, for Petitioner.\n\nAlexis B. Babcock, U. S. Dep’t of Justice, Washington, DC, for Respondent.\n\n                  DECISION GRANTING ATTORNEY’S FEES AND COSTS 1\n\n       On November 11, 2015, Jeffrey Treadway filed a petition seeking compensation under the\nNational Vaccine Injury Compensation Program (the “Vaccine Program”), alleging that he suffers\nfrom Bell’s palsy as a result of his October 10, 2014 receipt of the influenza vaccine.2 The parties\neventually filed a stipulation for damages on February 14, 2017 (ECF No. 24), which I adopted as\nmy dec",
                {},
            ),
        ],
        "juriscraper.opinions.united_states.state.pasuperct": [
            (
                "J-A13044-21\n\n                                   2021 PA Super 113\n\n\n  COMMONWEALTH OF PENNSYLVANIA                 :   IN THE SUPERIOR COURT OF\n                                               :        PENNSYLVANIA\n                                               :\n  ",
                {
                    "Citation": "2021 PA Super 113",
                },
            )
        ],
        "juriscraper.opinions.united_states.state.sc": [
            (
                # https://www.courtlistener.com/api/rest/v4/opinions/10744852/
                "                   THE STATE OF SOUTH CAROLINA\n                        In The Supreme Court\n\n             In the Matter of Lawrence J. Purvis, Jr., Respondent.\n\n             Appellate Case No. 2024-000453\n\n\n                              Opinion No. 28244\n             Submitted October 30, 2024 – Filed November 20, 2024\n\n\n",
                {
                    "Docket": {
                        "docket_number": "2024-000453",
                    },
                },
            )
        ],
        "juriscraper.opinions.united_states.state.sc_u": [
            (
                # https://www.courtlistener.com/api/rest/v4/opinions/10732544/
                "THIS OPINION HAS NO PRECEDENTIAL VALUE. IT SHOULD NOT BE\n   CITED OR RELIED ON AS PRECEDENT IN ANY PROCEEDING\n        EXCEPT AS PROVIDED BY RULE 268(d)(2), SCACR.\n\n                 THE STATE OF SOUTH CAROLINA\n                      In The Supreme Court\n\n        Robin Allen, Petitioner,\n\n        v.\n\n        Richard Winn Academy, Kristen Chaisson (in her\n        individual capacity and as Head of School), and John\n        Ryan II, Respondents.\n\n        Appellate Case No. 2023-000805\n\n\n\n     ON WRIT OF CERTIORARI TO THE COURT OF APPEALS\n\n\n                     Appeal from Fairfield County\n                Eugene C. Griffith, Jr., Circuit Court Judge\n\n\n                Memorandum Opinion No. 2024-MO-024\n       ",
                {
                    "Docket": {
                        "docket_number": "2023-000805",
                    },
                },
            )
        ],
        "juriscraper.opinions.united_states.state.scctapp_u": [
            (
                # https://www.courtlistener.com/api/rest/v4/opinions/10756176/
                "THIS OPINION HAS NO PRECEDENTIAL VALUE. IT SHOULD NOT BE\n   CITED OR RELIED ON AS PRECEDENT IN ANY PROCEEDING\n        EXCEPT AS PROVIDED BY RULE 268(d)(2), SCACR.\n\n                THE STATE OF SOUTH CAROLINA\n                    In The Court of Appeals\n\n        South Carolina Department of Social Services,\n        Respondent,\n\n        v.\n\n        Corey M. Nelson, Appellant.\n\n        In the interest of a minor under the age of eighteen.\n\n        Appellate Case No. 2024-000816\n\n\n\n                     Appeal From Richland County\n                  M. Scott Rankin, Family Court Judge\n\n\n ",
                {
                    "Docket": {
                        "docket_number": "2024-000816",
                    },
                },
            )
        ],
        "juriscraper.opinions.united_states.state.scctapp": [
            (
                # https://www.courtlistener.com/api/rest/v4/opinions/10744853/
                "                     THE STATE OF SOUTH CAROLINA\n                         In The Court of Appeals\n\n             Crescent Homes SC, LLC, Appellant,\n\n             v.\n\n             CJN, LLC, Respondent.\n\n             Appellate Case No. 2022-000897\n\n\n\n                        Appeal From Greenville County\n                    Charles B. Simmons, Jr., Master-in-Equity\n\n\n                               Opinion No. 6093\n                  Heard May 9, 2024 – Filed November 20, 2024\n\n\n                                   AFFIRMED\n\n\n             Ellis Reed-Hill Lesemann and Benjamin Houston Joyce,\n             both of Lesemann & Associates, LLC, of Charleston, for\n   ",
                {
                    "Docket": {
                        "docket_number": "2022-000897",
                    },
                },
            )
        ],
        "juriscraper.opinions.united_states.state.lactapp_2": [
            (
                # https://www.la2nd.org/wp-content/uploads/2025/04/56139-40ca.pdf,
                "Appealed from the\n                   Fourth Judicial District Court for the\n                       Parish of Ouachita, Louisiana\n                Trial Court Nos. 2015-3872 and 2024-2434\n\n                    Honorable Wilson Rambo, Judge\n\n                                *****\n\nDIANNE HILL                                          Counsel for Appellant,\n                                                     Darryl Michael Miller\n\nCUMMINS AND FITTS, LLC                               Counsel for Appellee,\nBy: Jessica L. Fitts                                 Cleo Miller\n\nTHE JONES LAW GROUP, LLC\nBy: Charles D. Jones\n\n\n                                *****\n\n         Before PITMAN, THOMPSON, and MARCOTTE, JJ.",
                {
                    "Docket": {
                        "appeal_from_str": "Fourth Judicial District Court for the Parish of Ouachita"
                    },
                    "OpinionCluster": {"judges": "PITMAN; THOMPSON; MARCOTTE"},
                },
            )
        ],
        "juriscraper.opinions.united_states.state.mont": [
            (
                # https://www.courtlistener.com/api/rest/v4/opinions/10801442/
                "'02/18/2025\n\n\n                                        DA 23-0746\n\n                IN THE SUPREME COURT OF THE STATE OF MONTANA\n\n                                         2025 MT 35\n\n\n\nIN THE MATTER OF THE ESTATE OF:\n\nWARREN DAN EDDLEMAN,",
                {
                    "Citation": "2025 MT 35",
                },
            )
        ],
        "juriscraper.opinions.united_states.state.ga": [
            # https://www.courtlistener.com/opinion/3186280/in-the-matter-of-tony-c-jones/
            (
                "298 Ga. 313\nFINAL COPY\n\nS11Y1626, S13Y0138, S15Y1641",
                {
                    "Citation": "298 Ga. 313",
                },
            )
        ],
        "juriscraper.opinions.united_states.state.me": [
            (
                "MAINE SUPREME JUDICIAL COURT Decision: 2025 ME 25\nDocket: Sag-24-5\nSubmitted\nOn Briefs: November 25, 2024\nDecided: March 11, 2025\nPanel: STANFILL, C.J., and HORTON, CONNORS, and DOUGLAS, JJ.\nReporter of Decisions\nSTEPHEN A. CLARK JR. et al.\nv.\nTOWN OF PHIPPSBURG et al.\nCONNORS, J.\n[¶1] This appeal pursuant to Maine Rule of Civil Procedure 80B",
                {
                    "Docket": {
                        "date_argued": "2024-11-25",
                        "docket_number": "Sag-24-5",
                    },
                    "Opinion": {
                        "author_str": "CONNORS, J.",
                        "per_curiam": False,
                    },
                    "OpinionCluster": {
                        "judges": "STANFILL, C.J., and HORTON, CONNORS, and DOUGLAS, JJ.",
                    },
                },
            ),
            (
                "MAINE SUPREME JUDICIAL COURT Decision: 2025 ME 26\nDocket: Pen-24-253\nSubmitted\nOn Briefs: February 7, 2025\nDecided: March 13, 2025\nPanel: STANFILL, C.J., and MEAD, CONNORS, LAWRENCE, and DOUGLAS, JJ.\nReporter of Decisions\nSTATE OF MAINE\nv.\nJEFF BELONY\nPER CURIAM\n[¶1] Jeff Belony appeals from",
                {
                    "Opinion": {"author_str": "", "per_curiam": True},
                    "OpinionCluster": {
                        "judges": "STANFILL, C.J., and MEAD, CONNORS, LAWRENCE, and DOUGLAS, JJ.",
                    },
                    "Docket": {
                        "date_argued": "2025-02-07",
                        "docket_number": "Pen-24-253",
                    },
                },
            ),
            (
                "MAINE SUPREME JUDICIAL COURT Decision: 2025 ME 32\nDocket: Han-23-466\nArgued: October 8, 2024\nDecided: March 27, 2025\nReporter of Decisions\nPanel: STANFILL, C.J., and MEAD, HORTON, CONNORS, LAWRENCE, and DOUGLAS, JJ.\nSTATE OF MAINE\nv.\nCRAIG A. WOODARD\nSTANFILL, C.J.\n[¶1]",
                {
                    "Opinion": {
                        "author_str": "STANFILL, C.J.",
                        "per_curiam": False,
                    },
                    "OpinionCluster": {
                        "judges": "STANFILL, C.J., and MEAD, HORTON, CONNORS, LAWRENCE, and DOUGLAS, JJ.",
                    },
                    "Docket": {
                        "date_argued": "2024-10-08",
                        "docket_number": "Han-23-466",
                    },
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.or": [
            # https://www.courtlistener.com/opinion/10160687/mclaughlin-v-wilson/
            (
                """"                                        535\n\n   Argued and submitted May 15, at Mt. Hood Community College, Gresham,\n    Oregon; decision of Court of Appeals affirmed, judgment of circuit court\n  reversed in part, and case remanded to circuit court for further proceedings\n                               September 12, 2019\n\n\n\n                    Nicole McLAUGHLIN,\n                    Respondent on Review,\n                               v.\n                   Kenneth WILSON, M.D.,\n                     Petitioner on Review.\n           (CC 13C21746) (CA A160000) (SC S066047)\n                                    449 P3d 492\n\n     Plaintiff filed complaint alleging """,
                {"Citation": "449 P3d 492"},
            )
        ],
        "juriscraper.opinions.united_states.state.orctapp": [
            # https://www.courtlistener.com/opinion/10161013/state-v-oxford/pdf/
            (
                """"                                      184\n\n    On appellant’s petition for reconsideration filed June 29, reconsideration\nallowed, former opinion (302 Or App 407, 461 P3d 249) withdrawn; reversed and\n                           remanded October 7, 2020\n\n\n                       STATE OF OREGON,\n                        Plaintiff-Respondent,\n                                  v.\n                       NATHAN OXFORD,\n                    aka Nathan Daniel Oxford,\n                       Defendant-Appellant.\n                  Multnomah County Circuit Court\n                        140230856; A161408\n                                   474 P3d 465\n\n    Defendant, who was convicted of various sex crimes, seeks reconsideration""",
                {"Citation": "474 P3d 465"},
            ),
        ],
        "juriscraper.opinions.united_states.state.tenn": [
            (
                """"  IN THE SUPREME COURT OF TENNESSEE\n                      AT KNOXVILLE\n                  September 5, 2024 Session\nPAYTON CASTILLO v. DAVID LLOYD REX, M.D. ET AL.\n      Appeal by Permission from the Court of Appeals\n             Circuit Court for Hamilton County\n    No. 20C1270       Ward Jeffrey Holl""",
                {
                    "Docket": {
                        "appeal_from_str": "Circuit Court for Hamilton County"
                    },
                    "OpinionCluster": {"precedential_status": "Published"},
                },
            ),
            (
                """ 03/11/2025\n                   IN THE COURT OF APPEALS OF TENNESSEE\n                                AT JACKSON\n\n              MANOUCHEKA THERMITUS v. SCHILLER JEROME\n\n                     Appeal from the Chancery Court for Shelby County\n                      No. CH-22-0257 JoeDae L. Jenkins, Chancellor\n                          ___________________________________\n\n                                No. W2024-01508-COA-R3-CV\n                            ___________________________________\n\n\nAppellant, Schiller Jerome, has appealed an order of the Shelby County Chancery Court\nthat was entered on September 3, 2024. We determine that the trial court’s order does not\nconstitute a final appealable judgment. As a result, this Court lacks jurisdiction to consider\nthis appeal. The appeal is, therefore, dismissed.\n\n                  Tenn. R. App. P. 3 Appeal as of Right; Appeal Dismissed.\n\nJ. STEVEN STAFFORD, P.J., W.S.; KENNY ARMSTRONG, J.; CARMA DENNIS MCGEE, J.\n\nLinda Kendall Garner, Memphis, Tennessee, for the appellant, Schiller Jerome.\n\nZachary Michael Moore, Memphis, Tennessee, for the appellee, Manoucheka Thermitus.\n\n\n                                   MEMORANDUM OPINION1\n""",
                {
                    "Docket": {
                        "appeal_from_str": "Chancery Court for Shelby County"
                    },
                    "OpinionCluster": {"precedential_status": "Unpublished"},
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.tenncrimapp": [
            (
                """05/28/2025\nIN THE COURT OF CRIMINAL APPEALS OF TENNESSEE\nAT KNOXVILLE\nAssigned on Briefs May 20, 2025\nSTATE OF TENNESSEE v. TRA’SHAWN GLASS\nAppeal from the Criminal Court for Knox County\nNo. 125669 Steven Wayne Sword, Judge\n___________________________________\n""",
                {
                    "Docket": {
                        "appeal_from_str": "Criminal Court for Knox County"
                    },
                    "OpinionCluster": {"precedential_status": "Published"},
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.tennctapp": [
            (
                """05/28/2025\nIN THE COURT OF APPEALS OF TENNESSEE\nAT NASHVILLE\nApril 2, 2024 Session\nHEATHER MARIE BAILEY v. DANIEL MICHAEL BAILEY\nAppeal from the General Sessions Court for Warren County\nNo. 21-DV-9505 L. Craig Johnson, Judge1""",
                {
                    "Docket": {
                        "appeal_from_str": "General Sessions Court for Warren County"
                    },
                    "OpinionCluster": {"precedential_status": "Published"},
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.lactapp_4": [
            (
                """PLAQUEMINES PORT                         *       NO. 2024-CA-0614\nHARBOR & TERMINAL\nDISTRICT                                 *\n                                                 COURT OF APPEAL\nVERSUS                                   *\n                                                 FOURTH CIRCUIT\nTUAN NGUYEN                              *\n                                                 STATE OF LOUISIANA\n                                   *******\n\n\n\n                               APPEAL FROM\n                   25TH JDC, PARISH OF PLAQUEMINES\n                          NO. 68-734, DIVISION “A”\n                          Honorable Kevin D. Conner\n                                  ******\n                          Judge Monique G. Morial\n                                  ******\n(Court composed of Judge Daniel L. Dysart, Judge Rosemary Ledet, Judge Tiffany\nGautier Chase, Judge Nakisha Ervin-Knott, Judge Monique G. Morial)""",
                {
                    "Docket": {
                        "panel_str": "Judge Daniel L. Dysart; Judge Rosemary Ledet; Judge Tiffany Gautier Chase; Judge Nakisha Ervin-Knott; Judge Monique G. Morial"
                    },
                    "Opinion": {
                        "author_str": "Judge Monique G. Morial",
                        "type": "020lead",
                    },
                    "OpinionCluster": {
                        "judges": "Judge Daniel L. Dysart; Judge Rosemary Ledet; Judge Tiffany Gautier Chase; Judge Nakisha Ervin-Knott; Judge Monique G. Morial"
                    },
                },
            ),
            (
                """      STERLING DOUCETTE, * NO. 2024sCAs0585\nDAVID NIXON, AND LEON\nRICHARD * COURT OF APPEAL\n\nVERSUS * FOURTH CIRCUIT\n\nEASTOVER PROPERTY * STATE OF LOUISIANA\nOWNERS" ASSOCIATION,\nINC. AND EASTOVER *\nNEIGHBORHOOD\nIMPROVEMENT AND *\nSECURITY DISTRICT *******\n\n\nJCL LOBRANO, J., CONCURS IN THE RESULT""",
                {
                    "Docket": {},
                    "Opinion": {
                        "author_str": "Lobrano",
                        "type": "030concurrence",
                    },
                    "OpinionCluster": {},
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.indtc": [
            (
                """PETITIONERS APPEARING PRO SE: ATTORNEY FOR RESPONDENT:\nLAWRENCE PACHNIAK MARILYN S. MEIGHEN\nCulver, IN MEIGHEN & ASSOCIATES, P.C.\nCarmel, IN\n_____________________________________________________________________\nIN THE\nINDIANA TAX COURT\n_____________________________________________________________________\nLAWRENCE and GLENDA PACHNIAK, )\nPetitioners, )\nv. ) Cause No. 49T10-0904-TA-18\nMARSHALL COUNTY ASSESSOR, )\n)\n)\n)\n)\nRespondent. )\n______________________________________________________________________\nON APPEAL FROM A FINAL DETERMINATION OF\nTHE INDIANA BOARD OF TAX REVIEW\nNOT FOR PUBLICATION\nJune 8, 2010\nFISHER, J.\nLawrence and Glenda Pachniak (the Pachniaks) challenge the final""",
                {
                    "OpinionCluster": {"precedential_status": "Unpublished"},
                },
            ),
        ],
        # https://www.courtlistener.com/api/rest/v4/opinions/2684767/
        "juriscraper.opinions.united_states.state.neb": [
            (
                "SYLISSA J.\t607\n\t                             Cite as 288 Neb. 607\n\namended ",
                {"Citation": "288 Neb. 607"},
            )
        ],
        # https://www.courtlistener.com/api/rest/v4/opinions/2810802/
        "juriscraper.opinions.united_states.state.nebctapp": [
            (
                "TRUST\t999\n\t                        Cite as 22 Neb. App. 999\n\nthe iss",
                {"Citation": "22 Neb. App. 999"},
            )
        ],
        "juriscraper.opinions.united_states.state.texbizct": [
            (
                """\nThe Business Court of Texas,\n11th Division\nWESTLAKE LONGVIEW CORP. and §\nWESTLAKE CHEMICAL OPCO LP,  §\nPlaintiffs,             § Cause No. 24-BC11B-0023 \nv.                          §\nEASTMAN CHEMICAL CO.,       §\nDefendant.              §\n═══════════════════════════════════════\nOPINION ON MOTION FOR PROTECTIVE ORDER\n══\nsuch evidence in the future, if a party moves to modify the protective order to allow\nspecific in-house attorneys access to AEO material.\nDate signed: May 16, 2025""",
                {
                    "OpinionCluster": {
                        "date_filed": "2025-05-16",
                        "date_filed_is_approximate": False,
                    },
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.alaska": [
            (
                "NOTICE\n      Memorandum decisions of this court do not create legal precedent. A party wishing to cite\n      such a decision in a brief or at oral argument should review Alaska Appellate Rule 214(d).\n\n\n               THE SUPREME COURT OF THE STATE OF ALASKA\n\n\n TREVOR PAUL FAIRBANKS,                           )\n                                                  )     Supreme Court No. S-19193\n                       Appellant,                 )\n                                                  )     Superior Court No. 3AN-19-05436 CI\n          v.                                      )\n                                                  )     MEMORANDUM OPINION\n CARA EILEEN FOX, f/k/a Cara Fox                  )        AND JUDGMENT*\n Fairbanks,                                       )\n                                                  )     No. 2100 – August 13, 2025\n                       Appellee.                  )\n                                                  )\n\n               Appeal from the Superior Court of the State of Alaska, Third\n               Judicial District, Anchorage, Josie Garton, Judge.\n\n               Appearances: Trevor Paul Fairbanks, pro se, Anchorage,\n               Appellant. Notice of nonparticipation filed by Kara A.\n               Nyquist, Nyquist Law Group, Anchorage, for Appellee.\n\n               Before: Carney, Borghesan, Henderson, and Pate, Justices.\n               [Maassen, Chief Justice, not participating.]",
                {
                    "Docket": {
                        "appeal_from_str": "Superior Court of the State of Alaska, Third Judicial District",
                    },
                    "OriginatingCourtInformation": {
                        "assigned_to_str": "Josie Garton"
                    },
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.alaskactapp": [
            (
                "NOTICE\n      Memorandum decisions of this court do not create legal precedent. A party wishing to cite\n      such a decision in a brief or at oral argument should review Alaska Appellate Rule 214(d).\n\n\n               THE SUPREME COURT OF THE STATE OF ALASKA\n\n\n TREVOR PAUL FAIRBANKS,                           )\n                                                  )     Supreme Court No. S-19193\n                       Appellant,                 )\n                                                  )     Superior Court No. 3AN-19-05436 CI\n          v.                                      )\n                                                  )     MEMORANDUM OPINION\n CARA EILEEN FOX, f/k/a Cara Fox                  )        AND JUDGMENT*\n Fairbanks,                                       )\n                                                  )     No. 2100 – August 13, 2025\n                       Appellee.                  )\n                                                  )\n\n               Appeal from the Superior Court of the State of Alaska, Third\n               Judicial District, Anchorage, Josie Garton, Judge.\n\n               Appearances: Trevor Paul Fairbanks, pro se, Anchorage,\n               Appellant. Notice of nonparticipation filed by Kara A.\n               Nyquist, Nyquist Law Group, Anchorage, for Appellee.\n\n               Before: Carney, Borghesan, Henderson, and Pate, Justices.\n               [Maassen, Chief Justice, not participating.]",
                {
                    "Docket": {
                        "appeal_from_str": "Superior Court of the State of Alaska, Third Judicial District",
                    },
                    "OriginatingCourtInformation": {
                        "assigned_to_str": "Josie Garton"
                    },
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.alaska_u": [
            (
                "NOTICE\n      Memorandum decisions of this court do not create legal precedent. A party wishing to cite\n      such a decision in a brief or at oral argument should review Alaska Appellate Rule 214(d).\n\n\n               THE SUPREME COURT OF THE STATE OF ALASKA\n\n\n TREVOR PAUL FAIRBANKS,                           )\n                                                  )     Supreme Court No. S-19193\n                       Appellant,                 )\n                                                  )     Superior Court No. 3AN-19-05436 CI\n          v.                                      )\n                                                  )     MEMORANDUM OPINION\n CARA EILEEN FOX, f/k/a Cara Fox                  )        AND JUDGMENT*\n Fairbanks,                                       )\n                                                  )     No. 2100 – August 13, 2025\n                       Appellee.                  )\n                                                  )\n\n               Appeal from the Superior Court of the State of Alaska, Third\n               Judicial District, Anchorage, Josie Garton, Judge.\n\n               Appearances: Trevor Paul Fairbanks, pro se, Anchorage,\n               Appellant. Notice of nonparticipation filed by Kara A.\n               Nyquist, Nyquist Law Group, Anchorage, for Appellee.\n\n               Before: Carney, Borghesan, Henderson, and Pate, Justices.\n               [Maassen, Chief Justice, not participating.]",
                {
                    "Docket": {
                        "appeal_from_str": "Superior Court of the State of Alaska, Third Judicial District",
                    },
                    "OriginatingCourtInformation": {
                        "assigned_to_str": "Josie Garton"
                    },
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.ariz": [
            (
                "IN THE\n\n   SUPREME COURT OF THE STATE OF ARIZONA\n\n          PHOENIX UNION HIGH SCHOOL DISTRICT NO. 210,\n                          Petitioner,\n\n                                  v.\n\n  THE HON. JOAN M. SINCLAIR, JUDGE OF THE SUPERIOR COURT OF THE\n      STATE OF ARIZONA, IN AND FOR THE COUNTY OF MARICOPA,\n                            Respondent,\n\n                                And\n\nCHRISTOPHER A. LUCERO, A MINOR CHILD, BY AND THROUGH HIS NATURAL\n                 FATHER, CHRISTOPHER J. LUCERO,\n                       Real Party in Interest.\n\n\n\n\n                         No. CV-24-0307-PR\n                         Filed July 15, 2025\n\n\nPetition for Special Action from the Superior Court in Maricopa County\n                 The Honorable Joan M. Sinclair, Judge\n                           No. CV2022-005719\n\n      REVERSED AND REMANDED WITH INSTRUCTIONS\n\n\n           Order from the Court of Appeals, Division One\n                         1 CA-SA 24-0205\n                      Filed December 4, 2024\n\n                             VACATED\n                   PUSD 210 V. HON. SINCLAIR/LUCERO\n                         Opinion of the Court",
                {
                    "Docket": {
                        "appeal_from_str": "Superior Court in Maricopa County",
                    },
                    "OriginatingCourtInformation": {
                        "assigned_to_str": "Honorable Joan M. Sinclair"
                    },
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.arizctapp_div_1": [
            (
                "IN THE\n\n   SUPREME COURT OF THE STATE OF ARIZONA\n\n          PHOENIX UNION HIGH SCHOOL DISTRICT NO. 210,\n                          Petitioner,\n\n                                  v.\n\n  THE HON. JOAN M. SINCLAIR, JUDGE OF THE SUPERIOR COURT OF THE\n      STATE OF ARIZONA, IN AND FOR THE COUNTY OF MARICOPA,\n                            Respondent,\n\n                                And\n\nCHRISTOPHER A. LUCERO, A MINOR CHILD, BY AND THROUGH HIS NATURAL\n                 FATHER, CHRISTOPHER J. LUCERO,\n                       Real Party in Interest.\n\n\n\n\n                         No. CV-24-0307-PR\n                         Filed July 15, 2025\n\n\nPetition for Special Action from the Superior Court in Maricopa County\n                 The Honorable Joan M. Sinclair, Judge\n                           No. CV2022-005719\n\n      REVERSED AND REMANDED WITH INSTRUCTIONS\n\n\n           Order from the Court of Appeals, Division One\n                         1 CA-SA 24-0205\n                      Filed December 4, 2024\n\n                             VACATED\n                   PUSD 210 V. HON. SINCLAIR/LUCERO\n                         Opinion of the Court",
                {
                    "Docket": {
                        "appeal_from_str": "Superior Court in Maricopa County",
                    },
                    "OriginatingCourtInformation": {
                        "assigned_to_str": "Honorable Joan M. Sinclair"
                    },
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.arizctapp_div_2": [
            (
                "IN THE\n\n   SUPREME COURT OF THE STATE OF ARIZONA\n\n          PHOENIX UNION HIGH SCHOOL DISTRICT NO. 210,\n                          Petitioner,\n\n                                  v.\n\n  THE HON. JOAN M. SINCLAIR, JUDGE OF THE SUPERIOR COURT OF THE\n      STATE OF ARIZONA, IN AND FOR THE COUNTY OF MARICOPA,\n                            Respondent,\n\n                                And\n\nCHRISTOPHER A. LUCERO, A MINOR CHILD, BY AND THROUGH HIS NATURAL\n                 FATHER, CHRISTOPHER J. LUCERO,\n                       Real Party in Interest.\n\n\n\n\n                         No. CV-24-0307-PR\n                         Filed July 15, 2025\n\n\nPetition for Special Action from the Superior Court in Maricopa County\n                 The Honorable Joan M. Sinclair, Judge\n                           No. CV2022-005719\n\n      REVERSED AND REMANDED WITH INSTRUCTIONS\n\n\n           Order from the Court of Appeals, Division One\n                         1 CA-SA 24-0205\n                      Filed December 4, 2024\n\n                             VACATED\n                   PUSD 210 V. HON. SINCLAIR/LUCERO\n                         Opinion of the Court",
                {
                    "Docket": {
                        "appeal_from_str": "Superior Court in Maricopa County",
                    },
                    "OriginatingCourtInformation": {
                        "assigned_to_str": "Honorable Joan M. Sinclair"
                    },
                },
            ),
        ],
    }

    def test_extract_from_text(self):
        """Test that extract_from_text returns the expected data."""
        # prevent logger.error calls to be triggered
        logging.disable(logging.CRITICAL)
        for module_string, test_cases in self.test_data.items():
            package, module = module_string.rsplit(".", 1)
            mod = __import__(
                f"{package}.{module}", globals(), locals(), [module]
            )
            site = mod.Site()

            # ensure that if no data is parsed, a dict is returned
            # also, this ensures that there are no uncontrolled exceptions
            self.assertTrue(
                isinstance(
                    site.extract_from_text("Lorem ipsum dolorem..."), dict
                )
            )
            for test_case in test_cases:
                self.assertEqual(
                    site.extract_from_text(test_case[0]), test_case[1]
                )
        logging.disable(logging.NOTSET)

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
            if mod.Site.extract_from_text == OpinionSite.extract_from_text:
                # Method is not overridden, so skip it.
                continue
            self.assertIn(
                module_string,
                self.test_data.keys(),
                msg=f"{module_string} not yet added to extract_from_text test data.",
            )

    def test_valid_date_format(self):
        """Is the returned date format valid for a Django model date field?

        Django models will accept date objects and strings. If a string is not
        in the database datestring format, it will error

        ```
        django.core.exceptions.ValidationError:
        [“July 29, 2022" value has an invalid date format. It must be in YYYY-MM-DD format.]
        ```

        Even if the database accepts a disambiguation format, let's standardize
        to the ISO format YYYY-MM-DD or YYYY/MM/DD

        psql $ show datestyle
        > ISO, MDY
        """
        for module_string, test_cases in self.test_data.items():
            for test_case in test_cases:
                for dic in test_case[1].values():
                    if isinstance(dic, str):  # skip citation string
                        continue

                    for key, value in dic.items():
                        if "date" not in key or key in [
                            "date_blocked",
                            "date_filed_is_approximate",
                        ]:
                            continue

                        if isinstance(value, str):
                            try:
                                datetime.strptime(value, "%Y/%m/%d")
                            except ValueError:
                                try:
                                    datetime.strptime(value, "%Y-%m-%d")
                                except ValueError:
                                    self.fail(
                                        f"Date string not in valid ISO format {module_string} '{key}' '{value}'"
                                    )
                        elif not isinstance(value, date):
                            self.fail(
                                f"Not an accepted type for a date field {module_string} '{key}' '{value}'"
                            )
