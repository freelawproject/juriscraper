#  Scraper for Kansas Supreme Court
# CourtID: kan_p

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinearWebDriven import OpinionSiteLinearWebDriven


class Site(OpinionSiteLinearWebDriven):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court = "Supreme Court"
        self.court_id = self.__module__
        self.pages = []
        self.pages_to_process = 5
        self.status = "Published"
        self.url = "https://www.kscourts.org/Cases-Opinions/Opinions.aspx"

    def _download(self, request_dict={}):
        if self.test_mode_enabled():
            test_page = super()._download(request_dict)
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
        """Fill out and the submit the form

        There is some bug that is preventing the standard webdriver
        functions from working on this website. The form elements,
        despite appearing proper in a screen shot, are recognized
        by the webdriver has have hugely negative X coordinates,
        which prevents us from being able to click them. I've tried
        an ungodly amount of solution to scroll to the element, or
        move it, before clicking, but simply couldn't get it to work.
        So instead, we are just executing jQuery scripts on the page
        to unselect and select form options before submitting.
        """

        # build and execute jQuery to manipulate form
        id_status = self.get_form_id("Published")
        id_court = self.get_form_id("Court")
        jquery_remove = "$('#%s option').each(function(){$(this).removeAttr('selected');});"
        jquery_select = (
            "$('#%s option[value=\"%s\"]').attr('selected','selected');"
        )
        jquery = ";".join(
            [
                jquery_remove % id_status,
                jquery_remove % id_court,
                jquery_select % (id_status, self.status),
                jquery_select % (id_court, self.court),
            ]
        )
        self.webdriver.execute_script(jquery)

        # submit the form and wait to load
        id_submit = self.get_form_id("Filter", "btn")
        self.find_element_by_id(id_submit).click()

    def get_cell_link(self, row, index):
        """Return the first anchor href in cell [index] in row"""
        return row.xpath(".//td[%d]//a/@href" % index)[0]

    def get_cell_text(self, row, index):
        """Return the text of cell [index] in row"""
        return row.xpath(".//td[%d]" % index)[0].text_content().strip()

    def paginate_through_search_results(self):
        """Click through search results pagination and store each page"""
        page_numbers_to_process = list(range(2, self.pages_to_process + 1))

        logger.info("Adding first result page")
        page_current = self.get_page()
        self.pages.append(page_current)

        for page_number in page_numbers_to_process:
            path = "//*[@id='pagination1']//li/a[text()=%d]" % page_number
            if not page_current.xpath(path):
                logger.info("Done paginating, no more results")
                break

            logger.info("Adding search result page %d" % page_number)
            pagination_link = self.find_element_by_xpath(path)
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
