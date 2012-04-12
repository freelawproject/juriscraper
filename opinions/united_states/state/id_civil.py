from GenericSite import GenericSite 
import HTMLParser 
import time 
from datetime import date 
import urllib 
import string 
import re
 
class id_civil(GenericSite):
    def __init__(self):
        super(id_civil, self).__init__()
        self.url = 'http://www.isc.idaho.gov/opinions/sccivil.htm'
        self.court_id = self.__module__

    def _get_case_names(self):
        names = []
        return_names = []
        for xelement in self.html.xpath('//li[@class="MsoNormal"]/span/a[1]'):
                texts = xelement.xpath('./descendant-or-self::text()');
                name_string = ''
                for text in texts:
                    name_string = name_string + HTMLParser.HTMLParser().unescape(text.strip()) + " "
                name_string = string.replace(name_string, "\r", "")
                name_string = string.replace(name_string, "\n", "")
                name_string = string.replace(name_string, " ", " ")
                names = name_string.split()
    
                if names == '':
                    names.append('')
                else:
                    i = 0
                    j = 0
                    name = names[0]
                    while not name == u'\u2013' and not name == u'-' and not name == u'&ndash;' and not u'\u2013' in name and not u'-' in name and not u'&ndash;' in name :
                        i = i+1
                        name = names[i]
                        if name[0] == u'-' or name[len(name) - 1] == u'-':
                            break
                    j = i+1
                    name = names[j]
                    while not name == u'\u2013' and not name == u'-' and not name == u'&ndash;' and not u'\u2013' in name and not u'-' in name and not u'&ndash;' in name :
                        name = names[j]
                        if name[0] == u'-' or name[len(name) - 1] == u'-':
                                break
                        j = j + 1
                        name = names[j]
                        if name == names[len(names) - 1]:
                                break

                    val = names[i+1:j]
                
                return_names.append(' '.join([unicode(x) for x in val]))
    
        return return_names

    def _get_download_links(self):
        download_links = []
        for e in self.html.xpath('//li[@class="MsoNormal"]/span/a/@href'):
                download_links.append(e)
        return download_links

    def _get_case_dates(self):
        dates = []
        return_dates = []
        date_time = []
        for xelement in self.html.xpath('//li[@class="MsoNormal"]/span/a[1]'):
                texts = xelement.xpath('./descendant-or-self::text()');
                date_string = ''
                for text in texts:
                        date_string = date_string + HTMLParser.HTMLParser().unescape(text.strip()) + " "
                date_string = string.replace(date_string, "\r", "")
                date_string = string.replace(date_string, "\n", "")
                date_string = string.replace(date_string, " ", " ")
                dates = date_string.split()
        
                if dates == '':
                    dates.append('')
                else:
                    i = 0
                    date_val = dates[0]
                    while not date_val == u'\u2013' and not date_val == u'-' and not date_val == u'&ndash;' and not u'\u2013' in date_val and not u'-' in date_val and not u'&ndash;' in date_val :
                            date_val = dates[i]
                            i = i + 1

                val = dates[0:i]
                val[0] = re.sub(r'\W', "", val[0])
                val[1] = re.sub(r'\D', "", val[1])
                val[2] = re.sub(r'\D', "", val[2])
                date_time.append(date.fromtimestamp(time.mktime(time.strptime(val[0] + " " + val[1] + " " + val[2], "%B %d %Y"))))
    
        return date_time
    
    def _get_precedential_statuses(self):
        statuses = []
        for e in self.html.xpath('//li[@class="MsoNormal"]/span/a/@href'):
                statuses.append("Published")
        return statuses
        
    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath('//li[@class="MsoNormal"]/span/a/@href'):
            docket_numbers.append("")
        return docket_numbers

