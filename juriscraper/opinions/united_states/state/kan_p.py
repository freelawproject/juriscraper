# Scraper for Kansas Supreme Court (published)
# CourtID: kan_p
from datetime import datetime

from fontTools.ttLib.tables.otBase import have_uharfbuzz
from socks import method

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://kscourts.gov/Cases-Decisions/Decisions"
        self.request["verify"] = False
        self.status = "Published"
        self.court = "Supreme Court"
        self.last_date=None

    def _update_parameters(self, page):
        # view_state = self.html.xpath("//input[@id='__VIEWSTATE']")[0].get("value")
        # VIEWSTATEGENERATOR = self.html.xpath("//input[@id='__VIEWSTATEGENERATOR']")[0].get("value")
        # event_target = self.html.xpath("//input[@id='__EVENTTARGET']")[0].get("value")
        # CMSCsrfToken = self.html.xpath("//input[@id='__CMSCsrfToken']")[0].get("value")
        data = f'__EVENTTARGET=p%24lt%24zonePagePlaceholder%24pageplaceholder%24p%24lt%24ctl07%24UniversalPager%24pagerElem&__EVENTARGUMENT={page}&__SCROLLPOSITIONX=0&__SCROLLPOSITIONY=0&__CMSCsrfToken=Awm0VttxDqS14wCuI2Yfr%2FzuogyXvi%2BSBwg6k01FhPpREhWujN82S3zTkh%2FJEJjjpAadCE6rDj1g0y1BzmtDWWPkpcM9MdjYet3Jm2Q2WHI%3D&lng=en-US&__VIEWSTATEGENERATOR=A5343185&__SCROLLPOSITIONX=0&__SCROLLPOSITIONY=2447&p%24lt%24ctl02%24SmartSearchBox3%24txtWord_exWatermark_ClientState=&p%24lt%24ctl02%24SmartSearchBox3%24txtWord=&p%24lt%24zonePagePlaceholder%24pageplaceholder%24p%24lt%24ctl02%24OpinionFilter1%24filterControl%24txtSearch=&p%24lt%24zonePagePlaceholder%24pageplaceholder%24p%24lt%24ctl02%24OpinionFilter1%24filterControl%24drpPublished={self.status}&p%24lt%24zonePagePlaceholder%24pageplaceholder%24p%24lt%24ctl02%24OpinionFilter1%24filterControl%24drpCourt={self.court}&p%24lt%24zonePagePlaceholder%24pageplaceholder%24p%24lt%24ctl02%24OpinionFilter1%24filterControl%24drpSortBy=Sort+By&p%24lt%24zonePagePlaceholder%24pageplaceholder%24p%24lt%24ctl04%24AccordionLayout1%24acc_AccordionExtender_ClientState=-1&p%24lt%24zonePagePlaceholder%24pageplaceholder%24p%24lt%24ctl09%24AccordionLayout%24acc_AccordionExtender_ClientState=-1&p%24lt%24ctl12%24SmartSearchBox1%24txtWord_exWatermark_ClientState=&p%24lt%24ctl12%24SmartSearchBox1%24txtWord=&__VIEWSTATE=ZZnI0eb6RJS8gUUuaGDhxlJvBbXvxn19RbzGZNBv2A%2BcEAkeRlrtYwEKVF19bOnbfrNpcY3eyYr8r5%2BelIwE3WTT5IdzDPD6qNpCTdPh2E%2FId33GmtUN%2FK65FHx%2BxnroveJziCFNJFBEdbe7rtUwXapi66ZRxb1ttOTd8cVWcwzY%2FsbU0xVm4J3nkhXnrv%2BAhYzdHV9rIfDA4Kz32WYZXNyVa1t%2BqWeiILG2P0xzloPwpLOLPRyfGH%2Bp7fmNA0nmUGh%2FHlQIWImp%2FuOc9g6fXuQoORZKjEdCUNORbsj1oBvlWZG4OAONu19w%2FeIrpUJj8HvsAe3pAzf%2F40EGoEI1aWnWFtP9z8ticBgJtW2e6mBsCGiJ8AsSLXeiL2SKTyD0FhPskINChPt%2F%2BfBmTgo%2BHsJ4iL%2BQg19kya%2Bw6LLyCHZeLG8S2X6ZHByiANhcivc4tYAysCiBzOSclgXm48wV2T4qqY0aOssUkpFkUeLyBw9YaM7LXE0MO7WC2A9q7xKRifiQe8ntxVf2FMygkP8YltyTONZ9wSxNHETGQTtLq%2BlYyE69D5l9G2dSASM3g1MaOFO5u9PkdXXk6%2BCGjmBlX48m%2Bh26LCZy%2FwxTRJc%2FElAi3XwGao5Ybr52v%2FdcIzm9q7WDdg0wtQqWlwnYQ2FpdMpqHSvpOJn%2F7uH%2FErxzw9%2BZ9mC%2F1xgB4tLudVDKuNW9dE7GQzcAlyUoeqwdZyH6hfcPRzn7Age18yLAXt1lQ3orCDRyeyASIUODpu09EG7B8MR1pBHaqPO9ALe21QHuU%2B5iBIaMWuVfMgcTYFrtZGD3krfy0sKLDq%2BQqANZfdJHuU6lIZOoq1M7yvYmiHrt35VaGdQlebC16Ga2Yhcdj2svWM3l5%2BCGTyOAtLhiD9bqHyjIG3PedmAhigGuP%2Byrb2gqBY6O9e7xgINbGzHHvU9zevo%2BvnwXmIMus7o%2BJ1Cy%2BcBOntNbROKMpwl6NL4ShtRrKtfcIFXBfmbRwOOpuQepUONi8eOGe9ytmJ%2Fv92y0k5y06zAVYA3OrB1CPOJQvbEDxoKBkhnbN4AErE%2FFCIc1ql4mc%2B62lwci4brpJ0eh5aej%2FtsfDta61JWJGHF7QIIJ%2FiMTqBJGBtae%2B12PCVoaWGf%2FKW5JVD6WBySHazfeOs922jABxAnX%2BrcDKa6HmX9ZBCVCAcdlQprsGaBjhjeZvkz2luLfxsaCKl0fjafNRLXDSMT3oGr2O5YIpk%2BVHf%2ByLqBS1Es56HoVL1bFr9bcRR1xpdwrTN%2BZQXXLE7K9ztdqMz5N4t4TVJcnnBnb5DO2Q7F4h7DdnJ%2FgBXA0rK6bvWteCXaT5%2Fkuo4vMG0BwiUrVDeUW1TLrblDWfqOvb5cpH0q%2B1oF5alE8ei9AKgLvZhh7xY%2FEIMNUdphxfJGfisN9YBmvlGv84JXk5zNLbGyoMnF%2FzhutlXX3tpiGNL6lMPI48Q7yAfXlNhQa7DM167%2FQui3pVrOPZM%2B%2FUzVLt4k7equobxWQWS%2FC0kK8Ny%2F%2F8RI684CBLDPwmKKSP%2FIMGrklYVMXmt8zNnXblm4VpeOSq2Ja2OtteCBfOVxrI3Hx9tATRuqTcM9bfqA4mxwW5nd9YAPiJc5IJNqAKUvO%2BfmJ9iYMiqjmye4aUzJ6OAky516mqjFqvjLHOguDLI3T2UIEIQ%2FqaX55lFbhRFMChHmsU7YliJ%2FvJR62MNRsRwSyT%2BrdX6Q8rur9%2BUMpE7XzJCRjiqKA6XMVGNE9bbdEr9SiBc1w6jGAmzD7RuPRMY0jIiips5PQQjpuh5BNVGvA7FzhEmA7LlNBBgOw%2FVfRWhflV3bld5cHpjsOMW2gXa%2BdyJ4FKYKverQncxUOWQ37fh%2BrK%2FGuIwuhTVNptrjDGmgftMUdK1soSaDrqsicooG0d21CFNr12gQh01hBspXySNcZovJk4lHt%2FCi81I6vNiTLLnURQ6gomYl9esP9W60gBbRcGkkwrp1G%2B1DXVyxwNuok8PoYEtQwFu22asnoA2P20SVyOgQ5R%2FxuYGTMm02kO7AKrIdzL6nzoRFe6G1F%2Bhcii2ZRVDf2dqofZ7rZcCCIexmhQhBrFTQw0nek%2Fitvfcjs5ZNRCCX6PRWmbO5NHEC7kfeYU%2BoTK8q4FDuVnyQ4PwCvkTmZmDwk%2BDmpV5p2GVnoXyK1SZYo3pBWAZvROFVOEO22iuRvTOidqtdp1q9DBQhe4dMYYqAhhCB2zNXKiS%2F3RaPJG50WU%2BzoV0ah5h%2F4TOo3gbacoBA0nPsPeO6I3KXrY7rN2J69IQO4nKEfH5ocbzWtIzX2GIiuiREBWZOggibJl352nKBU2oE4XS%2BnobdWC6Q3kYm43xPkixQkDnj55UnpJIW5FM5324Re9tLr%2FhhTe9c0mYbtOu9s3YwnbmUIArwuwNLsCIdNyqXB8g0i57Jdrm4qZFdT5er2K8%2FI4BSm4I0FOOHHwgUNP348ErNEdFNRV9jNNT4b4X2sY8dMIUy07CQCogCQuuIEKXGTWoISzmVCVmij4%2FYzlzKngERqI4uqOnVMIYfKaD9zxgAukBHlKGAthHbCRwny4Vb97QVdkah%2Bok3jct5XUA0KEfoh%2BzSnICjphHwtjcR4qyd8F3ahdIbn1S6k4X9mCpc2rYnNRQgdT%2B9gJqBXh8QUeYh87XQ7jC4TEhE3HhII8VadM4HL6kJ5jlBVMz3j3LfieTCwrKsQV3YAca9tQcQzGtfhh4VVjKJe3gFBPXuZOwmfkgoEvkjLaXKXtdT3yVx6%2BltRoyfVTztDN43IWw%2FD7remsMN6DbIIaeTiTo%2BwRIY2Z9WtwWQZMxedA0O1cPc3aegCVMjQUyj%2BCBAzhS3Od9i2RVQcBUVlrRQ8H4ybhYRHloYuuQPWg%2FbD%2F%2Fya%2F9ALjlmPWgNc2QLkoa9h6uukw3lYZRvRABzyJmKUve6B4ed4uTOw%2FJ3nCtCgw%2FrKL71hZpsIlhT%2FBhTv%2FiHosu9dnLo9dJ%2Fwoppy%2BHx5caoLyvu3zc8at9V%2FiAnrK%2B66lkS9HtN7o9xn65SNhDWZpNemflqYY1PmoeFd98oWXce4qYa%2F%2B4NtAOp9%2BtaJv3hswPbH%2BrWhFGojVYisp%2Fs6jmnfLfvP7byHQRGxbHS76Aosbe6g8rTnwgui%2BFgdJo0WJOnpXV6HdY2cGN8TBDtLA9jMtDYNIXcGrsZVtoIj8iuNLzHGysRzInwxiqPrdCGpyzIeF4afauHx82SjOOhkYpU8jpXRJIMSbMmJj%2Bz4QKqq%2Fn4EJeTdQGXvzsLvqCijhpJBPuwuYDWfCwJ%2FD4KoVZanYbvFMp%2BA8WhfoZfyiPjs1lXD3AwSCSan%2BgGnquopk4f6NQpphNNsgjSATIxDwLmQmlS%2FgJZ0ZK7VmiNabfccqy4rlVoKKhgmplO%2BclafG5B%2B8G9Wwn%2FG9aqfHQw9sJyIx%2BJPrxXusIm0ypm0CJkw6FiBTvIiIKGnSp0eWuLD7m6L56UnlWWWFbmw4SviTcis3br5Skj6AubzUh5oG%2F11DpLiGavKfmUPblGQ%2BjnWyR%2B9dkaY%2Bl0XPik0wOy2QuvMHjxFdt5%2B%2FAGP%2F2Nd8%2Bl6%2BJzeRwgrmUArIQm6h7EU%2FEtan0tzNmYxc3xNC4D4i3wc8kDECEErbhass7WHTMotZeIE7emXUko1y6ofU3dDp8U%2BtulwFTbwhEhmwDNMjMof9pHWLGWahdoOiEyxXvahWeTb7aOEFn1kxaDHDb2L61Fko9LM23O2hXcYWHBQ0DT90BWmczeFyEKq47unPIibgSrqJ%2Bq0%2BIaDTrQJ6P3hwZhwlXhoRCIfoai6vMEBTdylXrskiS%2FbhQ0bRtjMnZQyhYcz%2Fck1oR%2BrrgK5ZkV0%2F1%2B2pNDItxa8O72vpiCK8ETdQyjcKsHoBMXnSsif9wWCv%2BdeBfZVfHZtIu4%2BI73tVVI8YPZVWHsCR4ydSzSutmN6GbCCcgqgPTiZjyg0RExX5qfMf4qvyI21hxV4IJy5ktM2SC%2BJM4IXtUXLm6FQBLiKvKIfb7dNHXNnd8%2B2ID1j2SQIUlBZoJq7A9ITlNg8RWH9qUIhuEAghraRL9pP4CEXOk%2Flur%2BaHyjwHbtbldrG6XnIsNS55GQCgvedIV7yN8gxu1u0NIoPLg0fEIwKgYrCCQzTKPi%2FklcgQJlKJeASw3EVLWZN5RnglHZAPzSJ7ripUxEDxCvQQxMTfSJjchwlV6YrGNjrqyy944X7XW3wnWQMPXXH%2B2kUFyU0HoN0aUaKdTL4rjuMfLzDn5FxrPhZ3A2iLFxnbGIxBwVGTYaJV96n10Gc8i%2BUsUbs6GQCCv3oa0RCD1AmtXIT4g3zhgDyfZrKlW2%2BWA44fLoCwA%2Fvf70v%2F507wX6s%2Fg9dX8mkcI9gG4PE3NGIsqmTJWbdHW3LYs9Iun%2BiEQrJbj6WV9Kh%2BA2cRal%2FYmp9awb9SMv%2FlLfC62YqiLVuUZJjFaAkdbwF3N4t1gxzoWd9K14QMAI%2FXaVNovdND3IksL4gjSqD10Fl3vgmZtfS5Lzv31cLJ8TQ4HqOEakDpxe4ifoVGp6BzoHWhHnH5TKm4NVSS6PumpNdMroOHhFecqds8YGzH2xHX7KxRbXdJv7hBtC3V5KdFOwSE4vhK%2FaxFaH1byyszCtWnUQ1LpBpy8k8waqIConcFLYeM5TII%2BTgP0twCG8SPGMWOApA9Sow5Y0oPqyOJVupmC8G8goaRB8x23RltpkUXuDAzRtt46aGUc9s9PvmesK6epW5D5X%2B81Pn3bXeBjDzdGN5PCm64VD1%2Fy1WHn7kKiAZTnANf8ouCV8YaKGSObvPT%2BRM3YwJDHsaaNMee97AY8HZQ%2BYsvEJyrGH9YpdF3m69YY8QPQpJ3hYbwlCCXLocb3krdic19SL7Mm70dxidactKGe%2B1%2FAmif5hOlYYc4NGwdfdvqI%2FHJmHRj4JeJvBcF14HL7FDHyKRP4TRHZZ6BDk9vrYAi%2Fbl%2FKqVmceQ9H214b0%2BNReAjp0PHGLkJfGLsDCTkqVIXTypNRj6clPNUkGM3kN8igyU38g2%2FXRMPbVcDd6kqnRaXv%2FF4RcvO%2FXUTEHaMISVv4M3fZlfouRsz1MJIZecT%2FUd1ZlxjN8a%2FN3Q3tHlHJ%2FQs2N785ufis5coEA92rEVk1aOOP00DiaCIYFm72n5xehA6LT2%2F0dNevDSwyXYOJrLsTGJtwNxVYsR6D%2F%2BU16HE4h%2FsnrFqaKkqlcsTh4XxbM7bqp55wRXdbaSQhE65DPSoV4%2BPG%2FGrC%2Ftuu5p0S7QrhMLJaZGA6esVxGFxffjGSFWuWQVHDv66IHfQi0d62YaXZ5ZwxPDzVgYPGIbT9uEUuBUiSVSdOF4624OW5tnPyY2HWXr8gTRMcevxg9om8LFlJ77C%2FzLWrx46gZKbo8ZwJa38%2BrxM49Dhxmefw8fcvIOU%2BRODVCSNjcARbt0AU90XdnXFtJNVpsYsoGjxyH1hzaOJKk86hx%2FmKlMlE7OOUSYq9p3FuxiBSh0Y7%2FxzASeu27EHc0wMedz9FzQ6TSpSxTUIFZRbdHEbugRbRXPUtHov1JxYs92X4RYcJp2FoKsRT4fF4sauYCqdHTrMecdom4KNl3CBBIDt5hnEMncraUPeH3of8nJORI%2Bzpo50Tb08wB3glIRY7BPgNoZmqC2Q4UAG8wznE8h%2Fy9UZ1ZD9AOsOx6ciWslLBZrMy%2FgDaTS4XSNeXUuW4ENwvFWRiloWEiLEQa7lM5x114zsXd0wLchbumhJZwA7YhGmESY6YGqshFeNvDcqS5RwTI81xZBuYRfIqcCSNQt5ru1w0gYahFEd%2FMG%2BFxbhJayJk3pwhE30NYPd8jINIvWt1JVSzztq551VGct3WqfPSI9I9w14yW9%2FfUoI%2BjIlv6N7xXn2NkMwyofbVvBGxaxrHemr1dK1qvcMoGJbCwI7IKcyURfCH68BIfElx0YCc78h%2F0E%2B50j20gIlb3npczJZ0hv8tT94rZKMcmOPZCkYjRRCgaRVIpCtJ%2BBBbbFpTlnYztBD7EuWeAwml1m2NG%2BN23u0pZ6EYJHSWt7sp%2FjYQJjGLpBWmv2lzxS%2B5dzKLNEcgUMmb5Dt1LHYrMpYgk1Wf2mbX82uLzy%2BEK6Cce6XiYhTtn3GA941ypas5bCeu9GVc136AdvCRxXuoVGw%2BS5emNKCoIDp6mPUVVVqJFVIcUd9QX62SqQXL8FA4w8lVQrdQgDDxm8zG2gR1qbDvW9Qgb6ACCdQu3ao3byW5yU29ggta33IsIAgRr25zl1kF46xLn9o9UDKukoPhm1gdwr6Zb3i0LqGAGrZjnqT6J%2Bly%2Bjqv6g02ggILeJ5jiez6VoufQxa%2Bnm7WNII3ql2HbmJfGiKRsHSHguUGdSGRXepiqipfkPi8oITMSyuLJZAzqHonQNYXS1xeh58c%2FNB88ID5teBhjheWu5UMYuzW%2F69a0NPjzXeKlm%2BbKq2JEUldC65ScjJWBCWy5T9qD695din5GmLTfDdw7AnJ1qVzQZ7%2F%2FptqQ50u6Lh8ultmD1OHli9CYCU8alNFuqclRGw97991tkBcTkyn2Pf5zveEtpPG%2BKX8XjpR5xsYQio1jSJnumDZUiwU2v42xhBt44%2FxOPjoWYrnBaCmQ%2Fx%2FZFVDsO6t9LVrjg7VEcMNwwiZKuQtg%2BF41YvcWQLds%2F%2BcYrwAV4haLs09OULDZkAN3OwjgwcdiYUh27EpHq%2BS7mk0%2BXPAPweGvFPDfcwY0o3eDWFRphv1RknzB9C4PfJA8MFJwQi7aGx47W2FE%2BodiTbxiLx8ILGrvtuECv0y%2Bh%2FCTAOT5ViYZtP7qVkJA14zgEzNmElyleFteR%2FJnOz3OG6yYglOsGrIWpqNg1BNtGKY%2BhWMYW5KVLfotBKpOwyJ4p6Q5TZiNoucD%2FY1bIv9Miy%2BvAIs8YCSjcD0OXgwGLkGZihqcaKM4CiEBdN%2F65QpDjb2ZHCaBfXnffbHcmBTxiVsB2owr0zGgv3lm8J5Xa%2Fkp78tayVccikAX6PhEFAgULdDfyuz6OK3SjA8E9oxehdyExU%2F4U7RSk2UOXpH0GzOiBZJ2PBR7mx2EE1WMp6ahqmXnJYoe5UA%2BUUrej0tNQ1OpO5JIaUdKOYQ4lw74c9rGi98nk%2Brq6VRXtgHCZNDR%2FqBfb3rlML43JTQPxF%2BuwNX4rhg3wpfVCgme9n0i0SlaaOLdZvNHF4M60YxbUGuAzToRQUXHpywxDgfW%2F%2BGHLB0SFv%2F1v3HOvm97ictN0FXCeQPv8cHV8Mn1j4VpZamR8ui68uXWnWyjr524%2BW61drT4dpMEx4pFTALXG2gWA%2FjveLxAu0IvxDjCR%2Fy6BqorNFFebTz6548ymNjAsPqdDvghOdTRhZ0J%2FLkVRYFWblN3xm3uvLVd94fbqrLNJ7tSM%2BQFZRM7metdxAyLDtt3y5bd%2B7IUessY4bg3t6UwVEmL5W6jVDEeoeGlwQtMqsDrYyCPB0ZjvLSE2Vi%2FQOp9tcy4VAVyP6OdMUBr7XeMrO55V%2FtzFygurrKLdXiZ8mgAh%2F4MPLX4%2FfXzXuicovPqGxrC%2FqtMjxxf89BTGcFayoTUaysKQwgP4I4U98vanLmTAPCgQaOsM%2FM0xUF80vmz7P3T5KcDIPnvi7JpS9EYf%2F9971RpjdMmMEqirZcGieWywVxztR%2Ffrr6afsjKV8MyJ6Cfa8V5EqCxGsBGBetIZcn4NkywKcuII3O7yccPdetBnEySs4OUHIcUP2VsFiKm6KD3eizAxMgC6aRE%2Bken45G2Y2QdvSnDwFYSNdrRV0kR1NXyNB4ocvCd2Jv6arRtaXVW2je8J4c91UpyWEDsEaEhQyw6swz89%2FQ4jME5g53KKOVmhIiuVI6ZER3J5AThrDDZduIjwOoRN%2FzE%2Btw7rj1u%2FfVk3idSbjbEYNU5mFbatn%2F%2FEHoiWQfIAR5bXB3Xo1ZnVXBL9Jo8G21KyMrcPrJl%2Fvf0kk5%2B1FUtqPEfKw%2Bu8itYxR2gz4Md6Ddg2%2B1jrPzrLnLT%2Byo3TQu9UpKBTWLx6edD3Ix2ZSDEMtKMHniLc9%2Blb7OHo1mXa3QPHT3sIjY8RlQjaruJhFuZ6SH1ikxqocdGzjgBUYjFLlPWnykPBl8XyylzC1UljGcI6AtGlourAtBGJUYhK98LCaENE29tIROPXz5ZS%2B4BVMN%2B8Jbw4K%2BkwMHHPV69bOse%2B1rIbmESHy3FnJvuIzhklkDmoHZdjAvJe2gyYldmymGo6tcc8OP26txPZ8w8UulKuAB0sBpsnnmg31NCnexMaXiIZGdN%2FfcYBrC%2BrpgtvFnbWwwvQtjumyfFB7LN0kAWhyWSz0teDOtyLjY1sAB%2BoS3DW476l1TbJHWIjkH5JYCuJpagE3hjCj%2FSSRkGevyiqGkWeA0QSCPGhQmi3%2BvCIOt%2F4f9deFH7dCYgokUsGO5Lft67%2BIsHJ6H39nVsLXWR%2FUAS4aQGzkWiKeh3yA4q%2BuU2weQJqzYvjnUq2jParSBAM%2BELxRu%2FPpCjZQDORERleq2cTK8p1uyomQcHKCDbZR6wksccInPLwiZdFKC0hEEhg6BKEUUa8mbc51R8Hh6pN8ixH0OvKLONfAChIl2ahxWQpBIodW42VzY6tOcN8vPqqUZpY2sEI6aK%2BygI5F34MN1cj97V7cKu6wuLtq4WZyAiZ43T7YAUvd%2BexhFJ8Dak5SWjpYMubxua7luRGOq3bX8PVDnNNi033JCUt9i706F4TIAQhVLTWp%2FeBS0C%2BqSoDApdz8BFi8EgQevq9GNr6Lpx2Ye0NEmXeTzNjIQaAZtFvok6OPam%2BHUVDppI7EvV6UrK6e2xuSx8s6EKFhgtT%2F9lPHIFkvth%2Fq%2F09yJti8pFeK7t0%2Bi8lPQYpuA%2BKM1gcMx5IWoQip6TLw5Gq2%2FywG5eiqga3RuJ%2F%2Fnwyx7eJfdwHmlegjMeFWKHqYVU4Q4YYiTini6IYAaYhZtR1hYKkEetnFLADetQJBAYUHhkHhFy6Uhw468OqlggKqK%2B2klS%2BlU6DWzu%2FH6Rv2PH%2FIz1Abs6QxXSuMxlo4nT1ZDpYYRgJBjxFdmVXGlTNtxIpaYHLLsK%2Bk%2F1LVd%2BrMOoGGvr2xQtiz65gCneMvT9NYVKd3oKwT%2FpNhff2UQn82Bx%2BUVXxU9STx7TyFOh%2FYkNvSUELUYtHEZirKbMcEyTxvO%2BcMRACpox4Kg%2Fqsr%2BgipMlZkgvotBx7A898WhxSIbzVWYfevKD9ElJ8eqYJtFi9mnVy2nvkYKe5xnxmRU8PzaJU0wdOTfYjPIqAIQTNMUTC0R7BDbmRweigQhXwSb8qh9HRv8xxOn8a5OLNeFeDUlp2UTI3sJLY7JhDNmSEUknxeCr258FEr3G1dTrq5kBCIeCD2w4up4riJYOX%2FZmtPsdnGVRopv1SaBMtgXrWlVj73byObWGiIJf9zmB0kRal9xPEWxvE3o8Bb4opHpzFrX5zkuNVLDhXYY%2F2UxqLPSDcMiBEqc%2FJDcefo%2BSxOGCInV37Z2IE64dBIDOch7JTDuC%2Brh12eMDFWsY0sSNVBTdqP8UO8ofDtj4nc1oWntuXnkxrn%2FdD0bCxBEF2hfX5uQidZhmvPjU%2BJRWGbpgSILQ5Kpi6o9UWTmb%2B%2FemG%2FJiFbsrLn%2BB5zNeM9oHrj4U0igl5s41cmeNquUngXZ6SgFYBaSPOlFEeJwQCt%2BRv8tY8NXgm5RSAjzrXrz1KCp6Ca2PkmDVFmK%2FXqElGJJy8aBdqMZn82tD37UDcYehtgxPpp7%2F3l12AKI2hqUmvU9egA%2BCmN2X5MlOc3XQMhe4xP6QnOxEXxegxDNiXndExrVcOLMpC2BURCjMuc5j39Pjq7oRCECCNBkz68ibJtQm7aCQ113ndUmcdTpIdPL2cotbYD33enqZQDTJ%2BWoOWBhO6Sap8LPdqd%2FOTkRMcxMsSTOz0zDBeR1HrQEFmfIfn2VmRQwNuXNeT2lvMAQV8Pmk1DLSAD%2BttltThNQ1UQp9HyjK1DunuiVggxNhIDyHSG2XVUQWd%2BrBZv%2BAwPqHQR1objt5C1MaBJWqRyHCBZsOpIqcHWfIOoEOQekfRpP2tHi1CBuYSQVqB4mS815VWqxDyKqRvFVxzNg2aQdx1J%2BZTK%2BTmjv%2Bwq8lAy03I9a1d32YuVIzir5vCLxsm4V%2FX516CDB8UuubzqN3Z68SAyjOvDsDwKa006OWzTpwwmqrjrWfX5H1jNhxpnhvgi1VWzJs2H5qrWk%2FM3mgLZXV0T%2BxDrFlHJSCgflA3rFpkaH5I%2F1hEf%2FHZcdMkNwCS5Qw65j5G%2BVBQDr8YHzEIugs6JPHkFa5ibIsjXrXv8oQsSbwXgy2YVRlne7PMVPIKh%2FP%2Fq06aGieMPokedzp5yH8L%2FnttCEYMoDOmlVqZAmyt9lkVHl%2BAu29bQBOd0TUNQhLQ5xgTJXOso3ju9I9T6rTX4krukj8MG8rtVuLcyVXlXjfN80KFDWMFiEndNfJWm942VCOFZeshc0qy3uVrIVkwgop39gb%2FL8TIMdxSGdlokEbVlkrBEeF%2FvGg3O%2Fr3MaNYD59EKrJqvV4UgyWV5iSWvfDqPnaiZteNyow8%2Bx7WUJV2pbs3Djs2quQEtGV9WXnnW2sGxD51Zo%2FLOYUffmCiUojJHcR16DteBOH265vBcQzbqts5bE5TsmD9dedWsO6yExX8bSwbSs56lYYO78hx2E7Ak9MY07DkV0luyJQzM6%2BeUs7%2BvAc1zw%2FnwiaDAPdUcIvMTbG0hQ20Dm%2FDnD7KaYkW6bosQO6oz3Aqwq8XUTc6Dlq91Y5XwHd16qkH97sDXOSADNkCsEyGYsTdxPC3s3yGdYVEurvL8W9rpBopMjMDSVNCoKDiyca65CYhxe95T0mAUv57O5XjCHBcuw5gYY151yCbkOKCLMjTyW6MJjRv95vvK1Uf9JqFvk9sZk3s%2F1FYoWoJCA1lnoKC%2B%2FDz%2Fn9NF0N9%2BFY3Y9xQxUptWBioE%2F%2BtCwJOgOL3PislLgJeGFffq7lhIDd5t8BDdkpTNsk6tAm8J8FGOia9VFohgy1cLEihOVK5%2FWQljKaPQuNrcvtiKCsc5B4tuzJ9YiW%2BFbozN3mUbSonrmTMU8fLdir3sGMtFtADVlEIDuP9RX046hXgfKjwENsrHBuSoCEOplmVS83F1c1p42P0Z0I%2BWZgOKBdKEE8So3EEYLi0Pmys2jZCOGN%2BAABYlgPA8VZ%2FUhgJRFyuqgYz6hwyoHZbpJcaZGb2M0VcEq0nOc0XWxS0xL2JkQ7CvLE22PqqBJ2VfxevbFDvn2OE%2FDsxdHirNZi637Of%2FefqGUymbF0ogfIEQlCTMiTCCN7xQ5RUwMWtXUW1SS%2F8WuAWc2SovmFcbFZ07Rn07pIz7ODUJVcYO7KM2XBN05ILrxNcRQmxGGSYvZCN26ax65vP7C%2F1Qu15EyI3Z2V%2BV59VRTZFfgbdkV8FMwZh0QoJFJOIvYb%2Bu5aB4%2FQGawOgkIr9tW9OqTAUFjqpZ6khe3a3nht8RK8EJnJJUl%2FNV8yOwLxb%2F80QTgPhPkxpqTS2oAaB0Ou9TNbmMTo%2FCXcAOr0AJEG%2FO7ulTYwG99hUiZ31zpLvE2jBH4i2sXhcu7%2F7t8E1a%2FViLxxvHljLgdrzWQZtJ0TXsvIbWUFl%2Bl2U%2F%2BN%2F2nty%2BtOGHK68xjHir8MhunSX%2FtbOTQErPH3Hkk6MP3ALYwF%2F6VdAU8O9peHMWCbmWWHfd%2Bk%2FmVpK1yj1zI9X2vqJqAuK%2FHIKeGaVMDoftx3Ja7ZfJyMdl5tWKjouS54XP606Tp3w0AU8iohDMmdpRDhmxGCo7caFQT5DiGt61mdtckFlvflUAoO0XGO3RVKRi7Tb0J8ckW%2FIz%2BwDz9pnQlpq11%2Bw85f5D%2FLH%2B%2B%2BwclDUxZbkct1fPGVFxA5NBPJY5Y54%2FmnmQ5FInu3QcGprFSs4GMcuc8rf%2BADnoiF%2BN514Z%2B%2Bc9qgaqYEVOmk%2FgrnSIjrXpF7uZs4FKR2Ct4WclKjW%2FkYpjMhBhb2PxTkwCGW2GRK4BQKiMRgvl7XUQDQNixBuumNV5fA0oFElhzTM3UcneEoWNIiKT6RNtER2ogNaexU0livjpaZLztKTk1csqivUScAmLBbqPyu7BdLQ5PhM97XkK1zk6ZsaXMY81VEJkUGvPCveuCvXM7c1snTvXbemKgygra%2FEQdrsP0Ns1vWcwy%2BXkhxLS65t5WqrBRixIGvDA80lkVetKmKoKMlCnJCBgEQPYCPw8oHSwckyxbNkrgG%2BYRl1FCTu23%2B6ciRvc7mOryYNooXYA2sa5Ol7NHr3g8YfGR3SC50RsGm77ohpgICVPFJxgelXT2lq%2FKKmXYYLnza299k66VVY2K57pl3Vh6OhFeNx5%2FKScQbEexODBeAb1xrBmegepd5OTmtKToC7Fchwz1gXdX9sF0v6tJf%2Bs1MMFCHO2x1AdQ4S93H5Ztvfkg8oEDNr%2F%2B56elcKSqkSW0x7HS%2FtRiW%2FX0Q2mPYTcLQgJIGPApB76V%2F%2BlyDeLO9ksV1qh1hZxU88w5MJw6LqyGHq%2B8l6mURj8EHa3zef1biI0MTuQ%2FDcmNAvEVkp%2B5J1ZvgYYeUiJIhvLinfE1bJLflV17CPQ3peZUFk2ozDd8o18gs5J06EZlMexvmvDx%2B4%2B2NBlOIXHEASuwOYwnYArACrRySUXXQgxvp1FPR%2FKS1Li2pdPZ8lx01dVfE65wba82dp2ZvEIYPKz%2BEsiRs7J%2BgvCcQECTjSQX4g55jzUZgFcjbdgALK7KOvys431B%2FGHsHyzU56Cwg%2BkRbbt1XaWrqOyAzaJ%2B%2B1N%2B9OnE0z2jyKj8%2BBpVTOcDE%2BbCk%2B10gB6ItBJp8pcIhXwqwhz1DIIHibjE4q87HhtRCSd7hR4iM9gPv3Vuod4awOG0V7wxIhPejSoOgNDUD5sR7bpeIbfX5FTl9vTlndSN9TWEA6QuEl8ncnaArrXeH5kVap01Kr8RU54LJJBQrPPzJ6LUKTZw98SRQi%2BcQzmBzB%2FuxgcF0PorSm8CvMYI2G5FBP2byRasP83eukLuqWcn9fNdFIgAlhS9ZC0pBYnF0fxOpF9o8'

        self.parameters = data
        self.method = "POST"
        self.request["headers"]={
            "Host": "kscourts.gov",
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://kscourts.gov/Cases-Decisions/Decisions",
            "Content-Length": "15088", "Origin": "https://kscourts.gov",
            "Connection": "keep-alive",
            "Cookie": "CMSPreferredCulture=en-US; CMSCsrfCookie=xLPIFiFvvHfhrT8jcXonzHUP2lRwNx32T+m1J2ry; ASP.NET_SessionId=nvohtvr3xt1rc2kufzh4jsbt",
            "Upgrade-Insecure-Requests": "1", "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "no-cors", "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Content-Type": "application/x-www-form-urlencoded",
            "Priority": "u=0, i", "Pragma": "no-cache",
            "Cache-Control": "no-cache"
        }
        self.request["verify"] = False

    def _process_html(self):
        page=1
        flag=True
        while flag:
            self.method = "POST"
            if not self.test_mode_enabled():
                if self.url == "https://kscourts.gov/Cases-Decisions/Decisions":
                    self._update_parameters(page)
                    self.html = self._download_again()
            for row in self.html.xpath(".//tr"):
                date_filed, docket_number, case_name, court, status = row.xpath(
                    ".//td/a/text()")
                url = row.xpath(".//td/a")[0].get("href")
                date_obj=datetime.strptime(date_filed,'%m/%d/%Y')
                to_comp_date=date_obj.strftime('%d/%m/%Y')
                res=CasemineUtil.compare_date(self.last_date,to_comp_date)
                if res==1:
                    flag=False
                    break
                self.cases.append({
                    "status": status,
                    "date": date_filed,
                    "docket": [docket_number],
                    "name": case_name,
                    "url": url,
                })
            page=page+1

    def _download_again(self, request_dict={}):
        """Download the latest version of Site"""
        self.downloader_executed = True
        self._request_url_post(self.url)
        self._post_process_response()
        return self._return_response_text_object()

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.last_date=start_date.strftime('%d/%m/%Y')
        self.parse()
        return 0

    def get_court_type(self):
        return "state"

    def get_state_name(self):
        return "Kansas"

    def get_class_name(self):
        return "kan_p"

    def get_court_name(self):
        return "Supreme Court of Kansas"
