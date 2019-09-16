# coding=utf-8

from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.string_utils import clean_string


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.isc.idaho.gov/appeals-court/coaunpublished'
        self.status = 'Unpublished'

    def _process_html(self):
        for item in self.html.xpath('//li[contains(.//a/@href, ".pdf")]'):
            text = clean_string(item.text_content())
            text_parts = text.split('-', 1)

            if len(text_parts) != 2:
                raise InsanityException('Unexpected text format: "%s"' % text)

            # sometimes the records include a docket number(s) as the
            # first words in the second half of the hyphenated string,
            # but some don't include a docket at all.  So we test to see
            # if the first word is numeric (minus the slash characters
            # used to conjoin multiple docket numbers).
            docket_name = text_parts[1].split(None, 1)
            first_word = docket_name[0].replace('/', '')
            if first_word.isnumeric():
                docket = docket_name[0]
                name = docket_name[1]
            else:
                docket = ''
                name = text_parts[1]

            self.cases.append({
                'date': text_parts[0],
                'docket': docket,
                'name': name,
                'url': item.xpath('.//a/@href')[0],
            })
