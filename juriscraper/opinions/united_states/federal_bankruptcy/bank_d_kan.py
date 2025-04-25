import re

from lxml import html

from juriscraper.opinions.united_states.federal_bankruptcy import bank_d_colo
def extract_case_and_docket(line):
    # Try pattern with comma or parentheses after docket number
    match = re.match(r'^(.*?),\s*(\d{2}-\d{5})(?:[,\s\(])', line)
    if match:
        name = match.group(1).strip()
        docket = match.group(2).strip()
        return name, docket
    return None, None
class Site(bank_d_colo.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Unpublished"
        self.base = "https://www.ksb.uscourts.gov/judges-info/opinions?field_opinion_date_value%5Bvalue%5D%5Byear%5D={}&field_judge_nid=All&page={}"

    def _process_html(self) -> None:
        judge_list=['Chief Judge Dale L. Somers','Judge Janice Miller Karlin','Judge Mitchell L. Herren','Judge Robert D. Berger','Judge Robert E. Nugent']
        # print(self.html)
        for row in self.html.xpath(".//div['view-content']//div[contains(concat(' ', normalize-space(@class), ' '), ' views-row ')]"):
            jud = row.xpath(".//div[@class='views-field views-field-title']/span/text()")[0].strip()
            text = row.xpath(".//div[@class='views-field views-field-title']/span/a/text()")[0].strip()
            date = row.xpath(".//div[@class='views-field views-field-title']/span/a/span/text()")[0].strip()
            url = row.xpath(".//div[@class='views-field views-field-title']/span/a/@href")[0].strip()
            month, day, year = date.split('/')
            case_date = f"{day}/{month}/{year}"

            if 'Somers' in jud:
                judge = judge_list[0]
            elif 'Karlin' in jud:
                judge = judge_list[1]
            elif 'Herren' in jud:
                judge = judge_list[2]
            elif 'Berger' in jud:
                judge = judge_list[3]
            elif 'Nugent' in jud:
                judge = judge_list[4]

            name, docket = extract_case_and_docket(text)

            self.cases.append({
                "name": name,
                "url": url,
                "docket": [docket],
                "judge" : [judge],
                "date": date,
            })

    def get_class_name(self):
        return "bank_d_kan"

    def get_court_type(self):
        return "Bankruptcy"

    def get_state_name(self):
        return "10th Circuit"

    def get_court_name(self):
        return "Bankruptcy Court District of Kansas"
