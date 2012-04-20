class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        # Replace %d with the current year; backscraper looks to be easy
        self.url = 'http://www.courts.state.nh.us/supreme/opinions/%d/index.htm'
        self.court_id = self.__module__

