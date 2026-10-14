from typing_extensions import override

from juriscraper.opinions.united_states.state import nytrial


class Site(nytrial.Site):
    court_regex = r"^Ct Cl|C(our)?t( [Oo]f)? Cl(aims)?$"

    @override
    def _get_child_courts(self) -> list[str]:
        """Return an empty string as child_court, since the
        New York Court of Claims in this source has no children

        :return: list of empty strings
        """
        return ["" for _ in self.cases]
