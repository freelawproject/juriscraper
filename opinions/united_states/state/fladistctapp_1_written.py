#  Scraper for Florida 1st District Court of Appeal
# CourtID: flaapp1
# Court Short Name: flaapp1
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 21 July 2014


from datetime import date, timedelta

from juriscraper.opinions.united_states.state import fladistctapp_1_per_curiam


class Site(fladistctapp_1_per_curiam.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.case_date = date.today() - timedelta(1)
        self.url = 'https://edca.1dca.org/opinions.aspx'
        self.parameters = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": "R27p8ythvn8bRVobJ9C6Po2drnTlbybfPJ9x7UeUHOwKB4Vx3hWkh7ICcXgUYGIh/FtXVvTCgc0WHLU1cF/V1XhkbfDyUn0IVksYoy8XOC/VE9NED35FWYvjzYx0CFJPwNpCTjXinW+9pfdh40GpT0ALnrSZ8EEu0jvYQYRaBiSirvg38PJP2UeQ16vA48hLUx+jomm9bVs/W+xg48JYex5uivR/7RSwOKvgHYL3eBTOpUQxlifkuaklpI25AXf+tDVzIzUVVoUGj0gOQ0jzq03gS8kWai15folTLe+oc0ba0q6964dRiqkpsjxHYo93PTPRMv7e+DO6O2wLI3ttJ3Q4grEZ/GVo/pOVmKKvczGnutAURm8xbcmWbZp6FhUVZfaC1Bf4LMnZ51CeinHFCiGMimSi4/o4+Wb4y9p1NeeO1Nme7Qznxsg9z4Wjm0dOF3y97T2oOpclOxvPA/+0Mdirk2HvlHk4Ug+5MTgqtPblAUWfdtF0EJadS7mcBDy0VYmIIGaJDS/ijRqT61hSU8EwaTNnoq5wBlSQMh6Z3fXOemY5WJv9w74jwc/PBP/Ue2mxf3OYZP3qvo9N+K1tz8OjTGOLJ+lmed4cinkpWw6lviuefHwECEHeCeb2bjzByneI8R+SQB5xsSafv5Og9CJcIG43ZA8OhPr1Bb2E8nhrL0JtPmGVXh1TzBpF20CFaj5bNBumR0iGXV7OKxFdV3viToyhqBQ5tOhu8Eow+szZJyiwSitldq+uoSPq6nDc/rLgygexnzEquB5dhDqPSxPab0/bH6LGyFwYAkyz4t9VikBYtjM9oG7yTMhH6Z4rS3aOK2AKTKEI3fJFJJidMipgj43BjLePt0ia/djp4/lD0gsqVZeDDOOWNPMJt9B2QIa1Bjavw1mHd0q4B5BH+jGghe6DgjBhozD/r72ckTCk3AzxZQ2JG73Hbi3fHA59Y+6kK65DzgCVfkIeMLs9npioZJWDCbOuooqiTLwaaUiohlAuj22TPc6SzbJJELTlqnzsHpQYsS91LZ1gCJ2MSYYVCMGal/9O+pBIbVDTWJNyWkRSuz5lPL0cnf9/4+vSEiO5IdABsB/7b2R5n2q8YMs3D1FxvqJscewYoK1HHem0e14ntDVhFMJkGAQEYHT3PvQcsMlpoAFfqTzWwk8AZ7Cfp5bAVKUwett83Sm9Ldk+QksPKlS7evt5Rh54MNKCsEYmC7mcYW6QPFaffpgSWrHxvgBtkZfk+NEUQYzALnEiKuJ/V0GxeZFbZAnv9BzwYoOT/qukV53SqZmAE6xRGtzha/fBN9EE8SpYmV+ARDAPzCSQutIgRlQoQAvI5tAVBWg0GY/HtHPgIT3z9w3ClwRK9Oit4ybgY8HI9k69sI4Gscv7vD640rH87YO869dqawBT//NhbuSkmUY11qlI2hjZ0aA7tLwBoBcnPhdDS6L7SKQGWTyBVOD5qSfyykauZQwOXBht8i4r3ugUlzCZEbFhBjqTufOKt0D6tCmmVs4MDtNMOxo8kLFb7Qro8L2aCfq2unMLtBWeDzdfmyZb/ponj2YF0eRRJmr9CbWge8wJvviRqhPcHjtuPwHcVoKkfy66PBDNg8XqRluvxtrMeVfYln7vEoYppi1WnP++1M+Hb7JQy3DphkbajmLS9ZGYekxsOWuqYSuzdbWJPCSgdrpkXtVWhGEfPXX9rIp0SAIN0jj7",
            "__VIEWSTATEENCRYPTED": "",
            "__EVENTVALIDATION": "AwSjONxyFc6VDZxMaMaK61PI38qVd+JOc/sb/BkT4+LGntfwws+u+ZdgSmtM8asEcTmtu8zOi0vCaTqPuqYOAl5o7fsaksWLy0abpvmlxAPL2MR750cAKdZ7YE3u581+N7ZdX/sjL3oYllRPTyl3Zcwpf+4DYsTVdglH8D170HsySwoxhDDs9PiOr3yq4Uxo5+BpYNyE3azpsxFJoVpm2v/+0oRgJXBOIK/fD/FLC7V5RtF+HLidYrMvu4PtTsN0djR0rWPpAjwJShL0a+Zbhgat5To77ksDEPEkeC3UV5XIVylmeLm3mf+DizYIGPm1nEjwdzD+yueI0NOi250v7hsbuGkpiPcneH2+P/PcZB/xpx9/8ke4Cfl2htI9r/KhCApTMIeuIeSw+4j+01CdAOiKu7woHV/SIziCcHXXv+rgToiu",
            "ddlTypes": "Written",
            "ddlMonths": "{mnyear}".format(mnyear=self.case_date.strftime("%m%Y")),
            "ddlDays": "All",
            "cmdSearch": "Search"
        }
        self.method = "POST"
