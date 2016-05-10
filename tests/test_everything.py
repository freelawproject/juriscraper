#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import glob
import logging
import time
import unittest
import datetime

sys.path.insert(0, os.path.abspath('..'))

from juriscraper.lib.importer import build_module_list
from juriscraper.lib.date_utils import parse_dates, quarter, \
    is_first_month_in_quarter
from juriscraper.lib.string_utils import (
    clean_string, fix_camel_case, force_unicode, harmonize, titlecase,
    CaseNameTweaker,
)
from juriscraper.opinions.united_states.state import massappct, pa, mass, nh, \
    colo
from juriscraper.oral_args.united_states.federal_appellate import ca6

class SlownessException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class DateParserTest(unittest.TestCase):
    def test_various_date_extractions(self):
        test_pairs = (
            # Dates separated by semicolons and JUMP words
            ('February 5, 1980; March 14, 1980 and May 28, 1980.',
             [datetime.datetime(1980, 2, 5, 0, 0),
              datetime.datetime(1980, 3, 14, 0, 0),
              datetime.datetime(1980, 5, 28, 0, 0)]),
            # Misspelled month value.
            ('Febraury 17, 1945',
             [datetime.datetime(1945, 2, 17, 0, 0)]),
            ('Sepetmber 19 1924',
             [datetime.datetime(1924, 9, 19)]),
            # Using 'Term' as an indicator.
            ('November Term 2004.',
             [datetime.datetime(2004, 11, 01)]),
            (u'April 26, 1961.[†]',
             [datetime.datetime(1961, 4, 26)]),
        )
        for pair in test_pairs:
            dates = parse_dates(pair[0])
            self.assertEqual(dates, pair[1])


class ScraperExampleTest(unittest.TestCase):
    def setUp(self):
        # Change the working directory to that of the script
        abs_path = os.path.abspath(__file__)
        dir_name = os.path.dirname(abs_path)
        os.chdir('%s/../..' % dir_name)

        # Disable logging
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        # Re-enable logging
        logging.disable(logging.NOTSET)

    def test_scrape_all_example_files(self):
        """Finds all the $module_example* files and tests them with the sample
        scraper.
        """

        module_strings = build_module_list('juriscraper')
        num_scrapers = len([s for s in module_strings
                            if 'backscraper' not in s])
        print "Testing {count} scrapers against their example files:".format(
            count=num_scrapers)
        max_len_mod_string = max(len(mod) for mod in module_strings
                                 if 'backscraper' not in mod) + 2
        num_example_files = 0
        num_warnings = 0
        cnt = CaseNameTweaker()
        for module_string in module_strings:
            package, module = module_string.rsplit('.', 1)
            mod = __import__("%s.%s" % (package, module),
                             globals(),
                             locals(),
                             [module])
            if 'backscraper' not in module_string:
                sys.stdout.write(
                    '  %s ' % module_string.ljust(max_len_mod_string)
                )
                sys.stdout.flush()
                # module_parts:
                # [0]  - "juriscraper"
                # [1]  - "opinions" or "oral_args"
                # ...  - rest of the path
                # [-1] - module name
                module_parts = module_string.split('.')
                example_path = os.path.join(
                    "juriscraper", "tests", "examples", module_parts[1],
                    "united_states", module_parts[-1],
                )
                paths = glob.glob('%s_example*' % example_path)
                self.assertTrue(
                    paths,
                    "No example file found for: %s! \n\nThe test looked in: "
                    "%s" % (
                        module_string.rsplit('.', 1)[1],
                        os.path.join(os.getcwd(), example_path),
                    ))
                num_example_files += len(paths)
                t1 = time.time()
                num_tests = len(paths)
                for path in paths:
                    # This loop allows multiple example files per module
                    if path.endswith('~'):
                        # Text editor backup: Not interesting.
                        continue
                    site = mod.Site(cnt=cnt)
                    site.url = path
                    # Forces a local GET
                    site.method = 'LOCAL'
                    site.parse()
                t2 = time.time()

                max_speed = 10
                warn_speed = 1
                speed = t2 - t1
                msg = ''
                if speed > max_speed:
                    if sys.gettrace() is None:
                        # Only do this if we're not debugging. Debuggers make
                        # things slower and breakpoints make things stop.
                        raise SlownessException(
                            "This scraper took {speed}s to test, which is more "
                            "than the allowed speed of {max_speed}s. "
                            "Please speed it up for tests to pass.".format(
                                speed=speed,
                                max_speed=max_speed,
                            ))
                elif speed > warn_speed:
                    msg = ' - WARNING: SLOW SCRAPER'
                    num_warnings += 1
                else:
                    msg = ''

                print '(%s test(s) in %0.1f seconds%s)' % (
                    num_tests, speed, msg
                )

        print ("\n{num_scrapers} scrapers tested successfully against "
               "{num_example_files} example files, with {num_warnings} "
               "speed warnings.".format(
            num_scrapers=num_scrapers,
            num_example_files=num_example_files,
            num_warnings=num_warnings,
        ))
        if num_warnings:
            print ("\nAt least one speed warning was triggered during the "
                   "tests. If this is due to a slow scraper you wrote, we "
                   "suggest attempting to speed it up, as it will be slow "
                   "both in production and while running tests. This is "
                   "currently a warning, but may raise a failure in the "
                   "future as performance requirements are tightened.")
        else:
            # Someday, this line of code will be run. That day is not today.
            print "\nNo speed warnings detected. That's great, keep up the " \
                  "good work!"


