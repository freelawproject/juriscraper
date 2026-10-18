"""
History:
    - 2014-08-05: Updated by mlr because it was not working, however, in middle
      of update, site appeared to change. At first there were about five
      columns in the table and scraper was failing. Soon, there were seven and
      the scraper started working without my fixing it. Very odd.
    - 2023-01-13: Update to use RSS Feed
    - 2026-05-29: Updated URL after site moved feeds under /decisions/.
    - 2026-08-28: Read the court's DynamoDB table instead of the RSS feed.
"""

from juriscraper.opinions.united_states.federal_appellate import ca9_p


class Site(ca9_p.Site):
    table = "memoranda"
    base_url = "https://cdn.ca9.uscourts.gov/datastore/memoranda/"
    precedential_status = "Unpublished"

    def get_judge_fields(self, record: dict) -> dict:
        """Map the table's judge column onto case keys

        `memoranda` names the whole panel in `case_panel` and has no `judge`
        column, so there is no author to report

        :param record: a DynamoDB row
        :return: the judge related part of the case dict
        """
        return {"judge": ca9_p.get_attribute(record, "case_panel")}
