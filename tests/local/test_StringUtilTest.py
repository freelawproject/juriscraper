#!/usr/bin/env python


import unittest

from juriscraper.lib.date_utils import is_first_month_in_quarter, quarter
from juriscraper.lib.diff_tools import normalize_phrase
from juriscraper.lib.string_utils import (
    CaseNameTweaker,
    clean_string,
    convert_date_string,
    fix_camel_case,
    force_unicode,
    harmonize,
    normalize_dashes,
    split_date_range_string,
    titlecase,
)


class StringUtilTest(unittest.TestCase):
    def test_make_short_name(self):
        test_pairs = [
            # In re and Matter of
            ("In re Lissner", "In re Lissner"),
            ("Matter of Lissner", "Matter of Lissner"),
            # Plaintiff is in bad word list
            ("State v. Lissner", "Lissner"),
            ("People v. Lissner", "Lissner"),
            ("California v. Lissner", "Lissner"),
            ("Dallas v. Lissner", "Lissner"),
            # Basic 3-word case
            ("Langley v. Google", "Langley"),
            # Similar to above, but more than 3 words
            ("Langley v. Google foo", "Langley"),
            # United States v. ...
            ("United States v. Lissner", "Lissner"),
            # Corporate first name
            ("Google, Inc. v. Langley", "Langley"),
            ("Special, LLC v. Langley", "Langley"),
            ("Google Corp. v. Langley", "Langley"),
            # Shorter appellant than plaintiff
            ("Michael Lissner v. Langley", "Langley"),
            # Multi-v with and w/o a bad_word
            ("Alameda v. Victor v. Keyboard", ""),
            ("Bloggers v. Victor v. Keyboard", ""),
            # Long left, short right
            ("Many words here v. Langley", "Langley"),
            # Other manually added items
            ("Ilarion v. State", "Ilarion"),
            ("Imery v. Vangil Ingenieros", "Imery"),
            # Many more tests from real data!
            ("Bean v. City of Monahans", "Bean"),
            ("Blanke v. Time, Inc.", "Blanke"),
            ("New York Life Ins. Co. v. Deshotel", "Deshotel"),
            ("Deatherage v. Deatherage", "Deatherage"),
            ("Gonzalez Vargas v. Holder", ""),
            ("Campbell v. Wainwright", "Campbell"),
            ("Liggett & Myers Tobacco Co. v. Finzer", "Finzer"),
            ("United States v. Brenes", "Brenes"),
            ("A.H. Robins Co., Inc. v. Eli Lilly & Co", ""),
            ("McKellar v. Hazen", "McKellar"),
            ("Gil v. State", "Gil"),
            ("Fuentes v. Owen", "Fuentes"),
            ("State v. Shearer", "Shearer"),
            ("United States v. Smither", "Smither"),
            ("People v. Bradbury", "Bradbury"),
            ("Venable (James) v. State", ""),
            ("Burkhardt v. Bailey", "Burkhardt"),
            ("DeLorenzo v. Bales", "DeLorenzo"),
            ("Loucks v. Bauman", "Loucks"),
            ("Kenneth Stern v. Robert Weinstein", ""),
            ("Rayner v. Secretary of Health and Human Services", "Rayner"),
            ("Rhyne v. Martin", "Rhyne"),
            ("State v. Wolverton", "Wolverton"),
            ("State v. Flood", "Flood"),
            ("Amason v. Natural Gas Pipeline Co.", "Amason"),
            ("United States v. Bryant", "Bryant"),
            ("WELLS FARGO BANK v. APACHE TRIBE OF OKLAHOMA", ""),
            ("Stewart v. Tupperware Corp.", "Stewart"),
            ("Society of New York Hosp. v. ASSOCIATED HOSP. SERV. OF NY", ""),
            ("Stein v. State Tax Commission", "Stein"),
            (
                "The Putnam Pit, Inc. Geoffrey Davidian v. City of Cookeville, Tennessee Jim Shipley",
                "",
            ),
            ("People v. Armstrong", "Armstrong"),
            ("Weeks v. Weeks", "Weeks"),
            ("Smith v. Xerox Corp.", ""),
            ("In Interest of Ad", ""),
            ("People v. Forsyth", "Forsyth"),
            ("State v. LeClair", "LeClair"),
            ("Agristor Credit Corp. v. Unruh", "Unruh"),
            ("United States v. Larry L. Stewart", ""),
            ("Starling v. United States", "Starling"),
            ("United States v. Pablo Colin-Molina", ""),
            ("Kenneth N. Juhl v. The United States", ""),
            ("Matter of Wilson", "Matter of Wilson"),
            ("In Re Damon H.", ""),
            ("Centennial Ins. Co. v. Zylberberg", "Zylberberg"),
            ("United States v. Donald Lee Stotler", ""),
            ("Byndloss v. State", "Byndloss"),
            ("People v. Piatkowski", "Piatkowski"),
            ("United States v. Willie James Morgan", ""),
            ("Harbison (Debra) v. Thieret (James)", ""),
            ("Federal Land Bank of Columbia v. Lieben", "Lieben"),
            ("John Willard Greywind v. John T. Podrebarac", ""),
            ("State v. Powell", "Powell"),
            ("Carr v. Galloway", "Carr"),
            ("Saylors v. State", "Saylors"),
            ("Jones v. Franke", "Jones"),
            (
                "In Re Robert L. Mills, Debtor. Robert L. Mills v. Sdrawde "
                "Titleholders, Inc., a California Corporation",
                "",
            ),
            (
                "Pollenex Corporation v. Sunbeam-Home Comfort, a Division of "
                "Sunbeam Corp., Raymond Industrial, Limited and Raymond Marketing "
                "Corporation of North America",
                "",
            ),
            ("Longs v. State", "Longs"),
            ("Performance Network Solutions v. Cyberklix", "Cyberklix"),
            ("DiSabatino v. Salicete", "DiSabatino"),
            ("State v. Jennifer Nicole Jackson", ""),
            ("United States v. Moreno", "Moreno"),
            ("LOGAN & KANAWHA COAL v. Banque Francaise", ""),
            ("State v. Harrison", "Harrison"),
            ("Efford v. Milam", "Efford"),
            ("People v. Thompson", "Thompson"),
            ("CINCINNATI THERMAL SPRAY v. Pender County", ""),
            ("JAH Ex Rel. RMH v. Wadle & Associates", ""),
            ("United Pub. Employees v. CITY & CTY. OF SAN FRAN.", ""),
            ("Warren v. Massachusetts Indemnity", "Warren"),
            (
                'Marion Edwards v. State Farm Insurance Company and "John Doe,"',
                "",
            ),
            ("Snowdon v. Grillo", "Snowdon"),
            ("Adam Lunsford v. Cravens Funeral Home", ""),
            ("State v. Dillon", "Dillon"),
            ("In Re Graham", "In Re Graham"),
            ("Durham v. Chrysler Corp.", ""),  # Fails b/c Durham is a city!
            ("Carolyn Warrick v. Motiva Enterprises, L.L.C", ""),
            ("United States v. Aloi", "Aloi"),
            ("United States Fidelity & Guaranty v. Graham", "Graham"),
            ("Wildberger v. Rosenbaum", "Wildberger"),
            ("Truck Insurance Exchange v. Michling", "Michling"),
            ("Black Voters v. John J. McDonough", ""),
            ("State of Tennessee v. William F. Cain", ""),
            ("Robert J. Imbrogno v. Defense Logistics Agency", ""),
            ("Leetta Beachum, Administratrix v. Timothy Joseph White", ""),
            ("United States v. Jorge Gonzalez-Villegas", ""),
            ("Pitts v. Florida Bd. of Bar Examiners", "Pitts"),
            ("State v. Pastushin", "Pastushin"),
            ("Clark v. Clark", ""),
            ("Barrios v. Holder", "Barrios"),
            ("Gregory L. Lavin v. United States", ""),
            ("Carpenter v. Consumers Power", "Carpenter"),
            ("Derbabian v. S & C SNOWPLOWING, INC.", "Derbabian"),
            ("Bright v. LSI CORP.", "Bright"),
            ("State v. Brown", "Brown"),
            ("KENNEY v. Keebler Co.", "KENNEY"),
            ("Hill v. Chalanor", "Hill"),
            ("Washington v. New Jersey", ""),
            ("Sollek v. Laseter", "Sollek"),
            (
                "United States v. John Handy Jones, International Fidelity "
                "Insurance Company",
                "",
            ),
            ("N.L.R.B. v. I. W. Corp", ""),
            ("Karpisek v. Cather & Sons Construction, Inc.", "Karpisek"),
            ("Com. v. Wade", "Wade"),
            ("Glascock v. Sukumlyn", "Glascock"),
            ("Burroughs v. Hills", "Burroughs"),
            ("State v. Darren Matthew Lee", ""),
            ("Mastondrea v. Occidental Hotels Management", "Mastondrea"),
            ("Kent v. C. I. R", "Kent"),
            ("Johnson v. City of Detroit", ""),
            ("Nolan v. United States", "Nolan"),
            ("Currence v. Denver Tramway Corporation", "Currence"),
            ("Matter of Cano", "Matter of Cano"),
            # Two words after "Matter of --> Punt."
            ("Matter of Alphabet Soup", ""),
            # Zero words after "Matter of" --> Punt.
            ("Matter of", "Matter of"),
            ("Simmons v. Stalder", "Simmons"),
            ("United States v. Donnell Hagood", ""),
            ("Kale v. United States INS", "Kale"),
            ("Cmk v. Department of Revenue Ex Rel. Kb", "Cmk"),
            ("State Farm Mut. Auto. Ins. Co. v. Barnes", "Barnes"),
            ("In Re Krp", "In Re Krp"),
            ("CH v. Department of Children and Families", "CH"),
            ("Com. v. Monosky", "Monosky"),
            ("JITNEY-JUNGLE, INCORPORATED v. City of Brookhaven", ""),
            ("Carolyn Humphrey v. Memorial Hospitals Association", ""),
            ("Wagner v. Sanders Associates, Inc.", "Wagner"),
            ("United States v. Venie (Arthur G.)", ""),
            ("Mitchell v. State", ""),
            ("City of Biloxi, Miss. v. Giuffrida", "Giuffrida"),
            ("Sexton v. St. Clair Federal Sav. Bank", "Sexton"),
            ("United States v. Matthews", "Matthews"),
            ("Freeman v. Freeman", "Freeman"),
            ("Spencer v. Toussaint", "Spencer"),
            ("In Re Canaday", "In Re Canaday"),
            ("Wenger v. Commission on Judicial Performance", "Wenger"),
            ("Jackson v. Janecka", "Janecka"),
            ("People of Michigan v. Ryan Christopher Smith", ""),
            ("Kincade (Michael) v. State", ""),
            ("Tonubbee v. River Parishes Guide", "Tonubbee"),
            ("United States v. Richiez", "Richiez"),
            ("In Re Allamaras", "In Re Allamaras"),
            ("United States v. Capoccia", "Capoccia"),
            ("Com. v. DeFranco", "DeFranco"),
            ("Matheny v. Porter", "Matheny"),
            ("Piper v. Hoffman", "Piper"),
            ("People v. Smith", ""),  # Punted b/c People and Smith are bad.
            ("Mobuary, Joseph v. State.", ""),  # Punted b/c "State." has punct
        ]
        tweaker = CaseNameTweaker()
        for t in test_pairs:
            output = tweaker.make_case_name_short(t[0])
            self.assertEqual(
                output,
                t[1],
                "Input was:\n\t%s\n\n\tExpected: '%s'\n\tActual: '%s'"
                % (t[0], t[1], output),
            )

    def test_quarter(self):
        answers = {
            1: 1,
            2: 1,
            3: 1,
            4: 2,
            5: 2,
            6: 2,
            7: 3,
            8: 3,
            9: 3,
            10: 4,
            11: 4,
            12: 4,
        }
        for month, q in answers.items():
            self.assertEqual(quarter(month), q)

    def test_is_first_month_in_quarter(self):
        answers = {
            1: True,
            2: False,
            3: False,
            4: True,
            5: False,
            6: False,
            7: True,
        }
        for month, is_first in answers.items():
            self.assertEqual(is_first_month_in_quarter(month), is_first)

    def test_harmonize_and_clean_string_tests(self):
        """Tests various inputs for the clean_string and harmonize functions"""
        test_pairs = [
            # Et al
            ["Lissner, et. al.", "Lissner"],
            ["Lissner, et. al", "Lissner"],
            ["Lissner, et al.", "Lissner"],
            ["Lissner, et al", "Lissner"],
            ["Lissner et. al.", "Lissner"],
            ["Lissner et. al", "Lissner"],
            ["Lissner et al.", "Lissner"],
            ["Lissner et al", "Lissner"],
            # US --> United States
            ["US v. Lissner, Plaintiff", "United States v. Lissner"],
            [
                "US v. Lissner, Petitioner-appellant",
                "United States v. Lissner",
            ],
            [
                "United States, Petitioner, v. Lissner",
                "United States v. Lissner",
            ],
            [
                "United States of America, Plaintiff-Appellee, v. Orlando B. "
                "Pino, Defendant-Appellant, Joseph",
                "United States v. Orlando B. Pino, Joseph",
            ],
            ["Herring v. U.S. **", "Herring v. United States"],
            ["Test v. U.S", "Test v. United States"],
            ["The United States v. Lissner", "United States v. Lissner"],
            # Make sure a match at the beginning of a string isn't trouble
            ["U.S. Coal Miners v. Test", "U.S. Coal Miners v. Test"],
            # Tests the output from a titlecased word containing
            # US to ensure it gets harmonized.
            ["Carver v. US", "Carver v. United States"],
            # US Steel --> US Steel
            ["US Steel v.  US", "US Steel v. United States"],
            ["US v. V.Vivack", "United States v. V.Vivack"],
            ["US vs. Lissner", "United States v. Lissner"],
            [
                "vs.boxer@gmail.com vs. USA",
                "vs.boxer@gmail.com v. United States",
            ],
            ["US v. US", "United States v. United States"],
            ["US  Steel v.  US", "US Steel v. United States"],
            ["U.S.A. v. Mr. v.", "United States v. Mr. v."],
            ["U.S.S. v. Lissner", "U.S.S. v. Lissner"],
            ["USC v. Lissner", "USC v. Lissner"],
            ["U.S.C. v. Lissner", "U.S.C. v. Lissner"],
            ["U.S. Steel v. Colgate", "U.S. Steel v. Colgate"],
            ["U.S.A. v. Lissner", "United States v. Lissner"],
            ["U.S. v. Lissner", "United States v. Lissner"],
            ["U. S. v. Lissner", "United States v. Lissner"],
            ["United States v. Lissner", "United States v. Lissner"],
            ["Usa v. Lissner", "United States v. Lissner"],
            ["USA v. Lissner", "United States v. Lissner"],
            [
                "United States of America v. Lissner",
                "United States v. Lissner",
            ],
            [
                "Lissner v. United States of America",
                "Lissner v. United States",
            ],
            # tests no period in v.
            ["USA v White", "United States v. White"],
            # tests no period in vs.
            ["USA vs White", "United States v. White"],
            [
                "V.Vivack and Associates v. US",
                "V.Vivack and Associates v. United States",
            ],
            [
                "v.v. Hendricks & Sons v. James v. Smith",
                "v.v. Hendricks & Sons v. James v. Smith",
            ],
            # tests upper-case VS.
            ["Lissner VS White", "Lissner v. White"],
            ["Lissner Vs White", "Lissner v. White"],
            ["Lissner VS. White", "Lissner v. White"],
            ["Lissner Vs. White", "Lissner v. White"],
            # Minimal normalization of "The State"
            ["Aimee v. The State", "Aimee v. State"],
            ["Aimee v. The State of Texas", "Aimee v. The State of Texas"],
            # Nuke Pet (short for petitioners)
            ["Commonwealth v. Mickle, V., Pet.", "Commonwealth v. Mickle, V."],
            # Unchanged, despite having the word Pet
            ["Pet Doctors inc. v. Spoon", "Pet Doctors inc. v. Spoon"],
            # Nukes the No. and Nos., but not
            ["No. 23423", "23423"],
            ["Nos. 23 and 232", "23 and 232"],
            ["No Expletives Inc.", "No Expletives Inc."],
            # Tests that "Nothing" doesn't get nuked.
            ["No. 232 Nothing 232", "232 Nothing 232"],
            # Garbage
            # leading slash.
            ["/USA vs White", "United States v. White"],
            # unicode input
            ["12–1438-cr", "12–1438-cr"],
            # Randoms
            ["clarinet alibi", "clarinet alibi"],
            ["papusa", "papusa"],
            ["CUSANO", "CUSANO"],
            # Filter out invalid XML characters
            [
                "Special Counsel ex rel. Karla Saunders",
                "Special Counsel ex rel. Karla Saunders",
            ],
        ]
        for pair in test_pairs:
            with self.subTest("Harmonize function", test=pair[0]):
                self.assertEqual(harmonize(clean_string(pair[0])), pair[1])

    def test_normalize_phrase(self):
        """Tests normalization of case titles."""
        test_pairs = [
            ["Commissioner v. Palin", "palin"],
            ["Commr v. Palin", "palin"],
            ["Comm'r v. Palin", "palin"],
            [
                "United States v. Learned Hand et. al.",
                "unitedstateslearnedhand",
            ],
            ["Baker, Plaintiff v. Palin, Defendant", "bakerpalin"],
        ]
        for pair in test_pairs:
            self.assertEqual(
                normalize_phrase(harmonize(clean_string(pair[0]))), pair[1]
            )

    def test_titlecase(self):
        """Tests various inputs for the titlecase function"""
        test_pairs = [
            [
                "Q&A with steve jobs: 'that's what happens in technology'",
                "Q&A With Steve Jobs: 'That's What Happens in Technology'",
            ],
            ["What is AT&T's problem?", "What is AT&T's Problem?"],
            [
                "Apple deal with AT&T falls through",
                "Apple Deal With AT&T Falls Through",
            ],
            ["this v that", "This v That"],
            ["this v. that", "This v. That"],
            ["this vs that", "This vs That"],
            ["this vs. that", "This vs. That"],
            [
                "The SEC's Apple Probe: What You Need to Know",
                "The SEC's Apple Probe: What You Need to Know",
            ],
            [
                "'by the Way, small word at the start but within quotes.'",
                "'By the Way, Small Word at the Start but Within Quotes.'",
            ],
            [
                "Small word at end is nothing to be afraid of",
                "Small Word at End is Nothing to Be Afraid Of",
            ],
            [
                "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
                "Starting Sub-Phrase With a Small Word: A Trick, Perhaps?",
            ],
            [
                "Sub-Phrase With a Small Word in Quotes: 'a Trick, Perhaps?'",
                "Sub-Phrase With a Small Word in Quotes: 'A Trick, Perhaps?'",
            ],
            [
                'Sub-Phrase With a Small Word in Quotes: "a Trick, Perhaps?"',
                'Sub-Phrase With a Small Word in Quotes: "A Trick, Perhaps?"',
            ],
            ['"Nothing to Be Afraid of?"', '"Nothing to Be Afraid Of?"'],
            ['"Nothing to be Afraid Of?"', '"Nothing to Be Afraid Of?"'],
            ["a thing", "A Thing"],
            [
                "2lmc Spool: 'gruber on OmniFocus and vapo(u)rware'",
                "2lmc Spool: 'Gruber on OmniFocus and Vapo(u)rware'",
            ],
            ["this is just an example.com", "This is Just an example.com"],
            [
                "this is something listed on del.icio.us",
                "This is Something Listed on del.icio.us",
            ],
            ["iTunes should be unmolested", "iTunes Should Be Unmolested"],
            [
                "Reading between the lines of steve jobs’s ‘thoughts on music’",
                # Tests unicode
                "Reading Between the Lines of Steve Jobs’s ‘Thoughts on Music’",
            ],
            [
                "seriously, ‘repair permissions’ is voodoo",  # Tests unicode
                "Seriously, ‘Repair Permissions’ is Voodoo",
            ],
            [
                "generalissimo francisco franco: still dead; kieren McCarthy: "
                "still a jackass",
                "Generalissimo Francisco Franco: Still Dead; Kieren McCarthy:"
                " Still a Jackass",
            ],
            [
                "Chapman v. u.s. Postal Service",
                "Chapman v. U.S. Postal Service",
            ],
            [
                "Spread Spectrum Screening Llc. v. Eastman Kodak Co.",
                "Spread Spectrum Screening LLC. v. Eastman Kodak Co.",
            ],
            [
                "Consolidated Edison Co. of New York, Inc. v. Entergy Nuclear "
                "Indian Point 2, Llc.",
                "Consolidated Edison Co. of New York, Inc. v. Entergy Nuclear"
                " Indian Point 2, LLC.",
            ],
            [
                "Infosint s.a. v. H. Lundbeck A/s",
                "Infosint S.A. v. H. Lundbeck A/S",
            ],
            [
                "KEVIN O'CONNELL v. KELLY HARRINGTON",
                "Kevin O'Connell v. Kelly Harrington",
            ],
            [
                "International Union of Painter v. J&r Flooring, Inc",
                "International Union of Painter v. J&R Flooring, Inc",
            ],
            [
                "DOROTHY L. BIERY, and JERRAMY and ERIN PANKRATZ v. THE UNITED"
                " STATES 07-693L And",
                "Dorothy L. Biery, and Jerramy and Erin Pankratz v. the "
                "United States 07-693l And",
            ],
            ["CARVER v. US", "Carver v. US"],
        ]

        for pair in test_pairs:
            unicode_string = force_unicode(pair[0])
            self.assertEqual(titlecase(unicode_string, DEBUG=False), pair[1])

    def test_fixing_camel_case(self):
        """Can we correctly identify and fix camelCase?"""
        test_pairs = (
            # A nasty one with a v in the middle and two uppercase letters
            ("Metropolitanv.PAPublic", "Metropolitan v. PA Public"),
            # An OK string.
            (
                "In Re Avandia Marketing Sales Practices & Products Liability "
                "Litigation",
                "In Re Avandia Marketing Sales Practices & Products Liability "
                "Litigation",
            ),
            # Partial camelCase should be untouched.
            (
                "PPL EnergyPlus, LLC, et al v. Solomon, et al",
                "PPL EnergyPlus, LLC, et al v. Solomon, et al",
            ),
            # The v. has issues.
            ("Pagliaccettiv.Kerestes", "Pagliaccetti v. Kerestes"),
            ("Coxv.Hornetal", "Cox v. Horn"),
            ("InReNortelNetworksInc", "In Re Nortel Networks Inc"),
            # Testing with a Mc.
            ("McLaughlinv.Hallinan", "McLaughlin v. Hallinan"),
            # Ends with uppercase letter
            ("TourchinvAttyGenUSA", "Tourchin v. Atty Gen USA"),
            ("USAv.Brown", "USA v. Brown"),
            # Fix 'of', ',etal', 'the', and 'Inre' problems
            (
                "RawdinvTheAmericanBrdofPediatrics",
                "Rawdin v. The American Brd of Pediatrics",
            ),
            (
                "Santomenno,etalv.JohnHancockLifeInsuranceCompany,etal",
                "Santomenno v. John Hancock Life Insurance Company",
            ),
            ("BaughvSecretaryoftheNavy", "Baugh v. Secretary of the Navy"),
            ("Smallv.CamdenCountyetal", "Small v. Camden County"),
            ("InreSCHCorpv.CFIClass", "In Re SCH Corp v. CFI Class"),
        )
        for pair in test_pairs:
            self.assertEqual(pair[1], fix_camel_case(pair[0]))

    def test_split_date_range_string(self):
        tests = {
            "October - December 2016": convert_date_string(
                "November 16, 2016"
            ),
            "July - September 2016": convert_date_string("August 16, 2016"),
            "April - June 2016": convert_date_string("May 16, 2016"),
            "January March 2016": False,
        }
        for before, after in tests.items():
            if after:
                self.assertEqual(split_date_range_string(before), after)
            else:
                with self.assertRaises(Exception) as cm:
                    split_date_range_string(before)

                assert cm.exception.args[0].startswith(
                    "Unrecognized date format:"
                )

    def test_normalize_dashes(self):
        tests = [
            # copied from http://www.w3schools.com/charsets/ref_utf_punctuation.asp
            " this is    –a test–",  # en dash
            " this is    —a test—",  # em dash
            " this is    ‐a test‐",  # hyphen
            " this is    ‑a test‑",  # non-breaking hyphen
            " this is    ‒a test‒",  # figure dash
            " this is    ―a test―",  # horizontal bar
        ]
        target = " this is    -a test-"
        for test in tests:
            self.assertEqual(normalize_dashes(test), target)
