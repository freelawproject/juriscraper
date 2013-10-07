#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import glob
import logging
import os
import time
import unittest

from juriscraper.lib.importer import build_module_list
from juriscraper.lib.parse_dates import parse_dates
from juriscraper.lib.string_utils import clean_string
from juriscraper.lib.string_utils import force_unicode
from juriscraper.lib.string_utils import harmonize
from juriscraper.lib.string_utils import titlecase
import sys


class DateParserTest(unittest.TestCase):
    def test_various_date_extractions(self):
        test_pairs = (
            # Dates separated by semicolons and JUMP words
            ('February 5, 1980; March 14, 1980 and May 28, 1980.',
             [datetime.datetime(1980, 2, 5, 0, 0), datetime.datetime(1980, 3, 14, 0, 0),
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
        print "Testing scrapers against example files:"
        module_strings = build_module_list('juriscraper.opinions')
        for module_string in module_strings:
            package, module = module_string.rsplit('.', 1)
            mod = __import__("%s.%s" % (package, module),
                             globals(),
                             locals(),
                             [module])
            if 'backscraper' not in module_string:
                sys.stdout.write('  %s ' % module_string)
                sys.stdout.flush()  # Makes sure the output prints before the error message.
                paths = glob.glob('%s_example*' % module_string.replace('.', '/'))
                self.assertTrue(paths, "No example file found for: %s!" % module_string.rsplit('.', 1)[1])
                t1 = time.time()
                for path in paths:
                    if path.endswith('~'):
                        # Text editor backup: Not interesting.
                        continue
                    # This loop allows multiple example files per module
                    site = mod.Site()
                    site.url = path
                    # Forces a local GET
                    site.method = 'LOCAL'
                    # do-nothing function, b/c we don't want to iterate over items in a DeferringList. Otherwise, this
                    # function is called as part of the parse() function.
                    site._clean_attributes = lambda *a: None
                    site.parse()
                t2 = time.time()
                if t2 - t1 > 2:
                    msg = " - WARNING: Slow scraper!"
                else:
                    msg = ' - OK'
                print '(%0.1f seconds%s)' % ((t2 - t1), msg)


class StringUtilTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_harmonize_and_clean_string_tests(self):
        """Tests various inputs for the clean_string and harmonize functions"""
        test_pairs = [['U.S.A. v. Lissner',
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
                      ['V.Vivack and Associates v. US',
                       u'V.Vivack and Associates v. United States'],
                      ['v.v. Hendricks & Sons v. James v. Smith',
                       u'v.v. Hendricks & Sons v. James v. Smith'],
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
                      ['papusa',
                       u'papusa'],
                      ['CUSANO',
                       u'CUSANO'],
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
                      ['clarinet alibi',
                       u'clarinet alibi'],
                      ['US v. Lissner, Plaintiff',
                       u'United States v. Lissner'],
                      ['US v. Lissner, Petitioner-appellant',
                       u'United States v. Lissner'],
                      ['United States, Petitioner, v. Lissner',
                       u'United States v. Lissner'],
                      ['United States of America, Plaintiff-Appellee, v. Orlando B. Pino, Defendant-Appellant, Joseph',
                       u'United States v. Orlando B. Pino, Joseph'],
                      ['Herring v. U.S. **',
                       u'Herring v. United States'],
                      ['Test v. U.S',
                       u'Test v. United States'],
                      ['The United States v. Lissner',
                       u'United States v. Lissner'],
                      ['USA v White',  # tests no period in v.
                       u'United States v. White'],
                      ['USA vs White',  # tests no period in vs.
                       u'United States v. White'],
                      ['/USA vs White',  # tests leading slash.
                       u'United States v. White'],
                      ['12–1438-cr',  # tests unicode input
                       u'12–1438-cr'],
                      ['Carver v. US',  # Tests the output from a titlecased word containing US to ensure it gets
                                        # harmonized.
                       u'Carver v. United States']]
        for pair in test_pairs:
            self.assertEqual(harmonize(clean_string(pair[0])), pair[1])

    def test_titlecase(self):
        """Tests various inputs for the titlecase function"""
        test_pairs = [["Q&A with steve jobs: 'that's what happens in technology'",
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
                      ['Reading between the lines of steve jobs’s ‘thoughts on music’', # Tests unicode
                       u'Reading Between the Lines of Steve Jobs’s ‘thoughts on Music’'],
                      ['seriously, ‘repair permissions’ is voodoo', # Tests unicode
                       u'Seriously, ‘repair Permissions’ is Voodoo'],
                      ['generalissimo francisco franco: still dead; kieren McCarthy: still a jackass',
                       u'Generalissimo Francisco Franco: Still Dead; Kieren McCarthy: Still a Jackass'],
                      ['Chapman v. u.s. Postal Service',
                       u'Chapman v. U.S. Postal Service'],
                      ['Spread Spectrum Screening Llc. v. Eastman Kodak Co.',
                       u'Spread Spectrum Screening LLC. v. Eastman Kodak Co.'],
                      ['Consolidated Edison Co. of New York, Inc. v. Entergy Nuclear Indian Point 2, Llc.',
                       u'Consolidated Edison Co. of New York, Inc. v. Entergy Nuclear Indian Point 2, LLC.'],
                      ['Infosint s.a. v. H. Lundbeck A/s',
                       u'Infosint S.A. v. H. Lundbeck A/S'],
                      ["KEVIN O'CONNELL v. KELLY HARRINGTON",
                       u"Kevin O'Connell v. Kelly Harrington"],
                      ['International Union of Painter v. J&r Flooring, Inc',
                       u'International Union of Painter v. J&R Flooring, Inc'],
                      ['DOROTHY L. BIERY, and JERRAMY and ERIN PANKRATZ v. THE UNITED STATES 07-693L And',
                       u'Dorothy L. Biery, and Jerramy and Erin Pankratz v. the United States 07-693l And'],
                      ['CARVER v. US',
                       u'Carver v. US']]
        for pair in test_pairs:
            self.assertEqual(titlecase(force_unicode(pair[0])),
                             pair[1])

if __name__ == '__main__':
    unittest.main()
