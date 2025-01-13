from juriscraper.opinions.united_states.state import nh_p


class Site(nh_p.Site):
    """
    From:
    https://www.courts.nh.gov/our-courts/supreme-court/orders-and-opinions/case-orders

    > The final orders below were issued in cases decided by the
    Supreme Court. These final orders, which are not
    precedential opinions, have been made available on a
    regular basis on the Supreme Court website beginning
    October 1, 2014. Only final orders deciding the merits of
    a case will be published here; orders that are not final orders,
    such as orders remanding for clarification or orders declining or
    dismissing cases, will not be published. Final merits orders in
    confidential cases are not published here or elsewhere.
    """

    # document_purpose = 1856 -> Supreme Court Case Orders
    base_filter = "{}@field_document_purpose|=|1856"
    start_year = 2014
    filter_mode = "INCLUSIVE"
    document_type = "case-orders"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Unpublished"
        self.year_to_filter.update(
            {
                2021: "@field_document_subcategory|=|1616",
                2020: "@field_document_subcategory|=|1611",
                2019: "@field_document_subcategory|=|1606",
            }
        )
