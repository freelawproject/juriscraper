# Create a site object
from datetime import datetime

from juriscraper.opinions.united_states.federal_appellate import ca1

site = ca1.Site()

site.execute_job("ca1")

# Populate it with data, downloading the page if necessary
# site.parse()

# Print out the object
# print(str(site))

# Print it out as JSON
# print(site.to_json())

# Iterate over the item
class_name = site.get_class_name()
court_name = site.get_court_name()
court_type = site.get_court_type()

for opinion in site:
    print(opinion)
    date = opinion.get('case_dates')
    date_obj=datetime.strptime(date,'')
    opinion_date = date_obj.strftime('%d/%m/%Y')
    year = opinion_date.split('/')[2]
    data = {
        # required
        'title' : opinion.get('case_names'),
        'download_url': opinion.get('download_urls'),
        'date': opinion_date,
        'case_status': opinion.get('precedential_statuses'),
        'docket': opinion.get('docket_numbers'),
        # optional
        'date_filed_is_approximate': opinion.get('date_filed_is_approximate'),
        'judges': opinion.get('judges'),
        'citation': opinion.get('citations'),
        'parallel_citation': opinion.get('parallel_citations'),
        'summary': opinion.get('summaries'),
        'lower_court': opinion.get('lower_courts'),
        'child_court': opinion.get('child_courts'),
        'adversary_number': opinion.get('adversary_numbers'),
        'division': opinion.get('divisions'),
        'disposition': opinion.get('dispositions'),
        'cause': opinion.get('causes'),
        'docket_attachment_number': opinion.get('docket_attachment_numbers'),
        'docket_document_number': opinion.get('docket_document_numbers'),
        'nature_of_suit': opinion.get('nature_of_suit'),
        'lower_court_number': opinion.get('case_dates'),
        'lower_court_judges': opinion.get('lower_court_judges'),
        'author': opinion.get('authors'),
        'per_curiam': opinion.get('per_curiam'),
        'type': opinion.get('types'),
        'joined_by': opinion.get('joined_by'),
        'other_date': opinion.get('other_dates'),
        # extra
        'blocked_statuses': opinion.get('blocked_statuses'),
        'case_name_shorts': opinion.get('case_name_shorts'),
        # additional
        'crawledAt': datetime.now() ,
        'processed': 333,
        'court_name': court_name,
        'court_type': court_type,
        'class_name': class_name,
        'year': year
    }
    site._process_opinion(data)
