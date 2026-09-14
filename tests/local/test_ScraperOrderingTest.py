import unittest
from datetime import date

from juriscraper.AbstractSite import AbstractSite
from juriscraper.ClusterSite import ClusterSite
from juriscraper.lib.importer import build_module_list
from juriscraper.OpinionSite import OpinionSite
from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.OralArgumentSite import OralArgumentSite
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class ScraperOrderingTest(unittest.TestCase):
    """Checks the ordering contract described in `AbstractSite`

    Consumers stop crawling at the first run of known items, so a scraper
    must either order its results newest first or declare that it can't
    with `is_recency_ordered = False`.
    """

    base_classes = [
        AbstractSite,
        OpinionSite,
        OpinionSiteLinear,
        OralArgumentSite,
        OralArgumentSiteLinear,
        ClusterSite,
    ]

    # module string -> expected `is_recency_ordered`
    expected_by_module = {
        "juriscraper.opinions.united_states.state.fla": False,
        "juriscraper.opinions.united_states.state.fladistctapp_1": False,
        "juriscraper.opinions.united_states.state.fladistctapp_2": False,
        "juriscraper.opinions.united_states.state.fladistctapp_3": False,
        "juriscraper.opinions.united_states.state.fladistctapp_4": False,
        "juriscraper.opinions.united_states.state.fladistctapp_5": False,
        "juriscraper.opinions.united_states.state.fladistctapp_6": False,
        "juriscraper.opinions.united_states.administrative_agency.bia": False,
        "juriscraper.opinions.united_states.state.mich": False,
        "juriscraper.opinions.united_states.state.michctapp": False,
        # positive controls
        "juriscraper.opinions.united_states.state.kan_p": True,
        "juriscraper.oral_args.united_states.federal_appellate.ca9": True,
    }

    @staticmethod
    def import_site(module_string):
        return __import__(module_string, globals(), locals(), ["Site"], 0).Site

    def test_base_classes_default_to_recency_ordered(self):
        for klass in self.base_classes:
            with self.subTest(klass=klass.__name__):
                self.assertIs(klass.is_recency_ordered, True)

    def test_is_recency_ordered_per_court(self):
        for module_string, expected in self.expected_by_module.items():
            with self.subTest(module_string=module_string):
                site_class = self.import_site(module_string)
                self.assertIs(site_class.is_recency_ordered, expected)

    def test_is_recency_ordered_is_visible_on_instances(self):
        site = self.import_site(
            "juriscraper.opinions.united_states.state.fladistctapp_6"
        )()
        self.assertIs(site.is_recency_ordered, False)

    def test_is_recency_ordered_is_a_bool_everywhere(self):
        module_strings = build_module_list(
            "juriscraper.opinions"
        ) + build_module_list("juriscraper.oral_args")
        for module_string in module_strings:
            if "backscraper" in module_string:
                continue
            with self.subTest(module_string=module_string):
                site_class = self.import_site(module_string)
                self.assertIsInstance(site_class.is_recency_ordered, bool)

    def test_date_sort_orders_by_date_then_name(self):
        """Pins the default order that `is_recency_ordered = True` promises"""
        site = OpinionSiteLinear()
        site.case_dates = [
            date(2026, 1, 1),
            date(2026, 1, 2),
            date(2026, 1, 1),
        ]
        site.case_names = ["Alpha v. Beta", "Gamma v. Delta", "Zeta v. Eta"]
        site.download_urls = ["u1", "u2", "u3"]
        site.precedential_statuses = ["Published"] * 3
        site.blocked_statuses = [False] * 3
        site.date_filed_is_approximate = [False] * 3

        site._date_sort()

        # `_date_sort` writes the columns back as tuples
        self.assertEqual(
            list(site.case_names),
            ["Gamma v. Delta", "Zeta v. Eta", "Alpha v. Beta"],
        )
        self.assertEqual(list(site.download_urls), ["u2", "u3", "u1"])
