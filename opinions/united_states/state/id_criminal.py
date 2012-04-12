from id_civil import id_civil
import HTMLParser
import time
from datetime import date
import urllib
import string
import re
from GenericSite import GenericSite


class id_criminal(id_civil):
    def __init__(self):
        super(id_criminal, self).__init__()
        self.url = 'http://www.isc.idaho.gov/opinions/sccrim.htm'
        self.court_id = self.__module__
