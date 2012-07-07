#!/usr/bin/env python
# -*- coding: utf-8 -*-

from string_utils import clean_string, force_unicode, harmonize, titlecase


def harmonize_and_clean_string_tests():
    '''
    >>> harmonize(clean_string('U.S.A. v. Lissner'))
    u'United States v. Lissner'
    >>> harmonize(clean_string('U.S. v. Lissner'))
    u'United States v. Lissner'
    >>> harmonize(clean_string('U. S. v. Lissner'))
    u'United States v. Lissner'
    >>> harmonize(clean_string('United States v. Lissner'))
    u'United States v. Lissner'
    >>> harmonize(clean_string('Usa v. Lissner'))
    u'United States v. Lissner'
    >>> harmonize(clean_string('USA v. Lissner'))
    u'United States v. Lissner'
    >>> harmonize(clean_string('United States of America v. Lissner'))
    u'United States v. Lissner'
    >>> harmonize(clean_string('Lissner v. United States of America'))
    u'Lissner v. United States'
    >>> harmonize(clean_string('V.Vivack and Associates v. US'))
    u'V.Vivack and Associates v. United States'
    >>> harmonize(clean_string('v.v. Hendricks & Sons v. James v. Smith'))
    u'v.v. Hendricks & Sons v. James v. Smith'
    >>> harmonize(clean_string('U.S.A. v. Mr. v.'))
    u'United States v. Mr. v.'
    >>> harmonize(clean_string('U.S.S. v. Lissner'))
    u'U.S.S. v. Lissner'
    >>> harmonize(clean_string('USC v. Lissner'))
    u'USC v. Lissner'
    >>> harmonize(clean_string('U.S.C. v. Lissner'))
    u'U.S.C. v. Lissner'
    >>> harmonize(clean_string('U.S. Steel v. Colgate'))
    u'U.S. Steel v. Colgate'
    >>> harmonize(clean_string('papusa'))
    u'papusa'
    >>> harmonize(clean_string('CUSANO'))
    u'CUSANO'
    >>> harmonize(clean_string('US Steel v.  US'))
    u'US Steel v. United States'
    >>> harmonize(clean_string('US v. V.Vivack'))
    u'United States v. V.Vivack'
    >>> harmonize(clean_string('US vs. Lissner'))
    u'United States v. Lissner'
    >>> harmonize(clean_string('vs.boxer@gmail.com vs. USA'))
    u'vs.boxer@gmail.com v. United States'
    >>> harmonize(clean_string('US v. US'))
    u'United States v. United States'
    >>> harmonize(clean_string('US  Steel v.  US'))
    u'US Steel v. United States'
    >>> harmonize(clean_string('Lissner, et. al.'))
    u'Lissner'
    >>> harmonize(clean_string('Lissner, et. al'))
    u'Lissner'
    >>> harmonize(clean_string('Lissner, et al.'))
    u'Lissner'
    >>> harmonize(clean_string('Lissner, et al'))
    u'Lissner'
    >>> harmonize(clean_string('Lissner et. al.'))
    u'Lissner'
    >>> harmonize(clean_string('Lissner et. al'))
    u'Lissner'
    >>> harmonize(clean_string('Lissner et al.'))
    u'Lissner'
    >>> harmonize(clean_string('Lissner et al'))
    u'Lissner'
    >>> harmonize(clean_string('clarinet alibi'))
    u'clarinet alibi'
    >>> harmonize(clean_string('US v. Lissner, Plaintiff'))
    u'United States v. Lissner'
    >>> harmonize(clean_string('US v. Lissner, Petitioner-appellant'))
    u'United States v. Lissner'
    >>> harmonize(clean_string('United States, Petitioner, v. Lissner'))
    u'United States v. Lissner'
    >>> harmonize(clean_string('United States of America, Plaintiff-Appellee, v. Orlando B. Pino, Defendant-Appellant, Joseph'))
    u'United States v. Orlando B. Pino, Joseph'
    >>> harmonize(clean_string('Herring v. U.S. **'))
    u'Herring v. United States'
    >>> harmonize(clean_string('Test v. U.S'))
    u'Test v. United States'
    >>> harmonize(clean_string('The United States v. Lissner'))
    u'United States v. Lissner'
    >>> harmonize(clean_string('USA v White')) # tests no period in v.
    u'United States v. White'
    >>> harmonize(clean_string('USA vs White')) # tests no period in vs.
    u'United States v. White'
    >>> harmonize(clean_string('/USA vs White')) # tests leading slash.
    u'United States v. White'
    '''


