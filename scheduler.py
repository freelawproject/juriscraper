import os
import importlib
import schedule
import time
import logging
from datetime import datetime
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("juriscraper_scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("juriscraper_scheduler")

# Import the CasemineUtil class
from casemine.casemine_util import CasemineUtil

# Define the folders to scan
FOLDERS_TO_SCAN = [
    # "juriscraper/opinions/united_states/federal_district",
    "juriscraper/opinions/united_states/federal_appellate",
    # "juriscraper/opinions/united_states/federal_bankruptcy",
    # "juriscraper/opinions/united_states/state"
]

def get_module_name(file_path):
    """Convert file path to module name."""
    # Remove .py extension and replace / with .
    module_name = file_path.replace('.py', '').replace('/', '.')
    return module_name

def run_site(site_class, class_name):
    """Run a site class and process its opinions."""
    try:
        logger.info(f"\n\n********************* Running {class_name} *********************\n\n")
        site = site_class.Site()
        site.execute_job(class_name)
        
        # Get site information
        class_name = site.get_class_name()
        court_name = site.get_court_name()
        court_type = site.get_court_type()
        state_name = site.get_state_name()
        
        # Process opinions
        ctr = 1
        for opinion in site:
            try:
                date = opinion.get('case_dates')
                opinion_date = date.strftime('%d/%m/%Y')
                res = CasemineUtil.compare_date(opinion_date, site.crawled_till)
                if res == 1:
                    site.crawled_till = opinion_date
                year = int(opinion_date.split('/')[2])
                
                # Process opinion data
                data = process_opinion_data(opinion, opinion_date, year, court_name, court_type, class_name, state_name)
                
                # Process the opinion
                flag = site._process_opinion(data)
                if flag:
                    logger.info(f'{ctr} - {data["title"]} - {data["date"]}')
                else:
                    logger.info(f'\t!!..Duplicate..!! {data["title"]} - {data["date"]}')
                ctr = ctr + 1
            except Exception as e:
                logger.error(f"Error processing opinion: {str(e)}")
                logger.error(traceback.format_exc())
        
        # Update crawl config details
        site.set_crawl_config_details(class_name, site.crawled_till)
        logger.info(f"Completed running {class_name}")
    except Exception as e:
        logger.error(f"Error running {class_name}: {str(e)}")
        logger.error(traceback.format_exc())

def process_opinion_data(opinion, opinion_date, year, court_name, court_type, class_name, state_name):
    """Process opinion data and return a dictionary."""
    # Helper function to check for None values
    def check_none(field):
        if field is None:
            return ''
        else:
            return field
    
    # Process judges
    jud = opinion.get('judges')
    if jud is None:
        jud = []

    # Process citations
    citation = opinion.get('citations')
    if citation is None or citation == ['']:
        citation = []

    # Process docket numbers
    docket = opinion.get('docket_numbers')
    if docket is not None:
        if docket == '':
            docket = []
        else:
            try:
                docket = eval(docket)
            except:
                docket = []
    else:
        docket = []

    # Process other fields
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

    # Create data dictionary
    data = {
        # required
        'title': check_none(opinion.get('case_names')),
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
        'lower_court_judges': lower_court_judges,
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
    
    # Add circuit or state based on court type
    if court_type == 'Federal':
        data["circuit"] = state_name
        data['teaser'] = check_none(opinion.get("teasers"))
    else:
        data["state"] = state_name
        
    return data

def discover_and_run_sites():
    """Discover all site classes in the specified folders and run them."""
    logger.info("Starting discovery and execution of all site classes")
    
    for folder in FOLDERS_TO_SCAN:
        logger.info(f"Scanning folder: {folder}")
        
        # Get all Python files in the folder
        try:
            files = [f for f in os.listdir(folder) if f.endswith('.py') and f != '__init__.py']
            
            for file in files:
                try:
                    # Convert file path to module name
                    module_path = os.path.join(folder, file)
                    module_name = get_module_name(module_path)
                    
                    # Import the module
                    module = importlib.import_module(module_name)
                    
                    # Find the Site class in the module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and attr_name == 'Site':
                            # Run the site
                            run_site(module, module_name.split('.')[-1])
                            break
                except Exception as e:
                    logger.error(f"Error processing file {file}: {str(e)}")
                    logger.error(traceback.format_exc())
        except Exception as e:
            logger.error(f"Error scanning folder {folder}: {str(e)}")
            logger.error(traceback.format_exc())
    
    logger.info("Completed discovery and execution of all site classes")

def job():
    """Main job function to be scheduled."""
    logger.info("Starting scheduled job")
    discover_and_run_sites()
    logger.info("Completed scheduled job")

def main():
    """Main function to set up the scheduler."""
    logger.info("Setting up scheduler")

    SHCEDULING_HOUR=16
    SHCEDULING_MINUTE=30
    # Schedule the job to run at 6:00 AM every day
    schedule.every().day.at(f"{SHCEDULING_HOUR}:{SHCEDULING_MINUTE}").do(job)
    
    # Also run every 10 minutes
    schedule.every(10).minutes.do(job)
    
    logger.info(f"Scheduler set up. Running jobs at {SHCEDULING_HOUR}:{SHCEDULING_MINUTE} daily and every 10 minutes.")
    
    # Run the job immediately on startup
    # job()
    logger.info("Waiting for scheduled times...")
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main() 