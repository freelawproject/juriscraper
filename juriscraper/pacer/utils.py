import re
from datetime import date, datetime
from typing import Dict, Optional, Union

import requests
import tldextract
from dateutil import parser
from dateutil.tz import gettz
from lxml import html

from ..lib.exceptions import ParsingException


def get_court_id_from_doc_id_prefix(prefix):
    prefix_to_cid_map = {
        "001": "ca1",
        "002": "ca2",
        "003": "ca3",
        "004": "ca4",
        "005": "ca5",
        "006": "ca6",
        "007": "ca7",
        "008": "ca8",
        "009": "ca9",
        "010": "ca10",
        "011": "ca11",
        "012": "cadc",
        "014": "cit",
        "015": "cofc",
        "016": "almb",
        "017": "almd",
        "018": "alnb",
        "019": "alnd",
        "020": "alsb",
        "021": "alsd",
        "022": "akb",
        "023": "akd",
        "024": "arb",
        "025": "azd",
        "026": "areb",
        "027": "ared",
        "028": "arwb",
        "029": "arwd",
        "031": "cacd",
        "032": "caeb",
        "033": "caed",
        "034": "canb",
        "035": "cand",
        "036": "casb",
        "037": "casd",
        "038": "cob",
        "039": "cod",
        "040": "ctb",
        "041": "ctd",
        "042": "deb",
        "043": "ded",
        "044": "dcb",
        "045": "dcd",
        "046": "flmb",
        "047": "flmd",
        "048": "flnb",
        "049": "flnd",
        "050": "flsb",
        "051": "flsd",
        "052": "gamb",
        "053": "gamd",
        "054": "ganb",
        "055": "gand",
        "056": "gasb",
        "057": "gasd",
        "058": "gub",
        "059": "gud",
        "060": "hib",
        "061": "hid",
        "062": "idb",
        "063": "idd",
        "064": "ilcb",
        "065": "ilcd",
        "066": "ilnb",
        "067": "ilnd",
        "068": "ilsb",
        "069": "ilsd",
        "070": "innb",
        "071": "innd",
        "072": "insb",
        "073": "insd",
        "074": "ianb",
        "075": "iand",
        "076": "iasb",
        "077": "iasd",
        "078": "ksb",
        "079": "ksd",
        "080": "kyeb",
        "081": "kyed",
        "082": "kywb",
        "083": "kywd",
        "084": "laeb",
        "085": "laed",
        "086": "lamb",
        "087": "lamd",
        "088": "lawb",
        "089": "lawd",
        "090": "meb",
        "091": "med",
        "092": "mdb",
        "093": "mdd",
        "094": "mab",
        "095": "mad",
        "096": "mieb",
        "097": "mied",
        "098": "miwb",
        "099": "miwd",
        "100": "mnb",
        "101": "mnd",
        "102": "msnb",
        "103": "msnd",
        "104": "mssb",
        "105": "mssd",
        "106": "moeb",
        "107": "moed",
        "108": "mowb",
        "109": "mowd",
        "110": "mtb",
        "111": "mtd",
        "112": "neb",
        "113": "ned",
        "114": "nvb",
        "115": "nvd",
        "116": "nhb",
        "117": "nhd",
        "118": "njb",
        "119": "njd",
        "120": "nmb",
        "121": "nmd",
        "122": "nyeb",
        "123": "nyed",
        "124": "nynb",
        "125": "nynd",
        "126": "nysb",
        "127": "nysd",
        "128": "nywb",
        "129": "nywd",
        "130": "nceb",
        "131": "nced",
        "132": "ncmb",
        "133": "ncmd",
        "134": "ncwb",
        "135": "ncwd",
        "136": "ndb",
        "137": "ndd",
        "138": "nmib",
        "139": "nmid",
        "140": "ohnb",
        "141": "ohnd",
        "142": "ohsb",
        "143": "ohsd",
        "144": "okeb",
        "145": "oked",
        "146": "oknb",
        "147": "oknd",
        "148": "okwb",
        "149": "okwd",
        "150": "orb",
        "151": "ord",
        "152": "paeb",
        "153": "paed",
        "154": "pamb",
        "155": "pamd",
        "156": "pawb",
        "157": "pawd",
        "158": "prb",
        "159": "prd",
        "160": "rib",
        "161": "rid",
        "162": "scb",
        "163": "scd",
        "164": "sdb",
        "165": "sdd",
        "166": "tneb",
        "167": "tned",
        "168": "tnmb",
        "169": "tnmd",
        "170": "tnwb",
        "171": "tnwd",
        "174": "txeb",
        "175": "txed",
        "176": "txnb",
        "177": "txnd",
        "178": "txsb",
        "179": "txsd",
        "180": "txwb",
        "181": "txwd",
        "182": "utb",
        "183": "utd",
        "184": "vtb",
        "185": "vtd",
        "188": "vaeb",
        "189": "vaed",
        "190": "vawb",
        "191": "vawd",
        "192": "vib",
        "193": "vid",
        "194": "waeb",
        "195": "waed",
        "196": "wawb",
        "197": "wawd",
        "198": "wvnb",
        "199": "wvnd",
        "200": "wvsb",
        "201": "wvsd",
        "202": "wieb",
        "203": "wied",
        "204": "wiwb",
        "205": "wiwd",
        "206": "wyb",
        "207": "wyd",
        "850": "jpml",
        "973": "cacb",
    }
    return prefix_to_cid_map[prefix]


