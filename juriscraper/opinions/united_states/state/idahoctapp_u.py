from datetime import datetime
from time import strftime

from casemine.casemine_util import CasemineUtil
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.string_utils import clean_string, convert_date_string
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.isc.idaho.gov/appeals-court/coaunpublished"
        self.status = "Unpublished"
        self.target = "01/06/2024"

    def _process_html(self):
        for item in self.html.xpath('//li[contains(.//a/@href, ".pdf")]'):
            text = clean_string(item.text_content())
            date_string = " ".join(text.split()[0:3])
            try:
                convert_date_string(date_string)
                check = self.check_date_format(date_string, '%B %d, %Y')
                date_obj = None
                if check:
                    date_obj = datetime.strptime(date_string, '%B %d, %Y')
                else:
                    date_string = date_string.replace("Sept", 'Sep')
                    date_obj = datetime.strptime(date_string, '%b %d, %Y')

                date_str = date_obj.strftime("%d/%m/%Y")
                res = CasemineUtil.compare_date(date_str, self.target)
                if res == -1:
                    break
            except:
                raise InsanityException(f'Unexpected text format: "{text}"')
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

            doc_arr = []
            if docket.__contains__("/"):
                doc_arr = docket.replace(" ", "").split('/')
            elif docket.__contains__("&"):
                doc_arr = docket.replace(" ", "").split('&')
            else:
                doc_arr.append(docket)
            self.cases.append(
                {"date": date_string, "docket": doc_arr, "name": name,
                 "url": item.xpath(".//a/@href")[0], })

    def check_date_format(self, date, format) -> bool:
        try:
            datetime.strptime(date, format)
            return True
        except Exception as e:
            return False

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.target = start_date.strftime("%d/%m/%Y")
        self.parse()
        return 0

    def get_class_name(self):
        return "idahoctapp_u"

    def get_court_name(self):
        return "Idaho Court of Appeals"

    def get_state_name(self):
        return "Idaho"

    def get_court_type(self):
        return "state"
