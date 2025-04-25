import re

from juriscraper.opinions.united_states.federal_bankruptcy import bank_d_colo


def extract_case_info(text):
    # 1. Title, 23-12345-JGR.
    match = re.match(r'^(.*?),\s*(\d{2}-\d{5}-[A-Z]+)\.', text)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    # 2. Title, Bankruptcy Case No. 22-10521-JGR
    match = re.match(
        r'^(.*?),\s*Bankruptcy Case No\.?\s*(\d{2}-\d{5}-[A-Z]+)', text)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    # 3. Title, Bankruptcy Case No.23-14384 TBM
    match = re.match(
        r'^(.*?),\s*Bankruptcy Case No\.?\s*(\d{2}-\d{5}\s+[A-Z]+)', text)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    # 4. Title, Adversary Proceeding No. 23-1223-JGR
    match = re.match(
        r'^(.*?),\s*Adversary Proceeding No\.?\s*(\d{2}-\d{4}-[A-Z]+)',
        text)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    # fallback: search anywhere for a docket number
    match = re.search(
        r'(\d{2}-\d{5}-[A-Z]+|\d{2}-\d{5}\s+[A-Z]+|\d{2}-\d{4}-[A-Z]+)',
        text)
    if match:
        return text.split(match.group(0))[0].strip(', '), match.group(
            0).strip()

    return None, None
class Site(bank_d_colo.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Unpublished"
        self.base = "https://www.cob.uscourts.gov/judges-info/unpublished-opinions?field_opinion_date_value%5Bvalue%5D%5Byear%5D={}&field_judge_nid=All&page={}"



    def _process_html(self) -> None:
        for row in self.html.xpath(".//div['view-content']//div[contains(concat(' ', normalize-space(@class), ' '), ' views-row ')]"):
            text=row.xpath(".//div[1]/span/a/text()")[0]
            url = row.xpath(".//div[1]/span/a/@href")[0]
            # text="In re Peak Serum, Inc., Case No. 19-19802 JGR Order entered December 8, 2020 (retroactive application of SBRA and CARES Act, and dismissal v. appointment of Chapter 11 trustee in jointly administered cases) 12/08/2020"
            summ = ""
            date = row.xpath(".//div[1]/span/a/span/text()")[0]
            month, day, year = date.split('/')
            case_date = f"{day}/{month}/{year}"
            for p in row.xpath(".//div[2]//p"):
                summ += p.xpath(".//text()")[0]

            case_name, docket = extract_case_info(text)


            self.cases.append({
                "name": case_name,
                "url": url,
                "summary":summ,
                "docket": [docket],
                "date": date,
            })

    def get_class_name(self):
        return "bank_d_colo_u"