def get_doc_id_prefix_from_court_id(court_id):
    cid_to_prefix_map = {
        "akb": "022",
        "akd": "023",
        "almb": "016",
        "almd": "017",
        "alnb": "018",
        "alnd": "019",
        "alsb": "020",
        "alsd": "021",
        "arb": "024",
        "areb": "026",
        "ared": "027",
        "arwb": "028",
        "arwd": "029",
        "azd": "025",
        "ca1": "001",
        "ca2": "002",
        "ca3": "003",
        "ca4": "004",
        "ca5": "005",
        "ca6": "006",
        "ca7": "007",
        "ca8": "008",
        "ca9": "009",
        "ca10": "010",
        "ca11": "011",
        "cacb": "973",
        "cacd": "031",
        "cadc": "012",
        "caeb": "032",
        "caed": "033",
        "canb": "034",
        "cand": "035",
        "casb": "036",
        "casd": "037",
        "cavc": "012",
        "cit": "014",
        "cob": "038",
        "cod": "039",
        "cofc": "015",
        "ctb": "040",
        "ctd": "041",
        "dcb": "044",
        "dcd": "045",
        "deb": "042",
        "ded": "043",
        "flmb": "046",
        "flmd": "047",
        "flnb": "048",
        "flnd": "049",
        "flsb": "050",
        "flsd": "051",
        "gamb": "052",
        "gamd": "053",
        "ganb": "054",
        "gand": "055",
        "gasb": "056",
        "gasd": "057",
        "gub": "058",
        "gud": "059",
        "hib": "060",
        "hid": "061",
        "ianb": "074",
        "iand": "075",
        "iasb": "076",
        "iasd": "077",
        "idb": "062",
        "idd": "063",
        "ilcb": "064",
        "ilcd": "065",
        "ilnb": "066",
        "ilnd": "067",
        "ilsb": "068",
        "ilsd": "069",
        "innb": "070",
        "innd": "071",
        "insb": "072",
        "insd": "073",
        "jpml": "850",
        "ksb": "078",
        "ksd": "079",
        "kyeb": "080",
        "kyed": "081",
        "kywb": "082",
        "kywd": "083",
        "laeb": "084",
        "laed": "085",
        "lamb": "086",
        "lamd": "087",
        "lawb": "088",
        "lawd": "089",
        "mab": "094",
        "mad": "095",
        "mdb": "092",
        "mdd": "093",
        "meb": "090",
        "med": "091",
        "mieb": "096",
        "mied": "097",
        "miwb": "098",
        "miwd": "099",
        "mnb": "100",
        "mnd": "101",
        "moeb": "106",
        "moed": "107",
        "mowb": "108",
        "mowd": "109",
        "msnb": "102",
        "msnd": "103",
        "mssb": "104",
        "mssd": "105",
        "mtb": "110",
        "mtd": "111",
        "nceb": "130",
        "nced": "131",
        "ncmb": "132",
        "ncmd": "133",
        "ncwb": "134",
        "ncwd": "135",
        "ndb": "136",
        "ndd": "137",
        "neb": "112",
        "ned": "113",
        "nhb": "116",
        "nhd": "117",
        "njb": "118",
        "njd": "119",
        "nmb": "120",
        "nmd": "121",
        "nmib": "138",
        "nmid": "139",
        "nvb": "114",
        "nvd": "115",
        "nyeb": "122",
        "nyed": "123",
        "nynb": "124",
        "nynd": "125",
        "nysb": "126",
        "nysd": "127",
        "nywb": "128",
        "nywd": "129",
        "ohnb": "140",
        "ohnd": "141",
        "ohsb": "142",
        "ohsd": "143",
        "okeb": "144",
        "oked": "145",
        "oknb": "146",
        "oknd": "147",
        "okwb": "148",
        "okwd": "149",
        "orb": "150",
        "ord": "151",
        "paeb": "152",
        "paed": "153",
        "pamb": "154",
        "pamd": "155",
        "pawb": "156",
        "pawd": "157",
        "prb": "158",
        "prd": "159",
        "rib": "160",
        "rid": "161",
        "scb": "162",
        "scd": "163",
        "sdb": "164",
        "sdd": "165",
        "tneb": "166",
        "tned": "167",
        "tnmb": "168",
        "tnmd": "169",
        "tnwb": "170",
        "tnwd": "171",
        "txeb": "174",
        "txed": "175",
        "txnb": "176",
        "txnd": "177",
        "txsb": "178",
        "txsd": "179",
        "txwb": "180",
        "txwd": "181",
        "utb": "182",
        "utd": "183",
        "vaeb": "188",
        "vaed": "189",
        "vawb": "190",
        "vawd": "191",
        "vib": "192",
        "vid": "193",
        "vtb": "184",
        "vtd": "185",
        "waeb": "194",
        "waed": "195",
        "wawb": "196",
        "wawd": "197",
        "wieb": "202",
        "wied": "203",
        "wiwb": "204",
        "wiwd": "205",
        "wvnb": "198",
        "wvnd": "199",
        "wvsb": "200",
        "wvsd": "201",
        "wyb": "206",
        "wyd": "207",
    }
    return cid_to_prefix_map[court_id]


