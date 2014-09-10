#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import glob
import logging
import os
import time
import unittest

from juriscraper.lib.importer import build_module_list
from juriscraper.lib.date_utils import parse_dates, quarter, \
    is_first_month_in_quarter
from juriscraper.lib.string_utils import clean_string
from juriscraper.lib.string_utils import fix_camel_case
from juriscraper.lib.string_utils import force_unicode
from juriscraper.lib.string_utils import harmonize
from juriscraper.lib.string_utils import titlecase
from juriscraper.opinions.united_states.state import massappct, pa
import sys


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
                paths = glob.glob(
                    '%s_example*' % module_string.replace('.', '/'))
                self.assertTrue(paths, "No example file found for: %s!" %
                                module_string.rsplit('.', 1)[1])
                num_example_files += len(paths)
                t1 = time.time()
                num_tests = len(paths)
                for path in paths:
                    # This loop allows multiple example files per module
                    if path.endswith('~'):
                        # Text editor backup: Not interesting.
                        continue
                    site = mod.Site()
                    site.url = path
                    # Forces a local GET
                    site.method = 'LOCAL'
                    site.parse()
                t2 = time.time()

                max_speed = 2
                warn_speed = 1
                speed = t2 - t1
                if speed > max_speed:
                    print ("\nThis scraper took {speed}s to test, which is "
                           "more than the allowed speed of {max_speed}s. "
                           "Please speed it up before checking in.".format(
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
            # Fix 'of', ',etal', and the problems
            ('RawdinvTheAmericanBrdofPediatrics',
             'Rawdin v. The American Brd of Pediatrics'),
            ('Santomenno,etalv.JohnHancockLifeInsuranceCompany,etal',
             'Santomenno v. John Hancock Life Insurance Company'),
            ('BaughvSecretaryoftheNavy',
             'Baugh v. Secretary of the Navy'),
            ('Smallv.CamdenCountyetal',
             'Small v. Camden County'),
        )
        for pair in test_pairs:
            self.assertEqual(pair[1], fix_camel_case(pair[0]))


class ScraperSpotTest(unittest.TestCase):
    """Adds specific tests to specific courts that are more-easily tested
    without a full integration test.
    """

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


if __name__ == '__main__':
    unittest.main()
