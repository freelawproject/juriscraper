import unittest

from juriscraper.AbstractSite import logger
from juriscraper.opinions.united_states.state import nev_u, nevapp_u


class NevadaInitialsPanelTest(unittest.TestCase):
    def test_initials_only_panel(self):
        """Unpublished orders list the panel as initials only"""
        supreme, appeals = nev_u.Site(), nevapp_u.Site()
        tests = [
            (
                supreme,
                'Order of Affirmance. "ORDER the judgment AFFIRMED." DH/KP/RP. (SC)',
                "Douglas Herndon, Kristina Pickering, Ron D. Parraguirre",
            ),
            (
                supreme,
                "Order Denying Petition. ORDER the petition DENIED. A26 - KP/RP/LB (SC)",
                "Kristina Pickering, Ron D. Parraguirre, Linda Marie Bell",
            ),
            (
                supreme,
                "ORDER this appeal DISMISSED. A26-KP/RP/LB. (SC)",
                "Kristina Pickering, Ron D. Parraguirre, Linda Marie Bell",
            ),
            (
                appeals,
                "ORDER the petition DENIED. COA-BB/MG/DW. (COA)",
                "Bonnie A. Bulla, Michael P. Gibbons, Deborah L. Westbrook",
            ),
            (
                appeals,
                "ORDER AFFIRMED. Court of Appeals- MG/BB/DW. (COA)",
                "Michael P. Gibbons, Bonnie A. Bulla, Deborah L. Westbrook",
            ),
            (
                supreme,
                "Order Dismissing Appeal. This appeal is dismissed. (SC)",
                "",
            ),
            (
                supreme,
                "ORDER AFFIRMED. fn1[See NRS/NRAP.] SNP23-DH/PL/RP. (SC).",
                "Douglas Herndon, Patricia Lee, Ron D. Parraguirre",
            ),
            (supreme, "ORDER the motion GRANTED AND/OR DENIED. (SC)", ""),
        ]
        for site, description, judges in tests:
            with self.subTest(description=description):
                metadata = site.parse_description(description, "2026-07-06")
                self.assertEqual(metadata["judge"], judges)

    def test_initials_only_panel_unknown_judge(self):
        """Initials missing from the roster are reported, not dropped"""
        site = nev_u.Site()
        with self.assertLogs(logger, level="ERROR"):
            metadata = site.parse_description(
                "ORDER the petition DENIED. A26 - XY/KP/RP (SC)", "2026-07-06"
            )
        self.assertEqual(
            metadata["judge"], "Kristina Pickering, Ron D. Parraguirre"
        )


if __name__ == "__main__":
    unittest.main()
