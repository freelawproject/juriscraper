"""
History:
 - 2014-08-07: Fixed due to InsanityError on docketnumber
"""

from datetime import date

from juriscraper.opinions.united_states.federal_appellate import ca9_p


class Site(ca9_p.Site):
    """The unpublished cases have one more column than the published. Thus some
    overriding is done here. More than usual, but it's very slight tweaks."""

    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = "http://www.ca9.uscourts.gov/memoranda/?o_mode=view&amp;o_sort_field=21&amp;o_sort_type=DESC&o_page_size=100"
        self.court_id = self.__module__
        self.position = ""
        self.base = self.get_base_path()
        self.back_scrape_date_start = date(2009, 11, 11)
        self.back_scrape_date_end = date(2015, 1, 1)
        self.back_scrape_iterable = self.get_backscrape_iterable()
        self.back_scrape_url = "http://www.ca9.uscourts.gov/memoranda/"

        def get_back_scrape_parameters(self, d):
            return {
                "c_page_size": "50",
                "c__ff_cms_memoranda_case_name_operator": "like",
                "c__ff_cms_memoranda_case_num_operator": "like",
                "c__ff_cms_memoranda_case_panel_operator": "like",
                "c__ff_cms_memoranda_case_origin_operator": "like",
                "c__ff_cms_memoranda_case_type_operator": "%3D",
                "c__ff_cms_memoranda_filed_date_operator": "like",
                "c__ff_cms_memoranda_filed_date": d.strftime("%m/%d/%Y"),
                "c__ff_onSUBMIT_FILTER": "Search",
            }
