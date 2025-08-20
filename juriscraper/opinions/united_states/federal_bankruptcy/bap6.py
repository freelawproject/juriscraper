from juriscraper.opinions.united_states.federal_appellate import ca6


class Site(ca6.Site):
    bap_scraper = True

    # See https://www.ca6.uscourts.gov/bankruptcy-appellate-panel
    initials_to_judges = {
        "RSM": "Randal S. Mashburn",
        "SHB": "Suzanne H. Bauknight",
        "JLC": "Jimmy Croom",
        "JTG": "John T. Gregg",
        "JPG": "John P. Gustafson",
        "CRM": "Charles R. Merrill",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.should_have_results = False
