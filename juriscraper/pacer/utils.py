import certifi
import requests
import tldextract


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
    """
    return url.split('?')[1]


def get_pacer_document_number_from_doc1_url(url):
    """Extract the pacer document number from the doc1 URL.

    In:  https://ecf.almd.uscourts.gov/doc1/01712427473
    Out: 01712427473
    """
    return url.rsplit('/', 1)[1]


def verify_court_ssl(court_id):
    """Returns True for any court where the SSL is known to be bad."""
    bad_courts = [
        'nmib',  # Northern Mariana Islands Bankruptcy
        'ca3',   # Third Circuit
        'jpml',  # Judicial Panel on Multidistrict Litigation
    ]
    if court_id in bad_courts:
        return False
    return certifi.where()