def titlecase_tests():
    '''
    >>> titlecase(force_unicode("Q&A with steve jobs: 'that's what happens in technology'")).encode('utf-8')
    "Q&A With Steve Jobs: 'That's What Happens in Technology'"
    >>> titlecase(force_unicode("What is AT&T's problem?")).encode('utf-8')
    "What is AT&T's Problem?"
    >>> titlecase(force_unicode('Apple deal with AT&T falls through')).encode('utf-8')
    'Apple Deal With AT&T Falls Through'
    >>> titlecase(force_unicode('this v that')).encode('utf-8')
    'This v That'
    >>> titlecase(force_unicode('this v. that')).encode('utf-8')
    'This v. That'
    >>> titlecase(force_unicode('this vs that')).encode('utf-8')
    'This vs That'
    >>> titlecase(force_unicode('this vs. that')).encode('utf-8')
    'This vs. That'
    >>> titlecase(force_unicode("The SEC's Apple Probe: What You Need to Know")).encode('utf-8')
    "The SEC's Apple Probe: What You Need to Know"
    >>> titlecase(force_unicode("'by the Way, small word at the start but within quotes.'")).encode('utf-8')
    "'By the Way, Small Word at the Start but Within Quotes.'"
    >>> titlecase(force_unicode('Small word at end is nothing to be afraid of')).encode('utf-8')
    'Small Word at End is Nothing to Be Afraid Of'
    >>> titlecase(force_unicode('Starting Sub-Phrase With a Small Word: a Trick, Perhaps?')).encode('utf-8')
    'Starting Sub-Phrase With a Small Word: A Trick, Perhaps?'
    >>> titlecase(force_unicode("Sub-Phrase With a Small Word in Quotes: 'a Trick, Perhaps?'")).encode('utf-8')
    "Sub-Phrase With a Small Word in Quotes: 'A Trick, Perhaps?'"
    >>> titlecase(force_unicode('Sub-Phrase With a Small Word in Quotes: "a Trick, Perhaps?"')).encode('utf-8')
    'Sub-Phrase With a Small Word in Quotes: "A Trick, Perhaps?"'
    >>> titlecase(force_unicode('"Nothing to Be Afraid of?"')).encode('utf-8')
    '"Nothing to Be Afraid Of?"'
    >>> titlecase(force_unicode('"Nothing to be Afraid Of?"')).encode('utf-8')
    '"Nothing to Be Afraid Of?"'
    >>> titlecase(force_unicode('a thing')).encode('utf-8')
    'A Thing'
    >>> titlecase(force_unicode("2lmc Spool: 'gruber on OmniFocus and vapo(u)rware'")).encode('utf-8')
    "2lmc Spool: 'Gruber on OmniFocus and Vapo(u)rware'"
    >>> titlecase(force_unicode('this is just an example.com')).encode('utf-8')
    'This is Just an example.com'
    >>> titlecase(force_unicode('this is something listed on del.icio.us')).encode('utf-8')
    'This is Something Listed on del.icio.us'
    >>> titlecase(force_unicode('iTunes should be unmolested')).encode('utf-8')
    'iTunes Should Be Unmolested'
    >>> text = titlecase(force_unicode('Reading between the lines of steve jobs’s ‘thoughts on music’')).encode('utf-8')
    >>> result = 'Reading Between the Lines of Steve Jobs\xe2\x80\x99s \xe2\x80\x98thoughts on Music\xe2\x80\x99'
    >>> text == result
    True
    >>> text = titlecase(force_unicode('seriously, ‘repair permissions’ is voodoo')).encode('utf-8')
    >>> result = 'Seriously, \xe2\x80\x98repair Permissions\xe2\x80\x99 is Voodoo'
    >>> text == result
    True
    >>> titlecase(force_unicode('generalissimo francisco franco: still dead; kieren McCarthy: still a jackass')).encode('utf-8')
    'Generalissimo Francisco Franco: Still Dead; Kieren McCarthy: Still a Jackass'
    >>> titlecase(force_unicode('Chapman v. u.s. Postal Service')).encode('utf-8')
    'Chapman v. U.S. Postal Service'
    >>> titlecase(force_unicode('Spread Spectrum Screening Llc. v. Eastman Kodak Co.')).encode('utf-8')
    'Spread Spectrum Screening LLC. v. Eastman Kodak Co.'
    >>> titlecase(force_unicode('Consolidated Edison Co. of New York, Inc. v. Entergy Nuclear Indian Point 2, Llc.')).encode('utf-8')
    'Consolidated Edison Co. of New York, Inc. v. Entergy Nuclear Indian Point 2, LLC.'
    >>> titlecase(force_unicode('Infosint s.a. v. H. Lundbeck A/s')).encode('utf-8')
    'Infosint S.A. v. H. Lundbeck A/S'
    >>> titlecase(force_unicode("KEVIN O'CONNELL v. KELLY HARRINGTON")).encode('utf-8')
    "Kevin O'Connell v. Kelly Harrington"
    >>> titlecase(force_unicode('International Union of Painter v. J&r Flooring, Inc')).encode('utf-8')
    'International Union of Painter v. J&R Flooring, Inc'
    '''

if __name__ == '__main__':
    '''Run tests with python tests.py'''
    import doctest
    doctest.testmod()
