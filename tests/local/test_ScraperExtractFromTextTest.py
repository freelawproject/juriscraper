import datetime
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
        "juriscraper.opinions.united_states.state.sd": [
            (
                """#30018-a-MES\n2023 S.D. 4""",
                {"Docket": {"docket_number": "#30018-a-MES"}},
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
                    "OpinionCluster": {
                        "date_filed": datetime.date(2001, 4, 26)
                    },
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
                    "Citation": {
                        "volume": "81",
                        "reporter": "Misc 3d",
                        "page": "1215(A)",
                        "type": 2,
                    },
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
                    "Citation": {
                        "volume": "66",
                        "reporter": "Misc 3d",
                        "page": "1213(A)",
                        "type": 2,
                    },
                    "OpinionCluster": {
                        "case_name_full": "The People of the State of New York, against J.S., Adolescent Offender."
                    },
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.nycivct": [
            (
                # https://www.nycourts.gov/reporter/3dseries/2023/2023_23397.htm
                """<table width="80%" border="1" cellspacing="2" cellpadding="5" align="center">\n<tr>\n<td align="center"><b>City of New York v "Doe"</b></td>\n</tr>\n<tr>\n<td align="center">2023 NY Slip Op 23397</td>\n</tr>\n<tr>\n<td align="center">Decided on December 18, 2023</td>\n</tr>\n<tr>\n<td align="center">Civil Court Of The City Of New York, Bronx County</td>\n</tr>\n<tr>\n<td align="center">Zellan, J.</td>\n</tr>\n<tr>\n<td align="center">Published by New York State Law Reporting Bureau pursuant to Judiciary Law § 431.</td>\n</tr>\n<tr>\n<td align="center">This opinion is uncorrected and subject to revision before publication in the printed Official Reports.</td></tr>\n</table>\n<br><br>\nDecided on December 18, 2023\n<br><div align="center">Civil Court of the City of New York, Bronx County</div>\n\n<br><table width="75%" border="1" cellspacing="1" cellpadding="4" align="center"><tr><td><br><div align="center"><b>City \n\tof New York, Petitioner(s),\n\n<br><br>against<br><br>"John" "Doe"; "Jane" "Doe"; "John" "Doe"; "Jane" "Doe", Respondent(s).</b></div><br><br>\n\n</td></tr></table><br><br>Index No. LT-300755-22/BX\n<br><br><br>Maurice Dobson, Special Assistant Corporation Counsel, New York City Department of Housing Preservation &amp; Development (Isidore Scipio, of counsel), New York, NY, for petitioner.<br><br>April Whitehead, Irvington, NY, for respondents Alexander Aqel and Aqel Sheet Metal Inc.<p></p><br>Jeffrey S. Zellan, J. <p>Recitation, as required by CPLR 2219(a), of the papers considered in the review of this motion:</p>""",
                {
                    "Docket": {
                        "docket_number": "Index No. LT-300755-22/BX",
                        "case_name_full": 'City of New York, Petitioner(s), against "John" "Doe" "Jane" "Doe" "John" "Doe" "Jane" "Doe", Respondent(s).',
                    },
                    "Opinion": {"author_str": "Jeffrey S. Zellan"},
                    "OpinionCluster": {
                        "case_name_full": 'City of New York, Petitioner(s), against "John" "Doe" "Jane" "Doe" "John" "Doe" "Jane" "Doe", Respondent(s).'
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
                    "Citation": {
                        "volume": "81",
                        "reporter": "Misc 3d",
                        "page": "1211(A)",
                        "type": 2,
                    },
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
                    "Citation": {
                        "volume": "78",
                        "reporter": "Misc 3d",
                        "page": "1203(A)",
                        "type": 2,
                    },
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
                    "Citation": {
                        "volume": "66",
                        "reporter": "Misc 3d",
                        "page": "1210(A)",
                        "type": 2,
                    },
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
                    "Citation": {
                        "volume": "73",
                        "reporter": "Misc 3d",
                        "page": "1238(A)",
                        "type": 2,
                    },
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
                    "Citation": {
                        "volume": "58",
                        "reporter": "Misc 3d",
                        "page": "1215(A)",
                        "type": 2,
                    },
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
                    "Citation": {
                        "volume": "59",
                        "reporter": "Misc 3d",
                        "page": "1211(A)",
                        "type": 2,
                    },
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
                    "Citation": {
                        "volume": "78",
                        "reporter": "Misc 3d",
                        "page": "1211(A)",
                        "type": 2,
                    },
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
                    "Citation": {
                        "volume": "81",
                        "reporter": "Misc 3d",
                        "page": "1210(A)",
                        "type": 2,
                    },
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
                    "Citation": {
                        "volume": "2024",
                        "reporter": "ND",
                        "page": "143",
                        "type": 8,
                    },
                },
            ),
            (
                # Example of a consolidated case
                # https://www.courtlistener.com/api/rest/v3/opinions/10473085/
                """IN THE SUPREME COURT\n                        STATE OF NORTH DAKOTA\n\n                                      2024 ND 141\n\nRenae Irene Gerszewski,                                           Petitioner and Appellee\n      v.\nConrad Keith Rostvet,                                          Respondent and Appellant\n\n\n\n                                     No. 20230361\n\n\n\nConrad Keith Rostvet,                                            Petitioner and Appellant\n      v.\nRenae Irene Gerszewski,                                         Respondent and Appellee\n\n\n\n                                     No. 20230362\n\n\n\nConrad Rostvet,                                                  Petitioner and Appellant\n      v.\nWayne Gerszewski,                                               Respondent and Appellee\n\n\n\n                                     No. 20230363\n\n\n\nAppeal from the District Court of Walsh County, Northeast Judicial District, the Honorable\nBarbara L. Whelan, Judge.\n\fAFFIRMED.\n\nOpinion of the Court by Tufte, Justice.\n\nSamuel A. Gereszek, Grand Forks, N.D., for appellees.\n\nTimothy C. Lamb, Grand Forks, N.D., for appellant.\n\f                                 Gerszewski v. Rostvet\n                                Nos. 20230361–20230363\n\nTufte, Justice.\n\n[¶1] Conrad Rostvet appeals from a district court’s order""",
                {
                    "Citation": {
                        "volume": "2024",
                        "reporter": "ND",
                        "page": "141",
                        "type": 8,
                    },
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
                    "Citation": {
                        "volume": "2023",
                        "reporter": "WI",
                        "page": "50",
                        "type": 8,
                    },
                },
            )
        ],
        "juriscraper.opinions.united_states.state.wisctapp": [
            (
                # https://www.wicourts.gov/ca/opinion/DisplayDocument.pdf?content=pdf&seqNo=799325
                """2024 WI App 36\nCOURT OF APPEALS OF WISCONSIN\nPUBLISHED OPINION""",
                {
                    "Citation": {
                        "volume": "2024",
                        "reporter": "WI App",
                        "page": "36",
                        "type": 8,
                    },
                },
            )
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
