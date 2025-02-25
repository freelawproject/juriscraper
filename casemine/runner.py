import ast
from datetime import datetime

from casemine.casemine_util import CasemineUtil
from juriscraper.opinions.united_states.state import calctapp_4th_div1, \
    calctapp_4th_div2, calctapp_4th_div3, calctapp_5th, calctapp_6th, \
    calctapp_app_div, calctapp_u

site = calctapp_u.Site()

site.execute_job("nysupct")

print(f"Total judgements: {site.cases.__len__()}")

# Iterate over the items
class_name = site.get_class_name()
court_name = site.get_court_name()
court_type = site.get_court_type()
state_name = site.get_state_name()

def check_none(field):
    if field is None:
        return ''
    else:
        return field

ctr = 1
for opinion in site:
    # print(opinion)
    date = opinion.get('case_dates')
    opinion_date = date.strftime('%d/%m/%Y')
    res = CasemineUtil.compare_date(opinion_date, site.crawled_till)
    if res == 1:
        site.crawled_till = opinion_date
    year = int(opinion_date.split('/')[2])
    jud = opinion.get('judges')
    if jud is None:
        jud = []

    citation = opinion.get('citations')
    if citation is None or citation == ['']:
        citation = []

    docket = opinion.get('docket_numbers')
    if docket is not None:
        if docket == '':
            docket = []
        else:
            docket = ast.literal_eval(docket)
    else:
        docket = []


    parallel_citation = opinion.get('parallel_citations')
    if parallel_citation is None:
        parallel_citation = []

    lower_court_judges = opinion.get('lower_court_judges')
    if lower_court_judges is None:
        lower_court_judges = []

    dans = opinion.get('docket_attachment_numbers')
    if dans is None:
        dans = []

    ddns = opinion.get('docket_document_numbers')
    if ddns is None:
        ddns = []

    data = {
        # required
        'title' : check_none(opinion.get('case_names')),
        'pdf_url': check_none(opinion.get('download_urls')),
        'date': opinion_date,
        'case_status': check_none(opinion.get('precedential_statuses')),
        'docket': docket,
        # optional
        'date_filed_is_approximate': check_none(opinion.get('date_filed_is_approximate')),
        'judges': jud,
        'citation': citation,
        'parallel_citation': parallel_citation,
        'summary': check_none(opinion.get('summaries')),
        'lower_court': check_none(opinion.get('lower_courts')),
        'child_court': check_none(opinion.get('child_courts')),
        'adversary_number': check_none(opinion.get('adversary_numbers')),
        'division': check_none(opinion.get('divisions')),
        'disposition': check_none(opinion.get('dispositions')),
        'cause': check_none(opinion.get('causes')),
        'docket_attachment_number': dans,
        'docket_document_number': ddns,
        'nature_of_suit': check_none(opinion.get('nature_of_suit')),
        'lower_court_number': check_none(opinion.get('lower_court_numbers')),
        'lower_court_judges':lower_court_judges,
        'author': check_none(opinion.get('authors')),
        'per_curiam': check_none(opinion.get('per_curiam')),
        'type': check_none(opinion.get('types')),
        'joined_by': check_none(opinion.get('joined_by')),
        'other_date': check_none(opinion.get('other_dates')),
        # extra
        'blocked_statuses': check_none(opinion.get('blocked_statuses')),
        'case_name_shorts': check_none(opinion.get('case_name_shorts')),
        'opinion_type': check_none(opinion.get('opinion_types')),
        # additional
        'crawledAt': datetime.now(),
        'processed': 333,
        'court_name': court_name,
        'court_type': court_type,
        'class_name': class_name,
        'year': year,
    }
    if court_type.__eq__('Federal'):
        data["circuit"] = state_name
        data['teaser']= check_none(opinion.get("teasers"))
    else:
        data["state"] = state_name
    # print(data)
    flag = site._process_opinion(data)
    if flag:
        print(f'{ctr} - {data}')
    else:
        print("\t!!..Duplicate..!!")
    ctr = ctr + 1

site.set_crawl_config_details(class_name, site.crawled_till)