def get_pacer_court_info():
    r = requests.get("https://court-version-scraper.fly.dev/courts.json")
    return r.json()


def get_courts_from_json(j):
    courts = []
    for k, v in j.items():
        for court in v["courts"]:
            court["type"] = k
            courts.append(court)
    return courts


def get_court_id_from_url(url):
    """Extract the court ID from the URL."""
    parts = tldextract.extract(url)
    return parts.subdomain.split(".")[1]


def get_pacer_case_id_from_nonce_url(url):
    """Extract the pacer case ID from the URL.

    In: https://ecf.almd.uscourts.gov/cgi-bin/DktRpt.pl?56120
    Out: 56120
    In: https://ecf.azb.uscourts.gov/cgi-bin/iquery.pl?625371913403797-L_9999_1-0-663150
    Out: 663150
    """
    param = url.split("?")[1]
    if "L" in param:
        return param.rsplit("-", 1)[1]
    return param


def get_pacer_seq_no_from_doc1_url(url):
    """Extract the seq_no from the doc1 URL."""
    match = re.search(r"de_seq_num=(\d+)", url)
    if match:
        return match.group(1)
    else:
        return None


def get_pacer_case_id_from_doc1_url(url):
    """Extract the caseid from the doc1 URL."""
    match = re.search(r"caseid=(\d+)", url)
    if match:
        return match.group(1)
    else:
        return None


def get_pacer_magic_num_from_doc1_url(
    url: str,
    appellate: bool = False,
) -> Optional[str]:
    """Extract the magic number from the doc1 URL."""
    if appellate:
        # NDA free look link format is:
        # https://ecf.ca2.uscourts.gov/docs1/00208721516?uid=b775e9908ad79ce2
        match = re.search(r"uid=(\w+)", url)
    else:
        # NEF free look link format is:
        # https://ecf.almd.uscourts.gov/doc1/01713718205?caseid=75736&de_seq_num=30&magic_num=77910494
        match = re.search(r"magic_num=(\d+)", url)
    if match:
        return match.group(1)
    else:
        return None


