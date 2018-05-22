import re

import requests
import tldextract
from lxml import html
from six import string_types

from ..lib.string_utils import force_unicode


def get_pacer_court_info():
    r = requests.get("https://court-version-scraper.herokuapp.com/courts.json")
    return r.json()


def get_courts_from_json(j):
    courts = []
    for k, v in j.items():
        for court in v['courts']:
            court['type'] = k
            courts.append(court)
    return courts


def get_court_id_from_url(url):
    """Extract the court ID from the URL."""
    parts = tldextract.extract(url)
    return parts.subdomain.split('.')[1]


def get_pacer_case_id_from_docket_url(url):
    """Extract the pacer case ID from the docket URL.

    In: https://ecf.almd.uscourts.gov/cgi-bin/DktRpt.pl?56120
    Out: 56120
    In: https://ecf.azb.uscourts.gov/cgi-bin/iquery.pl?625371913403797-L_9999_1-0-663150
    Out: 663150
    """
    param = url.split('?')[1]
    if 'L' in param:
        return param.rsplit('-', 1)[1]
    return param


def get_pacer_doc_id_from_doc1_url(url):
    """Extract the pacer document ID from the doc1 URL. Coerce the fourth digit
    to zero.

    In:  https://ecf.almd.uscourts.gov/doc1/01712427473
    Out: 01702427473
    In:  /doc1/01712427473
    Out: 01702427473

    Note that results are strings, not ints, because many of the strings start
    with zero.

    See tests for more examples.
    """
    assert "show_case_doc" not in url, \
        "Cannot get doc1 ID from show_case_doc URL"
    url = url.rsplit('/', 1)[1].split('?')[0]
    url = url[:3] + "0" + url[4:]
    return url


def reverse_goDLS_function(s):
    """Extract the arguments from the goDLS JavaScript function.

    In: goDLS('/doc1/01712427473','56121','69','','','1','','');return(false);
    Out: {
      'form_post_url': '/doc1/01712427473',
      'caseid': '56121',
      'de_seq_num': '69',
      'got_receipt': '',
      'pdf_header': '',
      'pdf_toggle_possible': '1',
      'magic_num': '',
      'hdr': '',
    }

    The key names correspond to the form field names in the JavaScript on PACER,
    but we don't actually know what each of these values does. Our best
    speculation is:

     - form_post_url: Where the form is posted to. The HTML 'action' attribute.
     - caseid: The internal PACER ID for the case.
     - de_seq_num: Unclear. This seems to be the internal ID for the document,
       but this field can be omitted without any known issues.
     - got_receipt: If set to '1', this will bypass the receipt page and
       immediately direct you to the page where the PDF is embedded in an
       iframe.
     - pdf_header: Can be either 1 or 2. 1: Show the header. 2: No header.
     - pdf_toggle_possible: This seems to always be 1. Could be that some courts
       do not allow the header to be turned off, but we haven't discoered that
       yet.
     - magic_num: This is used for the "One free look" downloads.
     - hdr: Unclear what HDR stands for but on items that have attachments,
       passing this parameter bypasses the download attachment screen and takes
       you directly to the PDF that you're trying to download. For an example,
       see document 108 from 1:12-cv-00102 in tnmd, which is a free opinion that
       has an attachment.
    """
    args = re.findall("\'(.*?)\'", s)
    return {
        'form_post_url': args[0],
        'caseid': args[1],
        'de_seq_num': args[2],
        'got_receipt': args[3],
        'pdf_header': args[4],
        'pdf_toggle_possible': args[5],
        'magic_num': args[6],
        'hdr': args[7],
    }


def make_doc1_url(court_id, pacer_doc_id, skip_attachment_page):
    """Make a doc1 URL.

    If skip_attachment_page is True, we replace the fourth digit with a 1
    instead of a zero, which bypasses the attachment page.
    """
    if skip_attachment_page and pacer_doc_id[3] == '0':
        # If the fourth digit is a 0, replace it with a 1
        pacer_doc_id = pacer_doc_id[:3] + '1' + pacer_doc_id[4:]
    return 'https://ecf.%s.uscourts.gov/doc1/%s' % (court_id,
                                                    pacer_doc_id)


def is_pdf(response):
    """Determines whether the item downloaded is a PDF or something else."""
    if response.headers.get('content-type') == 'application/pdf':
        return True
    return False


def get_nonce_from_form(r):
    """Get a nonce value from a HTML response. Returns the first nonce that is
    found.

    :param r: The response object you wish to parse.
    :returns A nonce object that can be used to query PACER or None, if no nonce
    can be found.
    """
    tree = html.fromstring(r.text)
    form_attrs = tree.xpath('//form//@action')
    for attr in form_attrs:
        # The action attr will be a value like:
        # ../cgi-bin/HistDocQry.pl?112801540788508-L_1_0-1
        # Split on the '?', and return the nonce.
        path, nonce = attr.split('?')
        if '-L_' in nonce:
            return nonce
    return None


def clean_pacer_object(obj):
    """Clean a list or dict that is part of a scraping response.

    PACER data is notoriously horrible, so this function attempts to clean up
    common problems that it may have. You can pass in either a dict or a list,
    and it will be cleaned recursively.

    Supported cleanup includes:

    1. Removing spaces before commas.
    1. Stripping whitespace from the ends.
    1. Normalizing white space.
    1. Forcing unicode.

    :param obj: A dict or list containing string objects.
    :return: A dict or list with the string values cleaned.
    """
    if isinstance(obj, list):
        l = []
        for i in obj:
            l.append(clean_pacer_object(i))
        return l
    elif isinstance(obj, dict):
        d = {}
        for k, v in obj.items():
            d[k] = clean_pacer_object(v)
        return d
    elif isinstance(obj, string_types):
        s = ' '.join(obj.strip().split())
        s = force_unicode(s)
        return re.sub('\s+,', ',', s)
    else:
        return obj


BASE_IA_URL = "https://www.archive.org/download"


def get_bucket_name(court, pacer_case_id):
    bucketlist = ["gov", "uscourts", court, unicode(pacer_case_id)]
    return ".".join(bucketlist)


def get_docket_filename(court, pacer_case_id):
    return ".".join(["gov", "uscourts", unicode(court), unicode(pacer_case_id),
                     "docket.xml"])


def get_document_filename(court, pacer_case_id, document_number,
                          attachment_number):
    return ".".join(["gov", "uscourts", unicode(court), unicode(pacer_case_id),
                     unicode(document_number), unicode(attachment_number or 0),
                     "pdf"])


def get_docketxml_url(court, pacer_case_id):
    return "%s/%s/%s" % (
        BASE_IA_URL,
        get_bucket_name(court, pacer_case_id),
        get_docket_filename(court, pacer_case_id),
    )


def get_pdf_url(court, pacer_case_id, document_number, attachment_number):
    return "%s/%s/%s" % (
        BASE_IA_URL,
        get_bucket_name(court, pacer_case_id),
        get_document_filename(court, pacer_case_id, document_number,
                              attachment_number),
    )
