from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    """This court provides a json endpoint!
    How fun. Their single json endpoint dumps
    all of the cases into the following groupings:
        - Supreme
        - Published_Appellate
        - Unpublished_Appellate
        - Published_tax
        - Unpublished_Tax
        - Unpublished_Trial

    Human web interface: http://www.judiciary.state.nj.us/attorneys/opinions.html#Supreme
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "http://www.judiciary.state.nj.us/attorneys/assets"
        self.servername = "http://www.judiciary.state.nj.us"
        self.url = f"{self.base_url}/js/objects/opinions/op2017.json"
        self.case_types = ["Supreme"]

    def tweak_response_object(self):
        """Court is irresponsibly not returning valid json content
        type header, so we force it here. As a result, the self.html
        object will be a dict of the parsed json data.
        """
        self.request["response"].headers["content-type"] = "application/json"

    def _get_download_urls(self):
        urls = []
        for type in self.case_types:
            for opinion in self.html[type]:
                # They don't have uniform keys across all data, which is... odd
                if "DocumentURL" in opinion:
                    url = f"{self.servername}{opinion['DocumentURL']}"
                else:
                    url = self.get_absolute_opinion_path(
                        opinion["Document"], type
                    )
                urls.append(url)
        return urls

    def _get_case_names(self):
        names = []
        for type in self.case_types:
            names.extend([case["Title"] for case in self.html[type]])
        return names

    def _get_case_dates(self):
        dates = []
        for type in self.case_types:
            dates.extend(
                [
                    convert_date_string(case["PublishDate"])
                    for case in self.html[type]
                ]
            )
        return dates

    def _get_precedential_statuses(self):
        statuses = []
        for type in self.case_types:
            status = (
                "Unpublished"
                if type.startswith("Unpublished")
                else "Published"
            )
            statuses.extend([status] * len(self.html[type]))
        return statuses

    def _get_docket_numbers(self):
        dockets = []
        for type in self.case_types:
            dockets.extend([case["OpinionID"] for case in self.html[type]])
        return dockets

    def get_absolute_opinion_path(self, suffix, type):
        """Determine the absolute path given the file suffix in the
        json object and the opinion type.  This is necessary because
        the course does not return standardized data objects.
        """
        type_parts = type.lower().split("_")
        type_parts_length = len(type_parts)
        if type_parts_length == 1:
            status = False
            type = type_parts[0].lower()
        elif type_parts_length == 2:
            status = type_parts[0].lower()
            type = type_parts[1].lower()
        else:
            raise InsanityException(
                f'Unrecognized type "{type}", this should never happen'
            )
        if not suffix.startswith(type):
            if status:
                suffix = f"{type}/{status}/{suffix}"
            else:
                suffix = f"{type}/{suffix}"
        return f"{self.base_url}/opinions/{suffix}"
