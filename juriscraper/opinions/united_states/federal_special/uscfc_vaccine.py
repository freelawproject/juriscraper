"""Scraper for the United States Court of Federal Claims
CourtID: uscfc
Court Short Name: Fed. Cl."""

from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import ExtractedMetadata
from juriscraper.opinions.united_states.federal_special import uscfc


class Site(uscfc.Site):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.url = "https://ecf.cofc.uscourts.gov/cgi-bin/CFC_RecentDecisionsOfTheSpecialMasters.pl"

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Extract 'status' from text, if possible

        On the first page of the opinion, after the parties and attorneys names
        the decision title may point to it being published.

        The scraped site itself marks all `uscfc_vaccine` opinions as
        unreported
        """
        if "PUBLISHED DECISION" in scraped_text[:1500]:
            return {"OpinionCluster": {"precedential_status": "Published"}}

        return {}