class StringUtilTest(unittest.TestCase):
    def test_make_short_name(self):
        test_pairs = [
            # In re and Matter of
            ('In re Lissner', 'In re Lissner'),
            ('Matter of Lissner', 'In re Lissner'),

            # Plaintiff is in bad word list
            ('State v. Lissner', 'Lissner'),
            ('People v. Lissner', 'Lissner'),
            ('California v. Lissner', 'Lissner'),
            ('Dallas v. Lissner', 'Lissner'),

            # Basic 3-word case
            ('Langley v. Google', 'Langley'),
            # Similar to above, but more than 3 words
            ('Langley v. Google foo', 'Langley'),

            # United States v. ...
            ('United States v. Lissner', 'Lissner'),

            # Corporate first name
            ('Google, Inc. v. Langley', 'Langley'),
            ('Special, LLC v. Langley', 'Langley'),
            ('Google Corp. v. Langley', 'Langley'),

            # Shorter appellant than plaintiff
            ('Michael Lissner v. Langley', 'Langley'),

            # Multi-v with and w/o a bad_word
            ('Alameda v. Victor v. Keyboard', ''),
            ('Bloggers v. Victor v. Keyboard', ''),

            # Long left, short right
            ('Many words here v. Langley', 'Langley'),

            # Other manually added items
            ('Ilarion v. State', 'Ilarion'),
            ('Imery v. Vangil Ingenieros', 'Imery'),

            # Many more tests from real data!
            ('Bean v. City of Monahans', 'Bean'),
            ('Blanke v. Time, Inc.', 'Blanke'),
            ('New York Life Ins. Co. v. Deshotel', 'Deshotel'),
            ('Deatherage v. Deatherage', 'Deatherage'),
            ('Gonzalez Vargas v. Holder', ''),
            ('Campbell v. Wainwright', 'Campbell'),
            ('Liggett & Myers Tobacco Co. v. Finzer', 'Finzer'),
            ('United States v. Brenes', 'Brenes'),
            ('A.H. Robins Co., Inc. v. Eli Lilly & Co', ''),
            ('McKellar v. Hazen', 'McKellar'),
            ('Gil v. State', 'Gil'),
            ('Fuentes v. Owen', 'Fuentes'),
            ('State v. Shearer', 'Shearer'),
            ('United States v. Smither', 'Smither'),
            ('People v. Bradbury', 'Bradbury'),
            ('Venable (James) v. State', ''),
            ('Burkhardt v. Bailey', 'Burkhardt'),
            ('DeLorenzo v. Bales', 'DeLorenzo'),
            ('Loucks v. Bauman', 'Loucks'),
            ('Kenneth Stern v. Robert Weinstein', ''),
            ('Rayner v. Secretary of Health and Human Services', 'Rayner'),
            ('Rhyne v. Martin', 'Rhyne'),
            ('State v. Wolverton', 'Wolverton'),
            ('State v. Flood', 'Flood'),
            ('Amason v. Natural Gas Pipeline Co.', 'Amason'),
            ('United States v. Bryant', 'Bryant'),
            ('WELLS FARGO BANK v. APACHE TRIBE OF OKLAHOMA', ''),
            ('Stewart v. Tupperware Corp.', 'Stewart'),
            ('Society of New York Hosp. v. ASSOCIATED HOSP. SERV. OF NY', ''),
            ('Stein v. State Tax Commission', 'Stein'),
            (
                'The Putnam Pit, Inc. Geoffrey Davidian v. City of Cookeville, Tennessee Jim Shipley',
                ''),
            ('People v. Armstrong', 'Armstrong'),
            ('Weeks v. Weeks', 'Weeks'),
            ('Smith v. Xerox Corp.', ''),
            ('In Interest of Ad', ''),
            ('People v. Forsyth', 'Forsyth'),
            ('State v. LeClair', 'LeClair'),
            ('Agristor Credit Corp. v. Unruh', 'Unruh'),
            ('United States v. Larry L. Stewart', ''),
            ('Starling v. United States', 'Starling'),
            ('United States v. Pablo Colin-Molina', ''),
            ('Kenneth N. Juhl v. The United States', ''),
            ('Matter of Wilson', 'In re Wilson'),
            ('In Re Damon H.', 'In Re Damon H.'),
            ('Centennial Ins. Co. v. Zylberberg', 'Zylberberg'),
            ('United States v. Donald Lee Stotler', ''),
            ('Byndloss v. State', 'Byndloss'),
            ('People v. Piatkowski', 'Piatkowski'),
            ('United States v. Willie James Morgan', ''),
            ('Harbison (Debra) v. Thieret (James)', ''),
            ('Federal Land Bank of Columbia v. Lieben', 'Lieben'),
            ('John Willard Greywind v. John T. Podrebarac', ''),
            ('State v. Powell', 'Powell'),
            ('Carr v. Galloway', 'Carr'),
            ('Saylors v. State', 'Saylors'),
            ('Jones v. Franke', 'Jones'),
            ('In Re Robert L. Mills, Debtor. Robert L. Mills v. Sdrawde '
             'Titleholders, Inc., a California Corporation', ''),
            ('Pollenex Corporation v. Sunbeam-Home Comfort, a Division of '
             'Sunbeam Corp., Raymond Industrial, Limited and Raymond Marketing '
             'Corporation of North America', ''),
            ('Longs v. State', 'Longs'),
            ('Performance Network Solutions v. Cyberklix', 'Cyberklix'),
            ('DiSabatino v. Salicete', 'DiSabatino'),
            ('State v. Jennifer Nicole Jackson', ''),
            ('United States v. Moreno', 'Moreno'),
            ('LOGAN & KANAWHA COAL v. Banque Francaise', ''),
            ('State v. Harrison', 'Harrison'),
            ('Efford v. Milam', 'Efford'),
            ('People v. Thompson', 'Thompson'),
            ('CINCINNATI THERMAL SPRAY v. Pender County', ''),
            ('JAH Ex Rel. RMH v. Wadle & Associates', ''),
            ('United Pub. Employees v. CITY & CTY. OF SAN FRAN.', ''),
            ('Warren v. Massachusetts Indemnity', 'Warren'),
            ('Marion Edwards v. State Farm Insurance Company and "John Doe,"',
             ''),
            ('Snowdon v. Grillo', 'Snowdon'),
            ('Adam Lunsford v. Cravens Funeral Home', ''),
            ('State v. Dillon', 'Dillon'),
            ('In Re Graham', 'In Re Graham'),
            ('Durham v. Chrysler Corp.', ''),  # Fails b/c Durham is a city!
            ('Carolyn Warrick v. Motiva Enterprises, L.L.C', ''),
            ('United States v. Aloi', 'Aloi'),
            ('United States Fidelity & Guaranty v. Graham', 'Graham'),
            ('Wildberger v. Rosenbaum', 'Wildberger'),
            ('Truck Insurance Exchange v. Michling', 'Michling'),
            ('Black Voters v. John J. McDonough', ''),
            ('State of Tennessee v. William F. Cain', ''),
            ('Robert J. Imbrogno v. Defense Logistics Agency', ''),
            ('Leetta Beachum, Administratrix v. Timothy Joseph White', ''),
            ('United States v. Jorge Gonzalez-Villegas', ''),
            ('Pitts v. Florida Bd. of Bar Examiners', 'Pitts'),
            ('State v. Pastushin', 'Pastushin'),
            ('Clark v. Clark', ''),
            ('Barrios v. Holder', 'Barrios'),
            ('Gregory L. Lavin v. United States', ''),
            ('Carpenter v. Consumers Power', 'Carpenter'),
            ('Derbabian v. S & C SNOWPLOWING, INC.', 'Derbabian'),
            ('Bright v. LSI CORP.', 'Bright'),
            ('State v. Brown', 'Brown'),
            ('KENNEY v. Keebler Co.', 'KENNEY'),
            ('Hill v. Chalanor', 'Hill'),
            ('Washington v. New Jersey', ''),
            ('Sollek v. Laseter', 'Sollek'),
            ('United States v. John Handy Jones, International Fidelity '
             'Insurance Company', ''),
            ('N.L.R.B. v. I. W. Corp', ''),
            ('Karpisek v. Cather & Sons Construction, Inc.', 'Karpisek'),
            ('Com. v. Wade', 'Com.'),
            ('Glascock v. Sukumlyn', 'Glascock'),
            ('Burroughs v. Hills', 'Burroughs'),
            ('State v. Darren Matthew Lee', ''),
            ('Mastondrea v. Occidental Hotels Management', 'Mastondrea'),
            ('Kent v. C. I. R', 'Kent'),
            ('Johnson v. City of Detroit', ''),
            ('Nolan v. United States', 'Nolan'),
            ('Currence v. Denver Tramway Corporation', 'Currence'),
            ('Matter of Cano', 'In re Cano'),
            ('Simmons v. Stalder', 'Simmons'),
            ('United States v. Donnell Hagood', ''),
            ('Kale v. United States INS', 'Kale'),
            ('Cmk v. Department of Revenue Ex Rel. Kb', 'Cmk'),
            ('State Farm Mut. Auto. Ins. Co. v. Barnes', 'Barnes'),
            ('In Re Krp', 'In Re Krp'),
            ('CH v. Department of Children and Families', 'CH'),
            ('Com. v. Monosky', 'Com.'),
            ('JITNEY-JUNGLE, INCORPORATED v. City of Brookhaven', ''),
            ('Carolyn Humphrey v. Memorial Hospitals Association', ''),
            ('Wagner v. Sanders Associates, Inc.', 'Wagner'),
            ('United States v. Venie (Arthur G.)', ''),
            ('Mitchell v. State', ''),
            ('City of Biloxi, Miss. v. Giuffrida', 'Giuffrida'),
            ('Sexton v. St. Clair Federal Sav. Bank', 'Sexton'),
            ('United States v. Matthews', 'Matthews'),
            ('Freeman v. Freeman', 'Freeman'),
            ('Spencer v. Toussaint', 'Spencer'),
            ('In Re Canaday', 'In Re Canaday'),
            ('Wenger v. Commission on Judicial Performance', 'Wenger'),
            ('Jackson v. Janecka', 'Janecka'),
            ('People of Michigan v. Ryan Christopher Smith', ''),
            ('Kincade (Michael) v. State', ''),
            ('Tonubbee v. River Parishes Guide', 'Tonubbee'),
            ('United States v. Richiez', 'Richiez'),
            ('In Re Allamaras', 'In Re Allamaras'),
            ('United States v. Capoccia', 'Capoccia'),
            ('Com. v. DeFranco', 'Com.'),
            ('Matheny v. Porter', 'Matheny'),
            ('Piper v. Hoffman', 'Piper'),
            ('People v. Smith', ''),  # Punted b/c People and Smith are bad.
        ]
        tweaker = CaseNameTweaker()
        for t in test_pairs:
            output = tweaker.make_case_name_short(t[0])
            self.assertEqual(output, t[1],
                             "Input was:\n\t%s\n\n\tExpected: '%s'\n\tActual: '%s'" %
                             (t[0], t[1], output))

    def test_quarter(self):
        answers = {1: 1, 2: 1, 3: 1, 4: 2, 5: 2, 6: 2, 7: 3, 8: 3, 9: 3, 10: 4,
                   11: 4, 12: 4}
        for month, q in answers.iteritems():
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
        for month, is_first in answers.iteritems():
            self.assertEqual(is_first_month_in_quarter(month), is_first)

    def test_harmonize_and_clean_string_tests(self):
        """Tests various inputs for the clean_string and harmonize functions"""
        test_pairs = [
            # Et al
            ['Lissner, et. al.',
             u'Lissner'],
            ['Lissner, et. al',
             u'Lissner'],
            ['Lissner, et al.',
             u'Lissner'],
            ['Lissner, et al',
             u'Lissner'],
            ['Lissner et. al.',
             u'Lissner'],
            ['Lissner et. al',
             u'Lissner'],
            ['Lissner et al.',
             u'Lissner'],
            ['Lissner et al',
             u'Lissner'],

            # US --> United States
            ['US v. Lissner, Plaintiff',
             u'United States v. Lissner'],
            ['US v. Lissner, Petitioner-appellant',
             u'United States v. Lissner'],
            ['United States, Petitioner, v. Lissner',
             u'United States v. Lissner'],
            [
                'United States of America, Plaintiff-Appellee, v. Orlando B. '
                'Pino, Defendant-Appellant, Joseph',
                u'United States v. Orlando B. Pino, Joseph'],
            ['Herring v. U.S. **',
             u'Herring v. United States'],
            ['Test v. U.S',
             u'Test v. United States'],
            ['The United States v. Lissner',
             u'United States v. Lissner'],
            # Tests the output from a titlecased word containing
            # US to ensure it gets harmonized.
            ['Carver v. US',
             u'Carver v. United States'],
            # US Steel --> US Steel
            ['US Steel v.  US',
             u'US Steel v. United States'],
            ['US v. V.Vivack',
             u'United States v. V.Vivack'],
            ['US vs. Lissner',
             u'United States v. Lissner'],
            ['vs.boxer@gmail.com vs. USA',
             u'vs.boxer@gmail.com v. United States'],
            ['US v. US',
             u'United States v. United States'],
            ['US  Steel v.  US',
             u'US Steel v. United States'],
            ['U.S.A. v. Mr. v.',
             u'United States v. Mr. v.'],
            ['U.S.S. v. Lissner',
             u'U.S.S. v. Lissner'],
            ['USC v. Lissner',
             u'USC v. Lissner'],
            ['U.S.C. v. Lissner',
             u'U.S.C. v. Lissner'],
            ['U.S. Steel v. Colgate',
             u'U.S. Steel v. Colgate'],
            ['U.S.A. v. Lissner',
             u'United States v. Lissner'],
            ['U.S. v. Lissner',
             u'United States v. Lissner'],
            ['U. S. v. Lissner',
             u'United States v. Lissner'],
            ['United States v. Lissner',
             u'United States v. Lissner'],
            ['Usa v. Lissner',
             u'United States v. Lissner'],
            ['USA v. Lissner',
             u'United States v. Lissner'],
            ['United States of America v. Lissner',
             u'United States v. Lissner'],
            ['Lissner v. United States of America',
             u'Lissner v. United States'],

            # tests no period in v.
            ['USA v White',
             u'United States v. White'],
            # tests no period in vs.
            ['USA vs White',
             u'United States v. White'],
            ['V.Vivack and Associates v. US',
             u'V.Vivack and Associates v. United States'],
            ['v.v. Hendricks & Sons v. James v. Smith',
             u'v.v. Hendricks & Sons v. James v. Smith'],

            # Normalize "The State"
            ['Aimee v. The State',
             u'Aimee v. State'],

            # Nuke Pet (short for petitioners)
            ['Commonwealth v. Mickle, V., Pet.',
             u'Commonwealth v. Mickle v.'],
            # Unchanged, despite having the word Pet
            ['Pet Doctors inc. v. Spoon',
             u'Pet Doctors inc. v. Spoon'],

            # Nukes the No. and Nos., but not
            ['No. 23423',
             u'23423'],
            ['Nos. 23 and 232',
             u'23 and 232'],
            ['No Expletives Inc.',
             u'No Expletives Inc.'],
            # Tests that "Nothing" doesn't get nuked.
            ['No. 232 Nothing 232',
             '232 Nothing 232'],

            # Garbage
            # leading slash.
            ['/USA vs White',
             u'United States v. White'],
            # unicode input
            ['12–1438-cr',
             u'12–1438-cr'],

            # Randoms
            ['clarinet alibi',
             u'clarinet alibi'],
            ['papusa',
             u'papusa'],
            ['CUSANO',
             u'CUSANO'],

             # Filter out invalid XML characters
             [u'Special Counsel ex rel. Karla Saunders',
              u'Special Counsel ex rel. Karla Saunders'],
        ]
        for pair in test_pairs:
            self.assertEqual(harmonize(clean_string(pair[0])), pair[1])

    def test_titlecase(self):
        """Tests various inputs for the titlecase function"""
        test_pairs = [
            ["Q&A with steve jobs: 'that's what happens in technology'",
             u"Q&A With Steve Jobs: 'That's What Happens in Technology'"],
            ["What is AT&T's problem?",
             u"What is AT&T's Problem?"],
            ['Apple deal with AT&T falls through',
             u'Apple Deal With AT&T Falls Through'],
            ['this v that',
             u'This v That'],
            ['this v. that',
             u'This v. That'],
            ['this vs that',
             u'This vs That'],
            ['this vs. that',
             u'This vs. That'],
            ["The SEC's Apple Probe: What You Need to Know",
             u"The SEC's Apple Probe: What You Need to Know"],
            ["'by the Way, small word at the start but within quotes.'",
             u"'By the Way, Small Word at the Start but Within Quotes.'"],
            ['Small word at end is nothing to be afraid of',
             u'Small Word at End is Nothing to Be Afraid Of'],
            ['Starting Sub-Phrase With a Small Word: a Trick, Perhaps?',
             u'Starting Sub-Phrase With a Small Word: A Trick, Perhaps?'],
            ["Sub-Phrase With a Small Word in Quotes: 'a Trick, Perhaps?'",
             u"Sub-Phrase With a Small Word in Quotes: 'A Trick, Perhaps?'"],
            ['Sub-Phrase With a Small Word in Quotes: "a Trick, Perhaps?"',
             u'Sub-Phrase With a Small Word in Quotes: "A Trick, Perhaps?"'],
            ['"Nothing to Be Afraid of?"',
             u'"Nothing to Be Afraid Of?"'],
            ['"Nothing to be Afraid Of?"',
             u'"Nothing to Be Afraid Of?"'],
            ['a thing',
             u'A Thing'],
            ["2lmc Spool: 'gruber on OmniFocus and vapo(u)rware'",
             u"2lmc Spool: 'Gruber on OmniFocus and Vapo(u)rware'"],
            ['this is just an example.com',
             u'This is Just an example.com'],
            ['this is something listed on del.icio.us',
             u'This is Something Listed on del.icio.us'],
            ['iTunes should be unmolested',
             u'iTunes Should Be Unmolested'],
            ['Reading between the lines of steve jobs’s ‘thoughts on music’',
             # Tests unicode
             u'Reading Between the Lines of Steve Jobs’s ‘thoughts on Music’'],
            ['seriously, ‘repair permissions’ is voodoo',  # Tests unicode
             u'Seriously, ‘repair Permissions’ is Voodoo'],
            [
                'generalissimo francisco franco: still dead; kieren McCarthy: '
                'still a jackass',
                u'Generalissimo Francisco Franco: Still Dead; Kieren McCarthy:'
                u' Still a Jackass'],
            ['Chapman v. u.s. Postal Service',
             u'Chapman v. U.S. Postal Service'],
            ['Spread Spectrum Screening Llc. v. Eastman Kodak Co.',
             u'Spread Spectrum Screening LLC. v. Eastman Kodak Co.'],
            [
                'Consolidated Edison Co. of New York, Inc. v. Entergy Nuclear '
                'Indian Point 2, Llc.',
                u'Consolidated Edison Co. of New York, Inc. v. Entergy Nuclear'
                u' Indian Point 2, LLC.'],
            ['Infosint s.a. v. H. Lundbeck A/s',
             u'Infosint S.A. v. H. Lundbeck A/S'],
            ["KEVIN O'CONNELL v. KELLY HARRINGTON",
             u"Kevin O'Connell v. Kelly Harrington"],
            ['International Union of Painter v. J&r Flooring, Inc',
             u'International Union of Painter v. J&R Flooring, Inc'],
            [
                'DOROTHY L. BIERY, and JERRAMY and ERIN PANKRATZ v. THE UNITED'
                ' STATES 07-693L And',
                u'Dorothy L. Biery, and Jerramy and Erin Pankratz v. the '
                u'United States 07-693l And'],
            ['CARVER v. US',
             u'Carver v. US']]
        for pair in test_pairs:
            self.assertEqual(titlecase(force_unicode(pair[0])),
                             pair[1])

    def test_fixing_camel_case(self):
        """Can we correctly identify and fix camelCase?"""
        test_pairs = (
            # A nasty one with a v in the middle and two uppercase letters
            ('Metropolitanv.PAPublic',
             'Metropolitan v. PA Public'),
            # An OK string.
            (
                'In Re Avandia Marketing Sales Practices & Products Liability '
                'Litigation',
                'In Re Avandia Marketing Sales Practices & Products Liability '
                'Litigation'),
            # Partial camelCase should be untouched.
            ('PPL EnergyPlus, LLC, et al v. Solomon, et al',
             'PPL EnergyPlus, LLC, et al v. Solomon, et al'),
            # The v. has issues.
            ('Pagliaccettiv.Kerestes',
             'Pagliaccetti v. Kerestes'),
            ('Coxv.Hornetal',
             'Cox v. Horn'),
            ('InReNortelNetworksInc',
             'In Re Nortel Networks Inc'),
            # Testing with a Mc.
            ('McLaughlinv.Hallinan',
             'McLaughlin v. Hallinan'),
            # Ends with uppercase letter
            ('TourchinvAttyGenUSA',
             'Tourchin v. Atty Gen USA'),
            ('USAv.Brown',
             'USA v. Brown'),
            # Fix 'of', ',etal', 'the', and 'Inre' problems
            ('RawdinvTheAmericanBrdofPediatrics',
             'Rawdin v. The American Brd of Pediatrics'),
            ('Santomenno,etalv.JohnHancockLifeInsuranceCompany,etal',
             'Santomenno v. John Hancock Life Insurance Company'),
            ('BaughvSecretaryoftheNavy',
             'Baugh v. Secretary of the Navy'),
            ('Smallv.CamdenCountyetal',
             'Small v. Camden County'),
            ('InreSCHCorpv.CFIClass',
             'In Re SCH Corp v. CFI Class'),
        )
        for pair in test_pairs:
            self.assertEqual(pair[1], fix_camel_case(pair[0]))