def get_pacer_doc_id_from_doc1_url(url: str) -> str:
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
    assert (
        "show_case_doc" not in url
    ), "Cannot get doc1 ID from show_case_doc URL"
    url = url.rsplit("/", 1)[1].split("?")[0]
    url = f"{url[:3]}0{url[4:]}"
    return url


def get_pacer_seq_no_from_doc1_anchor(anchor):
    """Extract the PACER sequence number from an HTML anchor node.

    :param anchor: An LXML Element.
    :return: None if no sequence number can be found. Otherwise returns the
    sequence number.
    """
    try:
        onclick = anchor.xpath("./@onclick")[0]
    except IndexError:
        return None
    else:
        if "goDLS" in onclick:
            go_dls_parts = reverse_goDLS_function(onclick)
            return go_dls_parts["de_seq_num"]


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
       has an attachment. Note that the eighth parameter was added some time
       after 2010. Dockets older than that date only have seven responses.
    """
    args = re.findall("'(.*?)'", s)
    parts = {
        "form_post_url": args[0],
        "caseid": args[1],
        "de_seq_num": args[2],
        "got_receipt": args[3],
        "pdf_header": args[4],
        "pdf_toggle_possible": args[5],
        "magic_num": args[6],
    }
    try:
        parts["hdr"] = args[7]
    except IndexError:
        # At some point dockets added this eighth parameter. Older ones lack it
        parts["hdr"] = None
    return parts


def make_doc1_url(court_id, pacer_doc_id, skip_attachment_page):
    """Make a doc1 URL.

    If skip_attachment_page is True, we replace the fourth digit with a 1
    instead of a zero, which bypasses the attachment page.
    """
    if skip_attachment_page and pacer_doc_id[3] == "0":
        # If the fourth digit is a 0, replace it with a 1
        pacer_doc_id = f"{pacer_doc_id[:3]}1{pacer_doc_id[4:]}"
    doc_id_cid = get_court_id_from_doc_id_prefix(pacer_doc_id[:3])
    # The cadc/cavc courts use the same doc1 prefix so we need a court_id.
    if court_id is None and doc_id_cid == "cadc":
        raise ValueError(
            f"pacer_doc_id {pacer_doc_id} prefix has court_id cadc or cavc, "
            f"correct court_id must be passed explicitly"
        )
    elif court_id is None:
        court_id = doc_id_cid
    elif court_id == "cavc" and doc_id_cid == "cadc":
        pass
    elif court_id != doc_id_cid:
        raise ValueError(
            f"pacer_doc_id {pacer_doc_id} prefix has court_id {doc_id_cid}, "
            f"expected {court_id}"
        )
    return f"https://ecf.{court_id}.uscourts.gov/doc1/{pacer_doc_id}"


def make_docs1_url(
    court_id: Optional[str], pacer_doc_id: str, skip_attachment_page
) -> str:
    """Make a docs1 URL for NDAs free look downloads.

    :param court_id: The court ID.
    :param pacer_doc_id: The PACER document ID.
    """
    if skip_attachment_page and pacer_doc_id[3] == "0":
        # If the fourth digit is a 0, replace it with a 1
        pacer_doc_id = f"{pacer_doc_id[:3]}1{pacer_doc_id[4:]}"
    doc_id_cid = get_court_id_from_doc_id_prefix(pacer_doc_id[:3])
    # The cadc/cavc courts use the same doc1 prefix so we need a court_id.
    if court_id is None and doc_id_cid == "cadc":
        raise ValueError(
            f"pacer_doc_id {pacer_doc_id} prefix has court_id cadc or cavc, "
            f"correct court_id must be passed explicitly"
        )
    elif court_id is None:
        court_id = doc_id_cid
    elif court_id == "cavc" and doc_id_cid == "cadc":
        pass
    elif court_id != doc_id_cid:
        raise ValueError(
            f"pacer_doc_id {pacer_doc_id} prefix has court_id {doc_id_cid}, "
            f"expected {court_id}"
        )
    return f"https://ecf.{court_id}.uscourts.gov/docs1/{pacer_doc_id}"


def is_pdf(response):
    """Determines whether the item downloaded is a PDF or something else."""
    if response.headers.get("content-type") == "application/pdf":
        return True
    return False


def is_text(response):
    """Determines whether the item downloaded is a text file or something else."""
    if ".txt" in response.headers.get("content-type", ""):
        return True
    return False


def get_nonce_from_form(r):
    """Get a nonce value from a HTML response. Returns the first nonce that is
    found.

    :param r: The response object you wish to parse.
    :returns A nonce object that can be used to query PACER or None, if no
    nonce can be found.
    """
    try:
        tree = html.fromstring(r.text)
    except ValueError:
        # This usually happens when we are blocked from a court.
        raise ParsingException(
            "Got XML when expecting HTML and cannot parse it."
        )
    form_attrs = tree.xpath("//form//@action")
    for attr in form_attrs:
        # The action attr will be a value like:
        # ../cgi-bin/HistDocQry.pl?112801540788508-L_1_0-1
        # Split on the '?', and return the nonce.
        try:
            path, nonce = attr.split("?")
        except ValueError:
            raise ParsingException("Didn't get nonce from PACER form.")
        else:
            if "-L_" in nonce:
                return nonce
    return None


BASE_IA_URL = "https://www.archive.org/download"


def get_bucket_name(court, pacer_case_id):
    bucketlist = ["gov", "uscourts", court, str(pacer_case_id)]
    return ".".join(bucketlist)


def get_docket_filename(court, pacer_case_id):
    return ".".join(
        [
            "gov",
            "uscourts",
            str(court),
            str(pacer_case_id),
            "docket.xml",
        ]
    )


def get_document_filename(
    court, pacer_case_id, document_number, attachment_number
):
    return ".".join(
        [
            "gov",
            "uscourts",
            str(court),
            str(pacer_case_id),
            str(document_number),
            str(attachment_number or 0),
            "pdf",
        ]
    )


def get_docketxml_url(court, pacer_case_id):
    return "{}/{}/{}".format(
        BASE_IA_URL,
        get_bucket_name(court, pacer_case_id),
        get_docket_filename(court, pacer_case_id),
    )


def get_pdf_url(court, pacer_case_id, document_number, attachment_number):
    return "{}/{}/{}".format(
        BASE_IA_URL,
        get_bucket_name(court, pacer_case_id),
        get_document_filename(
            court, pacer_case_id, document_number, attachment_number
        ),
    )


def set_pacer_doc_id_as_appellate_document_number(
    de: Dict[str, Union[str, date, datetime]]
) -> None:
    """For appellate courts that don't use numbers, if available set the
    pacer_doc_id as document number.

    :param de: The docket entry dict to set the document number.
    :return: None, the dict is modified in place.
    """
    if not de["document_number"]:
        if de["pacer_doc_id"]:
            # If we lack the document number, but have
            # the pacer doc ID, use it.
            de["document_number"] = de["pacer_doc_id"]
        else:
            # We lack both the document number and the pacer doc ID.
            # Probably a minute order. No need to set either.
            pass


def parse_datetime_for_us_timezone(datetime_str: str) -> datetime:
    """Parse a datetime from a string that contains a US timezone.
    :param datetime_str: The str datetime to parse.
    :return: A datetime object with UTC timezone offset.
    """

    # Supported US timezones.
    tzinfos = {
        # US standard timezones
        "EST": gettz("US/Eastern"),
        "CST": gettz("US/Central"),
        "MST": gettz("US/Mountain"),
        "PST": gettz("US/Pacific"),
        "AKST": gettz("US/Alaska"),
        "HST": gettz("US/Hawaii"),
        "CHST": gettz("Pacific/Guam"),
        "SST": gettz("US/Samoa"),
        "AST": gettz("America/Puerto_Rico"),
        # US daylight saving time timezones
        "EDT": gettz("US/Eastern"),
        "CDT": gettz("US/Central"),
        "MDT": gettz("US/Mountain"),
        "PDT": gettz("US/Pacific"),
        "AKDT": gettz("US/Alaska"),
        "HDT": gettz("US/Hawaii"),
        # CHST, SST and AST, dont' observe DST.
    }
    date_time = parser.parse(datetime_str, tzinfos=tzinfos)
    if date_time.utcoffset() is None:
        # Raise an exception if a timezone abbreviation is not specified.
        raise NotImplementedError(f"Datetime {datetime_str} not understood.")
    return date_time
