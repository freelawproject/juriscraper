from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.RateLimited import RateLimited


class OpinionSiteLinearRateLimited(OpinionSiteLinear, RateLimited):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _download(self, request_dict=None):
        if not self.apply_working_hours():
            return None
        return super()._download(request_dict)
