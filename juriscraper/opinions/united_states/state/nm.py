from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    """This cour's website is implemented by Decisia, a software
    that has built-in anti-bot detection. If you make too many
    requests in rapid succession, the site will render a captcha
    page instead of rendering the real page content. Since the
    docket numbers for unpublished opinions are not published on
    the main results page (but on sub-info pages), we may (likely)
    need to issues multiple sub-requests for each crawl to retrieve
    the docket info for unpublished opinions.

    Given the above, we need to track and limit the number of
    sub-requests we make in order to prevent triggering the
    anti-bot detection, which would trigger the captcha and
    crash our scraping.

    If we ever wanted to implement a back scraper for this court,
    we'd likely need to create a separate class to handle it. In order
    to do this, we'd need to use the 'Advanced Search' mechanism to
    find all results. The results page will render 25 results. But,
    in a browser, when you scroll down, more results populate dynamically
    on the page via javascript.  So, we'd need to hit the page via a
    phantomjs webdriver and keep loading results. To make things more
    complicated, we'd also need to batch our (sub) requests in order
    to prevent triggering the anti-bot detection. I've testing sleeping
    for 1 minute every 40 requests, and that seems to work. Consequently,
    the back scraper would take a very very long time to run, but if we
    needed to do it, it can probably be done with the above method.
    """

    # fetch no more than 20 docket numbers for non-published opinions (see above)
    SUB_REQUEST_LIMIT = 20

    # The url query parameter below is required to actually render the data.
    # For whatever reason, the main page (url without IFRAME_QUERY) loads itself
    # with IFRAME_QUERY into an iframe to render the results. Don't ask why.
    IFRAME = "iframe=true"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            f"https://nmonesource.com/nmos/nmsc/en/nav_date.do?{self.IFRAME}"
        )
        self.cases = []

    def _download(self, request_dict={}):
        self.request_dict = request_dict
        html = super()._download(self.request_dict)
        self.extract_cases(html)
        return html

    def extract_cases(self, html):
        sub_request_count = 0
        sub_page_docket_path = '//tr[contains(./td[@class="label"]/text(), "Docket")]/td[@class="metadata"]'
        for record in html.xpath('//div[@class="documentList"]//li'):
            url = record.xpath('.//div[@class="documents"]/a/@href')[0]
            info = record.xpath('.//div[@class="subinfo"]')[0]
            date_string = info.xpath('.//span[@class="publicationDate"]')[
                0
            ].text_content()
            court_status_string = info.xpath('.//div[@class="subMetadata"]')[
                0
            ].text_content()
            status = (
                "Unpublished"
                if "unreported" in court_status_string.lower()
                else "Published"
            )
            anchor = info.xpath('.//span[@class="title"]/a')[0]
            name = anchor.text_content()
            citation = info.xpath('.//span[@class="citation"]')
            if citation:
                # the docket is displayed on the main results page (published opinion)
                docket = citation[0].text_content()
            else:
                if sub_request_count >= self.SUB_REQUEST_LIMIT:
                    # in order to avoid anti-bot detection, only don't fetch
                    # too many docket numbers for un-published opinions
                    continue
                if self.test_mode_enabled():
                    # avoid hitting network during test
                    docket = "test-docket-placeholder"
                else:
                    # find the docket from the sub page (unpublished opinion)
                    self.url = f"{anchor.attrib['href']}?{self.IFRAME}"
                    logger.info(
                        "%s: searching for docket on sub page %s"
                        % (self.court_id, self.url)
                    )
                    sub_page = super()._download(self.request_dict)
                    sub_request_count += 1
                    cell = sub_page.xpath(sub_page_docket_path)
                    if not cell:
                        # if no docket found on sub page, move on to the next opinion
                        logger.info(
                            'no docket found on sub page, skipping opinion "%s"'
                            % name
                        )
                        continue
                    docket = cell[0].text_content().strip()
                    logger.info(
                        'found docket "%s" on sub page for opinion "%s"'
                        % (docket, name)
                    )
            self.cases.append(
                {
                    "name": name,
                    "url": url,
                    "docket": docket,
                    "date": convert_date_string(date_string),
                    "status": status,
                }
            )

    def _get_download_urls(self):
        return [case["url"] for case in self.cases]

    def _get_case_names(self):
        return [case["name"] for case in self.cases]

    def _get_case_dates(self):
        return [case["date"] for case in self.cases]

    def _get_precedential_statuses(self):
        return [case["status"] for case in self.cases]

    def _get_docket_numbers(self):
        return [case["docket"] for case in self.cases]
