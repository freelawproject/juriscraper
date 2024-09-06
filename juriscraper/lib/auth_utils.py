import os

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSite import OpinionSite


def set_api_token_header(site: OpinionSite) -> None:
    """
    Puts the NY_API_TOKEN in the X-Api-Token header
    Creates the Site.headers attribute, copying the
    scraper_site.request[headers]

    :param scraper_site: a Site Object
    :returns: None
    """
    if site.test_mode_enabled():
        return
    api_token = os.environ.get("NY_API_TOKEN", None)
    if not api_token:
        logger.warning(
            "NY_API_TOKEN environment variable is not set. "
            f"It is required for scraping New York Court: {site.court_id}"
        )
        return
    site.request["headers"]["X-APIKEY"] = api_token
    site.needs_special_headers = True
