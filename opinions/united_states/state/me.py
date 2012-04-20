class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.courts.state.me.us/opinions_orders/supreme/publishedopinions.shtml'
        self.court_id = self.__module__
