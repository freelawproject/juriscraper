import os

from juriscraper.AbstractSite import logger


def set_api_token_header(self) -> None:
    """
    Puts the NY_API_TOKEN in the X-Api-Token header
    Creates the Site.headers attribute, copying the
    scraper_site.request[headers]

    :param scraper_site: a Site Object
    :returns: None
    """
    if self.test_mode_enabled():
        return

    if "juriscraper.opinions.united_states.state.ny" not in self.court_id:
        logger.warning(
            "NY_API_TOKEN environment variable is not set. "
            f"It is required for scraping New York Court: {self.court_id}"
        )
        return

    api_token = os.environ.get("NY_API_TOKEN")
    self.request["headers"]["X-APIKEY"] = api_token
    self.needs_special_headers = True
