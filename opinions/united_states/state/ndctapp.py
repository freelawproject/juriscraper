# Author: Michael Lissner
# Date created: 2013-06-11
# This court only hears cases that the ND Supreme Court assigns to it. As a
# result, years can go by without a case from this court.

from juriscraper.opinions.united_states.state import nd


class Site(nd.Site):
    """This class is almost an exact clone of the nd scraper.  They both point
    to the same resource page, but they scrape different data from that page.
    The page presents both Supreme Court and Appeal cases. While the nd scraper
    will look at the resource page and extract all of the Supreme Court cases
    and exclude the Appeal cases, this scraper will do the opposite.  That is,
    this scraper will only return the appeal cases listed on the resource page.

    The Appeals Court on North Dakota is only empaneled when the Supreme Court
    has a conflict of interest or when the backlog at the Supreme Court becomes
    too great (apparently this is statutorily defined). If the backlog is too
    big, the idea is that an Appeals Court can serve as a filtering function to
    decide cases before they go to the Supreme Court. (Of course, may of these
    cases are then appealed to the Supreme Court, so that's an issue.)

    In any case, as a result of this structure, appeal cases are posted VERY
    infrequently and it is completely normal for this scraper to return zero
    results for very long periods of time.  At the time of writing this (Feb
    2016), the last legitimate Appeal case was posted 8.5 years ago (Aug 2007).
    """

    def _should_scrape_case(self, citation):
        return self._is_appellate_citation(citation)