class ScraperSpotTest(unittest.TestCase):
    """Adds specific tests to specific courts that are more-easily tested
    without a full integration test.
    """

    def test_colo(self):
        strings = (
            '2015 COA 101. No. 10CA2481. People v. DeGreat.',
            '2015 COA 102. No. 12CA1589. People v. Froehler.',
        )
        attrs = (
            'docket_numbers',
            'case_names',
            'neutral_citations'
        )
        site = colo.Site()
        for s in strings:
            for attr in attrs:
                try:
                    site.title_regex.search(s).group(attr)
                except AttributeError:
                    self.fail("Unable to parse string: '{s}'".format(s=s))

    def test_mass(self):
        strings = {
            'Massachusetts State Automobile Dealers Association, Inc. v. Tesla Motors MA, Inc. (SJC 11545) (September 15, 2014)': [
                'Massachusetts State Automobile Dealers Association, Inc. v. Tesla Motors MA, Inc.',
                'SJC 11545',
                'September 15, 2014',
            ],
            'Bower v. Bournay-Bower (SJC 11478) (September 15, 2014)': [
                'Bower v. Bournay-Bower',
                'SJC 11478',
                'September 15, 2014',
            ],
            'Commonwealth v. Holmes (SJC 11557) (September 12, 2014)': [
                'Commonwealth v. Holmes',
                'SJC 11557',
                'September 12, 2014',
            ],
            'Superintendent-Director of Assabet Valley Regional School District v. Speicher (SJC 11563) (September 11, 2014)': [
                'Superintendent-Director of Assabet Valley Regional School District v. Speicher',
                'SJC 11563',
                'September 11, 2014',
            ],
            'Commonwealth v. Quinn (SJC 11554) (September 11, 2014)': [
                'Commonwealth v. Quinn',
                'SJC 11554',
                'September 11, 2014',
            ],
            'Commonwealth v. Wall (SJC 09850) (September 11, 2014)': [
                'Commonwealth v. Wall',
                'SJC 09850',
                'September 11, 2014',
            ],
            'Commonwealth v. Letkowski (SJC 11556) (September 9, 2014)': [
                'Commonwealth v. Letkowski',
                'SJC 11556',
                'September 9, 2014',
            ],
            'Commonwealth v. Sullivan (SJC 11568) (September 9, 2014)': [
                'Commonwealth v. Sullivan',
                'SJC 11568',
                'September 9, 2014',
            ],
            'Plumb v. Casey (SJC 11519) (September 8, 2014)': [
                'Plumb v. Casey',
                'SJC 11519',
                'September 8, 2014',
            ],
            'A.J. Properties, LLC v. Stanley Black and Decker, Inc. (SJC 11424) (September 5, 2014)': [
                'A.J. Properties, LLC v. Stanley Black and Decker, Inc.',
                'SJC 11424',
                'September 5, 2014',
            ],
            'Massachusetts Electric Co. v. Department of Public Utilities (SJC 11526, 11527, 11528) (September 4, 2014)': [
                'Massachusetts Electric Co. v. Department of Public Utilities',
                'SJC 11526, 11527, 11528',
                'September 4, 2014',
            ],
            'Commonwealth v. Doe (SJC-11861) (October 22, 2015)': [
                'Commonwealth v. Doe',
                'SJC-11861',
                'October 22, 2015',
            ],
        }
        site = mass.Site()
        for k, v in strings.items():
            try:
                self.assertEqual(
                    site.grouping_regex.search(k).group(1).strip(),
                    v[0],
                )
                self.assertEqual(
                    site.grouping_regex.search(k).group(2).strip(),
                    v[1],
                )
                self.assertEqual(
                    site.grouping_regex.search(k).group(3).strip(),
                    v[2],
                )
            except AttributeError:
                self.fail("Unable to parse mass string: '{s}'".format(s=k))

    def test_massappct(self):
        strings = (
            'Commonwealth v. Forbes (AC 13-P-730) (August 26, 2014)',
            'Commonwealth v. Malick (AC 09-P-1292, 11-P-0973) (August 25, 2014)',
            'Litchfield\'s Case (AC 13-P-1044) (August 28, 2014)',
            'Rose v. Highway Equipment Company (AC 13-P-1215) (August 27, 2014)',
            'Commonwealth v. Alves (AC 13-P-1183) (August 27, 2014)',
            'Commonwealth v. Forbes (AC 13-P-730) (August 26, 2014)',
            'Commonwealth v. Malick (AC 09-P-1292, 11-P-0973) (August 25, 2014)',
            'Commonwealth v. Dale (AC 12-P-1909) (August 25, 2014)',
            'Kewley v. Department of Elementary and Secondary Education (AC 13-P-0833) (August 22, 2014)',
            'Hazel\'s Cup & Saucer, LLC v. Around The Globe Travel, Inc. (AC 13-P-1371) (August 22, 2014)',
            'Becker v. Phelps (AC 13-P-0951) (August 22, 2014)',
            'Barrow v. Dartmouth House Nursing Home, Inc. (AC 13-P-1375) (August 18, 2014)',
            'Zimmerling v. Affinity Financial Corp. (AC 13-P-1439) (August 18, 2014)',
            'Lowell v. Talcott (AC 13-P-1053) (August 18, 2014)',
        )

        site = massappct.Site()
        for s in strings:
            try:
                site.grouping_regex.search(s).group(3)
            except AttributeError:
                self.fail(
                    "Unable to parse massctapp string: '{s}'".format(s=s))

    def test_pa(self):
        """Ensures our regex parses what we think it can, and fails otherwise.
        """
        string_pairs = (
            ("In Re: Reaccreditation of the American Board of Certification as"
             " a Certifying Organization for Consumer Bankruptcy, Creditors' "
             "Rights and Business Bankruptcy",
             False),
            ("Commonwealth v. Brown, M., Pet - No. 176 WAL 2014",
             True),
        )
        site = pa.Site()
        for s, expectation in string_pairs:
            try:
                site._return_case_name(s)
                outcome = True
            except:
                outcome = False
            self.assertEqual(
                expectation,
                outcome,
                msg="Did not get expected result ({expectation}) when parsing "
                    "string in 'pa' test. Instead got: {outcome}".format(
                    expectation=expectation,
                    outcome=outcome,
                )
            )

    def test_nh(self):
        """Ensures regex parses what we think it should."""
        string_pairs = (
            ('2012-644, State of New Hampshire v. Adam Mueller',
             'State of New Hampshire v. Adam Mueller',),
            ('2012-920, In re Trevor G.',
             'In re Trevor G.',),
            ('2012-313, State of New Hampshire v. John A. Smith',
             'State of New Hampshire v. John A. Smith',),
            ('2012-729, Appeal of the Local Government Center, Inc. & a . ',
             'Appeal of the Local Government Center, Inc. & a .',),
            ('2013-0343  In the Matter of Susan Spenard and David Spenard',
             'In the Matter of Susan Spenard and David Spenard',),
            ('2013-0893, Stephen E. Forster d/b/a Forster’s Christmas Tree',
             'Stephen E. Forster d/b/a Forster’s Christmas Tree'),
        )
        regex = nh.Site().link_text_regex
        for test, result in string_pairs:
            try:
                case_name = regex.search(test).group(2).strip()
                self.assertEqual(
                    case_name,
                    result,
                    msg="Did not get expected results when regex'ing: '%s'.\n"
                        "  Expected: '%s'\n"
                        "  Instead:  '%s'" % (test, result, case_name)
                )
            except AttributeError:
                self.fail("Unable to parse nh string: '{s}'".format(s=test))

    def test_ca6_oa(self):
        # Tests are triads. 1: Input s, 2: Group 1, 3: Group 2.
        tests = (
            ('13-4101 Avis Rent A Car V City of Dayton Ohio',
             '13-4101',
             'Avis Rent A Car V City of Dayton Ohio'),
            ('13-3950 13-3951 USA v Damien Russ',
             '13-3950 13-3951',
             'USA v Damien Russ'),
            ('09 5517  USA vs Taylor',
             '09 5517',
             'USA vs Taylor'),
        )
        regex = ca6.Site().regex
        for test, group_1, group_2 in tests:
            try:
                result_1 = regex.search(test).group(1).strip()
                self.assertEqual(
                    result_1,
                    group_1,
                    msg="Did not get expected results when regex'ing: '%s'.\n"
                        "  Expected: '%s'\n"
                        "  Instead:  '%s'" % (test, group_1, result_1)
                )
                result_2 = regex.search(test).group(2).strip()
                self.assertEqual(
                    result_2,
                    group_2,
                    msg="Did not get expected results when regex'ing: '%s'.\n"
                        "  Expected: '%s'\n"
                        "  Instead:  '%s'" % (test, group_2, result_2)
                )
            except AttributeError:
                self.fail("Unable to parse ca6 string: '{s}'".format(s=test))


if __name__ == '__main__':
    unittest.main()
