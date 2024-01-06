from juriscraper.opinions.united_states.state import nytrial


class Site(nytrial.Site):
    court_regex = r"Sup[rt]?\.? ?[Cc]o?u?r?t?|[sS]ur?pu?rem?e? C(our)?t|Sur?pe?r?me?|Suoreme|Sup County|Integrated Domestic Violence|Soho Fashions LTD"
