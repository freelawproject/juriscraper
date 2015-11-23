from datetime import date
import mo


class Site(mo.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        today = date.today()
        self.url = 'https://www.courts.mo.gov/page.jsp?id=12086&dist=Opinions Western&date=all&year=%s#all' % today.year
        self.court_id = self.__module__

    def _get_divisions(self):
        return ['Western Dist.'] * len(self.case_names)
