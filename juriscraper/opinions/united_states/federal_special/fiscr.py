from .fisc import Site as FiscSite


class Site(FiscSite):
    def skip_record(self, docket: str, filename: str) -> bool:
        """Skips a record that belongs to FISC

        :param docket: docket number
        :param filename: opinion title

        :return: True if record should skipped
        """
        return "FISCR" not in docket and "FISCR" not in filename
