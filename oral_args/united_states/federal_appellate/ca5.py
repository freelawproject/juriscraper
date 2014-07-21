"""Scraper for Fifth Circuit of Appeals
CourtID: ca5
Court Short Name: ca5
Author: Andrei Chelaru
Reviewer: mlr
Date created: 19 July 2014
"""

from datetime import datetime, date, timedelta

from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.ca5.uscourts.gov/OralArgumentRecordings.aspx'
        a_while_ago = date.today() - timedelta(days=60)
        tomorrow = date.today() + timedelta(days=1)
        self.parameters = {
            '__EVENTTARGET': "",
            '__EVENTARGUMENT': "",
            '__VIEWSTATE': "ThQ6OYU81+vxxvljNQZZUl1y3h9Suq8HGF0fxJBKiVrEh/7I2ATNltbPRfswcohpK1wqpd8s3XhU90npQP/VkAZHN/Pp4FIvPRSzpDcUd5g2smvNg0QtOuP7auSiZm2zKjxcfQzZI8mwe4/l/6c4khUCCPLASbi9nW7b5tBZcmzgM/fxwmkmPFnx5nYJGDSaWaLl4QdWQHTx5Zcag6nkNaGdLtmuvCuy3VaEh6aPCKbgj1bX1dhzsVAa8lnPaimGzqlTLdHxlEu3MU/SKmz6UL3HBj6XU2y/5TRGkgWd0SO7C+mRMI1HLYduh70B9YxaglcFzrQxZsqI5iSyt5vFXPalBgsCnVDkUX1WbXHAdd9NMav+WmhBzFhOFATbmNjxjfxusTyN6n3iaR3Ja0IUGu4sIaLGJkyXtMd8A9it4daSQC86LTf9TkIv5kFM9kJ2ermIOx3c8GCIJpdQ6C877WzlwCMLhRmG/caOX3X3wKGGzNaWbODzz7HhFjLIYh5HsFZxqX6U6nMWOnfX59OfWT0BNPrZYbNKeKoBeHXyGGKeEdw4YzDffgSORGSuWMpH5AKLsXNjt+3/GbMT8vh9NPGsNH9QDZTQ3MaMUHfHNnvWQBMCpgXU8DpxdSJnbjFgqbGf+pcaH8tyHk5vxRQyNQid6Yd9s3IhR6fT6vbpMhFGe3fR/MpdapRr04PM5NLgoy0DmMAEa3sn3nwrUwUVKq4a8x/ESLXgXuvypmvg3ZqvGepDGaTb84MT8ZdkLQaZSMBTt8ltHO/7sYZ0vhsedCSQpt5kAgPPe5+X2VpLi2eKLAzof4o/k8AfjEVEKp9b/ZqipEj27q1rRRMIiykV1N9GOIkb7ccK9NlDU9hbCE6eHQD7iPiHUWSfjF7PwvVm1qqxzyRjQ0byYmk+ZLaGGkPxOZWd+03hOHDcpgChSiCgieZs6ueAjWm4sU7yph1cfE2e7jeJtFNq6zIFV4hbU26pN5VMteax60nKwJnFRPal9JXRrfOuwUtutIec4wP8ik7vSuzKxagvVty+taUutOy46JTZQpyfqUreBpp1kVfGJk0E2ugvcJdNYhf5Nc5QoQS2QvjuWXjZexsMmKgmmCAHIbj9alJnpCjP1ZjnlenJ3NLjBbnkM4ENIwDGqJjjEYwE/AJnMITyo6qjR8O1xcxJ0dA84nAraY+nmCIMxjYTO7E4UpczhIzYthk2EEkUxRcbX+/Hoo4ZqYTYXbpE4JZnjn+BRKgumUvjusSAXJPwSWTQLck3SYQWREdJvt7exqNCdxfFqO3hVsBFRRPWS13ayzz8MTTpYc2U6Smjk6mzgOtRQiH92UcBq6Kzp24T3uf18Su4urEU2dFIxdywmMuQ1as57M/It4eMBu+VhPI=",
            '__VIEWSTATEENCRYPTED': "",
            '__EVENTVALIDATION': "7cSzl+gTvvoWXDgq3aX5tYDK3qLW7b5b8nacEEuVj1uKWVnaIc/KW3FmibaraD64MqQZkrdWRuD55r08X2+Xniq4lh5O15BeFkQ7L8MnpMUXTSkC12M+8rY9ZnFiWm93s1K0hx/SHskQf+iQojuS33eEgdDdMat4hji5BEDPr0vXxLBQuUo1jFJN1vieIq8ybr3vdi4Z0rCiQZjIEynBuU4hs/6OeiQZEyyNE9VwH9VhFG//2rkL/jvURX5LZQEsxChr0WmQfcRo9hEHi8lAt9La8o4PnNspzw8KayGc2bETsynkHqs63ThTfT1f8V1F",
            'txtBeginDate': date.strftime(a_while_ago, '%m/%d/%Y'),
            'txtEndDate': date.strftime(tomorrow, '%m/%d/%Y'),
            'txtDocketNumber': "",
            'txtTitle': "",
            'txtAttyFName': "",
            'txtAttyLname': "",
            'btnSearch': "Search",
        }
        self.method = "POST"

    def _get_download_urls(self):
        path = "id('tblPublished')//tr[position() > 1]/td[5]//@href"
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = "id('tblPublished')//tr[position() > 1]/td[3]//text()"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = "id('tblPublished')//tr[position() > 1]/td[2]//text()"
        return map(self._return_case_date, self.html.xpath(path))

    @staticmethod
    def _return_case_date(e):
        return datetime.strptime(e, '%m/%d/%Y').date()

    def _get_docket_numbers(self):
        path = "id('tblPublished')//tr[position() > 1]/td[1]//text()[not(contains(., 'Banc'))]"
        return list(self.html.xpath(path))
