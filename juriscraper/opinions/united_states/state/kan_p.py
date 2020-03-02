#  Scraper for Kansas Supreme Court
# CourtID: kan_p

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinearWebDriven import OpinionSiteLinearWebDriven


class Site(OpinionSiteLinearWebDriven):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court = "Supreme Court"
        self.court_id = self.__module__
        self.pages = []
        self.pages_to_process = 5
        self.status = "Published"
        self.url = "https://www.kscourts.org/Cases-Opinions/Opinions"

    def _download(self, request_dict={}):
        if self.test_mode_enabled():
            test_page = super(Site, self)._download(request_dict)
            self.pages.append(test_page)
            return
        self.initiate_webdriven_session()
        self.click_through_filter_form()
        self.paginate_through_search_results()

    def _process_html(self):
        path_non_header_rows = "//table[@class='info-table']//tr[position()>1]"
        for page in self.pages:
            for row in page.xpath(path_non_header_rows):
                self.cases.append(
                    {
                        "date": self.get_cell_text(row, 1),
                        "docket": self.get_cell_text(row, 2),
                        "name": self.get_cell_text(row, 3),
                        "url": self.get_cell_link(row, 6),
                    }
                )

    def click_through_filter_form(self):
        # select the status
        id_status = self.get_form_id("Published")
        path_status = self.get_dropdown_path(id_status, self.status)
        self.webdriver.find_element_by_xpath(path_status).click()

        # select the court
        id_court = self.get_form_id("Court")
        path_court = self.get_dropdown_path(id_court, self.court)
        self.webdriver.find_element_by_xpath(path_court).click()

        # submit the form and wait to load
        id_submit = self.get_form_id("Filter", "btn")
        self.webdriver.find_element_by_id(id_submit).click()

    def get_cell_link(self, row, index):
        """Return the first anchor href in cell [index] in row"""
        return row.xpath(".//td[%d]//a/@href" % index)[0]

    def get_cell_text(self, row, index):
        """Return the text of cell [index] in row"""
        return row.xpath(".//td[%d]" % index)[0].text_content().strip()

    def paginate_through_search_results(self):
        """Click through search results pagination and store each page"""
        page_numbers_to_process = range(2, self.pages_to_process + 1)

        logger.info("Adding first result page")
        page_current = self.get_page()
        self.pages.append(page_current)

        for page_number in page_numbers_to_process:
            path = "//*[@id='pagination1']//li/a[text()=%d]" % page_number
            if not page_current.xpath(path):
                logger.info("Done paginating, no more results")
                break

            logger.info("Adding search result page %d" % page_number)
            pagination_link = self.webdriver.find_element_by_xpath(path)
            pagination_link.click()
            page_current = self.get_page()
            self.pages.append(page_current)

    def get_form_id(self, field, field_type="drp"):
        """Return the werid ASPX id attribute for [field] of [field_type]"""
        return (
            "p_lt_zonePagePlaceholder_pageplaceholder_p_lt_ctl02_"
            "OpinionFilter1_filterControl_" + field_type + field
        )

    def get_dropdown_path(self, id, value):
        """Return xpath for select form's dropdown element [id] with [value]"""
        format = "//*[@id='{id}']/option[@value='{value}']"
        return format.format(id=id, value=value)
