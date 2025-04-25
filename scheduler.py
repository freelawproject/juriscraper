import os
import importlib
import schedule
import time
import logging
from datetime import datetime
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler("juriscraper_scheduler.log"), logging.StreamHandler()])
logger = logging.getLogger("juriscraper_scheduler")

# Import the CasemineUtil class
from casemine.casemine_util import CasemineUtil

# Define the folders to scan
FOLDERS_TO_SCAN = [
    "juriscraper/opinions/united_states/federal_district",
    "juriscraper/opinions/united_states/federal_appellate",
    "juriscraper/opinions/united_states/federal_bankruptcy",
    "juriscraper/opinions/united_states/state"
]
# Define restricted classes
RESTRICTED_CLASSES = {
    'dcd', 'd_sc', 'gov_info', 'bap9', 'bap10', 'nysupct_commercial',
    'miss', 'nytrial', 'nycrimct', 'scctapp', 'nycivct', 'alacrimapp',
    'nyag', 'mdag', 'or', 'missctapp', 'ind', 'nycountyct', 'ca3_u',
    'cadc_u', 'cadc_pi', 'bap1', 'indtc','sc',"masslandct","texag","indctapp",
    'minnag','calag',"miss_beginningofyear","la","miss","scctapp","ala","alacivapp"
}

def get_module_name(file_path):
    """Convert file path to module name."""
    # Remove .py extension and replace / with .
    module_name = file_path.replace('.py', '').replace('/', '.')
    return module_name

def run_site(site_class, class_name):
    """Run a site class and process its opinions."""
    try:
        # Get site information
        site = site_class.Site()
        court_name = site.get_court_name()
        state_name = site.get_state_name()

        # Get initial crawl date
        initial_crawl_date = site.crawled_till

        # Log start of processing
        start_time = datetime.now()
        logger.info(f"\n\n********************[{class_name}, {court_name}, {state_name}]********************")
        logger.info(f"Starting Date and time : {start_time.strftime('%d/%m/%Y %I:%M:%S %p')}")
        logger.info(f"Crawling started from : {initial_crawl_date}")

        site.execute_job(class_name)

        # Get additional site information
        court_type = site.get_court_type()

        # Process opinions
        total_records = 0
        unique_records = 0
        duplicate_records = 0

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
                try:
                    site._process_opinion(data)
                    unique_records += 1
                except Exception as e:
                    if "Judgment already Exists" in str(e):
                        duplicate_records += 1
                    else:
                        logger.error(f"Error processing opinion: {str(e)}")
                        logger.error(traceback.format_exc())
                total_records += 1
            except Exception as e:
                logger.error(f"Error processing opinion: {str(e)}")
                logger.error(traceback.format_exc())

        # Update crawl config details
        site.set_crawl_config_details(class_name, site.crawled_till)

        # Log end of processing
        end_time = datetime.now()
        logger.info(f"Ending Date and time : {end_time.strftime('%d/%m/%Y %I:%M:%S %p')}")
        logger.info(f"Crawling ended at : {site.crawled_till}")
        logger.info(f"Total records processed : {total_records}")
        logger.info(f"Unique records inserted : {unique_records}")
        logger.info(f"Duplicate records found : {duplicate_records}")
        logger.info("")

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
        'date': datetime.strptime(opinion_date, "%d/%m/%Y"),
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
        'html_url': check_none(opinion.get('html_urls')),
        'response_html': check_none(opinion.get('response_htmls')),
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

    # Track which classes have been processed
    processed_classes = set()
    total_classes = 0
    successful_classes = set()
    error_classes = set()
    skipped_classes = set()

    for folder in FOLDERS_TO_SCAN:
        logger.info(f"Scanning folder: {folder}")

        # Get all Python files in the folder
        try:
            files = [f for f in os.listdir(folder) if f.endswith('.py') and f != '__init__.py']
            total_classes += len(files)

            for file in files:
                try:
                    # Convert file path to module name
                    module_path = os.path.join(folder, file)
                    module_name = get_module_name(module_path)
                    class_name = module_name.split('.')[-1]

                    # Skip restricted classes
                    if class_name in RESTRICTED_CLASSES:
                        skipped_classes.add(class_name)
                        logger.info(f"Skipping restricted class: {class_name}")
                        continue

                    # Import the module
                    module = importlib.import_module(module_name)

                    # Find the Site class in the module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and attr_name == 'Site':
                            # Run the site
                            try:
                                run_site(module, class_name)
                                successful_classes.add(class_name)
                            except Exception as e:
                                error_classes.add(class_name)
                                logger.error(f"Error running class {class_name}: {str(e)}")
                                logger.error(traceback.format_exc())
                            processed_classes.add(class_name)
                            break
                except Exception as e:
                    logger.error(f"Error processing file {file}: {str(e)}")
                    logger.error(traceback.format_exc())
        except Exception as e:
            logger.error(f"Error scanning folder {folder}: {str(e)}")
            logger.error(traceback.format_exc())

    logger.info("Completed discovery and execution of all site classes")

    # Log summary of processed classes
    logger.info("\n\n\n******************** CLASS PROCESSING SUMMARY ********************")
    logger.info(f"Total classes found: {total_classes}")
    logger.info(f"Successfully processed classes ({len(successful_classes)}):")
    for class_name in sorted(successful_classes):
        logger.info(f"  - {class_name}")
    logger.info(f"\nClasses with errors ({len(error_classes)}):")
    for class_name in sorted(error_classes):
        logger.info(f"  - {class_name}")
    logger.info(f"\nSkipped restricted classes ({len(skipped_classes)}):")
    for class_name in sorted(skipped_classes):
        logger.info(f"  - {class_name}")
    logger.info("******************************************************************\n")

    # If all classes have been processed at least once, terminate the program
    if len(processed_classes) + len(skipped_classes) == total_classes:
        logger.info(f"All {total_classes} classes have been processed or skipped. Terminating program.")
        os._exit(0)

    else:
        logger.info(f"Processed {len(processed_classes)} out of {total_classes} classes. Continuing...")

def job():
    """Main job function to be scheduled."""
    logger.info("Starting scheduled job")
    discover_and_run_sites()
    logger.info("Completed scheduled job")


def main():
    """Main function to set up the scheduler."""
    logger.info("Setting up scheduler")

    SHCEDULING_HOUR = 18
    SHCEDULING_MINUTE = 10
    # Schedule the job to run at 6:00 AM every day
    schedule.every().day.at(f"{SHCEDULING_HOUR}:{SHCEDULING_MINUTE}").do(job)

    # Also run every 10 minutes
    schedule.every(10).minutes.do(job)

    logger.info(f"Scheduler set up. Running jobs at {SHCEDULING_HOUR}:{SHCEDULING_MINUTE} daily and every 10 minutes.")

    # Run the job immediately on startup
    job()
    logger.info("Waiting for scheduled times...")

    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main() 