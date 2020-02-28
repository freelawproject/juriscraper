# # coding=utf-8

from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.string_utils import clean_string
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.isc.idaho.gov/appeals-court/coaunpublished"
        self.status = "Unpublished"

    def _process_html(self):
        for item in self.html.xpath('//li[contains(.//a/@href, ".pdf")]'):
            text = clean_string(item.text_content())
            date_string = " ".join(text.split()[0:3])
            try:
                convert_date_string(date_string)
            except:
                raise InsanityException('Unexpected text format: "%s"' % text)
            docket_name = text.replace(date_string, "").strip().lstrip("-")

            # sometimes the records include a docket number(s) as the
            # first words in the second half of the hyphenated string,
            # but some don't include a docket at all.  So we test to see
            # if the first word is numeric (minus the slash characters
            # used to conjoin multiple docket numbers).
            docket, name = docket_name.split(None, 1)
            first_word = docket[0].replace("/", "")
            if not first_word.isnumeric():
                docket = ""
                name = docket_name

            self.cases.append(
                {
                    "date": date_string,
                    "docket": docket,
                    "name": name,
                    "url": item.xpath(".//a/@href")[0],
                }
            )
