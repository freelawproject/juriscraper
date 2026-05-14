from juriscraper.state.RequestManager import (
    RateLimit,
    RequestManager,
    Retry,
)


class FloridaScraper:
    def __init__(self) -> None:
        self.manager: RequestManager = RequestManager(
            handlers=[RateLimit(), Retry()]
        )
