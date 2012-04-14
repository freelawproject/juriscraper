from string_utils import clean_string
from string_utils import harmonize

def test_strings():
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

if __name__ == "__main__":
    import doctest
    doctest.testmod()
