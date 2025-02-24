# """Scraper for the Rhode Island Supreme Court
# CourtID: ri
# Court Short Name: R.I.
# Court Contact: helpdesk@courts.ri.gov, MFerris@courts.ri.gov (Ferris, Mirella), webmaster@courts.ri.gov
#     https://www.courts.ri.gov/PDF/TelephoneDirectory.pdf
# Author: Brian W. Carver
# Date created: 2013-08-10
# History:
#     Date created: 2013-08-10 by Brian W. Carver
#     2022-05-02: Updated by William E. Palin, to use JSON responses
# """
# from datetime import datetime
# from urllib.parse import quote
#
# from lxml import html
#
# from juriscraper.OpinionSiteLinear import OpinionSiteLinear
#
#
# class Site(OpinionSiteLinear):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.court_id = self.__module__
#         self.status = "Published"
#         self.url = "https://www.courts.ri.gov/Pages/ood.aspx#k=#l=1033"
#         # self.url ="https://www.courts.ri.gov/Courts/SupremeCourt/Pages/published-opinions.aspx#k=#l=1033"
#         self.search_key = "0e5a1158-d281-44df-aa6c-2a734804a382Default"
#         row_limit = 50
#
#         # Parameters are set in XML on this website - with adjustable values
#         self.data_xml = (
#             '<Request xmlns="http://schemas.microsoft.com/sharepoint/clientquery/2009" SchemaVersion="15.0.0.0" LibraryVersion="16.0.0.0" ApplicationName="Javascript Library"><Actions><ObjectPath Id="598" ObjectPathId="597" /><SetProperty Id="599" ObjectPathId="597" Name="ImpressionID"><Parameter Type="String">300116_-1_1033</Parameter></SetProperty><SetProperty Id="600" ObjectPathId="597" Name="TimeZoneId"><Parameter Type="Number">10</Parameter></SetProperty><SetProperty Id="601" ObjectPathId="597" Name="QueryTemplate"><Parameter Type="String">{SearchBoxQuery} (ContentType:"RIJOpinion" OR ContentType:"RIJAdministrativeOrder" OR ContentType:"RIJExecutiveOrder" OR ContentType:"RIJDecision" OR ContentType:"RIJMicellaneousOrder" OR ContentType:"RIJPublishedOrder") </Parameter></SetProperty><ObjectPath Id="603" ObjectPathId="602" /><Method Name="Add" Id="604" ObjectPathId="602"><Parameters><Parameter Type="String">RefinableDate03</Parameter><Parameter Type="Number">1</Parameter></Parameters></Method><ObjectPath Id="606" ObjectPathId="605" /><Method Name="Add" Id="607" ObjectPathId="605"><Parameters><Parameter Type="String">RIJCourt:"ǂǂ53757072656d65"</Parameter></Parameters></Method><Method Name="Add" Id="608" ObjectPathId="605"><Parameters><Parameter Type="String">OR(ContentType:"ǂǂ52494a4f70696e696f6e",ContentType:"ǂǂ52494a5075626c69736865644f72646572")</Parameter></Parameters></Method><SetProperty Id="609" ObjectPathId="597" Name="Culture"><Parameter Type="Number">1033</Parameter></SetProperty>'
#             '<SetProperty Id="610" ObjectPathId="597" Name="RowsPerPage">'
#             f'<Parameter Type="Number">{row_limit}</Parameter></SetProperty>'
#             f'<SetProperty Id="611" ObjectPathId="597" Name="RowLimit"><Parameter Type="Number">{row_limit}</Parameter></SetProperty>'
#             f'<SetProperty Id="612" ObjectPathId="597" Name="TotalRowsExactMinimum"><Parameter Type="Number">{row_limit}</Parameter></SetProperty>'
#             '<SetProperty Id="613" ObjectPathId="597" Name="SourceId"><Parameter Type="Guid">{8413cd39-2156-4e00-b54d-11efd9abdb89}</Parameter></SetProperty>'
#             '<ObjectPath Id="615" ObjectPathId="614" /><Method Name="SetQueryPropertyValue" Id="616" ObjectPathId="614"><Parameters><Parameter Type="String">SourceName</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">Local SharePoint Results</Property></Parameter></Parameters></Method><Method Name="SetQueryPropertyValue" Id="617" ObjectPathId="614"><Parameters><Parameter Type="String">SourceLevel</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">Ssa</Property></Parameter></Parameters></Method><SetProperty Id="618" ObjectPathId="597" Name="Refiners"><Parameter Type="String">RIJCourt(deephits=100000,sort=frequency/ascending,filter=15/0/*),ContentType(deephits=100000,filter=15/0/*),RIJYear(deephits=100000,sort=name/descending,filter=15/0/*)</Parameter></SetProperty><ObjectPath Id="620" ObjectPathId="619" /><Method Name="Add" Id="621" ObjectPathId="619"><Parameters><Parameter Type="String">Path</Parameter></Parameters></Method><Method Name="Add" Id="622" ObjectPathId="619"><Parameters><Parameter Type="String">RIJLongTitleOWSMTXT</Parameter></Parameters></Method><Method Name="Add" Id="623" ObjectPathId="619"><Parameters><Parameter Type="String">RIJDateOWSDATE</Parameter></Parameters></Method><Method Name="Add" Id="624" ObjectPathId="619"><Parameters><Parameter Type="String">RIJLongNumberOWSMTXT</Parameter></Parameters></Method><Method Name="Add" Id="625" ObjectPathId="619"><Parameters><Parameter Type="String">RIJCaseSummaryOWSMTXT</Parameter></Parameters></Method><ObjectPath Id="627" ObjectPathId="626" /><Method Name="Add" Id="628" ObjectPathId="626"><Parameters><Parameter Type="String">Title</Parameter></Parameters></Method><Method Name="Add" Id="629" ObjectPathId="626"><Parameters><Parameter Type="String">Path</Parameter></Parameters></Method><Method Name="Add" Id="630" ObjectPathId="626"><Parameters><Parameter Type="String">Author</Parameter></Parameters></Method><Method Name="Add" Id="631" ObjectPathId="626"><Parameters><Parameter Type="String">SectionNames</Parameter></Parameters></Method><Method Name="Add" Id="632" ObjectPathId="626"><Parameters><Parameter Type="String">SiteDescription</Parameter></Parameters></Method><SetProperty Id="633" ObjectPathId="597" Name="RankingModelId"><Parameter Type="String">8f6fd0bc-06f9-43cf-bbab-08c377e083f4</Parameter></SetProperty><SetProperty Id="634" ObjectPathId="597" Name="TrimDuplicates"><Parameter Type="Boolean">false</Parameter></SetProperty><Method Name="SetQueryPropertyValue" Id="635" ObjectPathId="614"><Parameters><Parameter Type="String">CrossGeoQuery</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">false</Property></Parameter></Parameters></Method><Method Name="SetQueryPropertyValue" Id="636" ObjectPathId="614"><Parameters><Parameter Type="String">ListId</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">815c0184-55cb-4e03-a379-a853eacc0d6a</Property></Parameter></Parameters></Method><Method Name="SetQueryPropertyValue" Id="637" ObjectPathId="614"><Parameters><Parameter Type="String">ListItemId</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">7</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">2</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="Null" /></Parameter></Parameters></Method><SetProperty Id="638" ObjectPathId="597" Name="ResultsUrl"><Parameter Type="String">https://www.courts.ri.gov/Pages/ood.aspx#Default=%7B%22k%22%3A%22%22%2C%22r%22%3A%5B%7B%22n%22%3A%22RIJCourt%22%2C%22t%22%3A%5B%22%5C%22%C7%82%C7%8253757072656d65%5C%22%22%5D%2C%22o%22%3A%22OR%22%2C%22k%22%3Afalse%2C%22m%22%3A%7B%22%5C%22%C7%82%C7%8253757072656d65%5C%22%22%3A%22Supreme%22%7D%7D%2C%7B%22n%22%3A%22ContentType%22%2C%22t%22%3A%5B%22%5C%22%C7%82%C7%8252494a4f70696e696f6e%5C%22%22%2C%22%5C%22%C7%82%C7%8252494a5075626c69736865644f72646572%5C%22%22%5D%2C%22o%22%3A%22OR%22%2C%22k%22%3Afalse%2C%22m%22%3A%7B%22%5C%22%C7%82%C7%8252494a4f70696e696f6e%5C%22%22%3A%22RIJOpinion%22%2C%22%5C%22%C7%82%C7%8252494a5075626c69736865644f72646572%5C%22%22%3A%22RIJPublishedOrder%22%7D%7D%5D%2C%22l%22%3A1033%7D</Parameter></SetProperty><SetProperty Id="639" ObjectPathId="597" Name="BypassResultTypes"><Parameter Type="Boolean">true</Parameter></SetProperty><SetProperty Id="640" ObjectPathId="597" Name="ClientType"><Parameter Type="String">UI</Parameter></SetProperty><Method Name="SetQueryPropertyValue" Id="641" ObjectPathId="614"><Parameters><Parameter Type="String">QuerySession</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">d06c85dc-f8d9-457f-be26-7ee4256b2372</Property></Parameter></Parameters></Method><SetProperty Id="642" ObjectPathId="597" Name="ProcessPersonalFavorites"><Parameter Type="Boolean">false</Parameter></SetProperty><SetProperty Id="643" ObjectPathId="597" Name="SafeQueryPropertiesTemplateUrl"><Parameter Type="String">querygroup://webroot/Pages/ood.aspx?groupname=Default</Parameter></SetProperty><SetProperty Id="644" ObjectPathId="597" Name="IgnoreSafeQueryPropertiesTemplateUrl"><Parameter Type="Boolean">false</Parameter></SetProperty><Method Name="SetQueryPropertyValue" Id="645" ObjectPathId="614"><Parameters><Parameter Type="String">QueryDateTimeCulture</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">1033</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">2</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="Null" /></Parameter></Parameters></Method><ObjectPath Id="647" ObjectPathId="646" /><ExceptionHandlingScope Id="648"><TryScope Id="650"><Method Name="ExecuteQueries" Id="652" ObjectPathId="646"><Parameters><Parameter Type="Array">'
#             f'<Object Type="String">{self.search_key}</Object>'
#             '</Parameter><Parameter Type="Array"><Object ObjectPathId="597" /></Parameter><Parameter Type="Boolean">true</Parameter></Parameters></Method></TryScope><CatchScope Id="654" /></ExceptionHandlingScope></Actions><ObjectPaths><Constructor Id="597" TypeId="{80173281-fffd-47b6-9a49-312e06ff8428}" /><Property Id="602" ParentId="597" Name="SortList" /><Property Id="605" ParentId="597" Name="RefinementFilters" /><Property Id="614" ParentId="597" Name="Properties" /><Property Id="619" ParentId="597" Name="SelectProperties" /><Property Id="626" ParentId="597" Name="HitHighlightedProperties" /><Constructor Id="646" TypeId="{8d2ac302-db2f-46fe-9015-872b35f15098}" /></ObjectPaths></Request>'
#         )
#
#         self.json_url = (
#             "https://www.courts.ri.gov/Courts/SupremeCourt/_vti_bin/client.svc/ProcessQuery"
#             # "https://www.courts.ri.gov/_vti_bin/client.svc/ProcessQuery"
#         )
#
#     def _download(self, request_dict={}):
#         if self.test_mode_enabled():
#             self.json = super()._download(request_dict)
#             return
#         return super()._download(request_dict)
#
#     def fetch_json(self) -> None:
#         """Fetch JSON data from the site.
#
#         :return: None
#         """
#         if self.test_mode_enabled():
#             return
#         self.parameters = self.data_xml
#         content = html.tostring(self.html)
#         request_digest = (
#             str(content).split("formDigestElement.value")[3].split("'")[1]
#         )
#         self.request["headers"]["X-RequestDigest"] = request_digest
#         self.request["headers"]["X-Requested-With"] = "XMLHttpRequest"
#         self._request_url_post(self.json_url)
#
#     def _process_html(self) -> None:
#         """Extract content from JSON response
#
#         :return: None
#         """
#         self.fetch_json()
#         print(self.fetch_json())
#         rows = self.request["response"].json()[-3][self.search_key][
#             "ResultTables"
#         ][0]["ResultRows"]
#         for row in rows:
#             # Summary can be None - which breaks CL so set it to empty string
#             summary = row.get("RIJCaseSummaryOWSMTXT", "")
#             summary = summary if summary else ""
#             self.cases.append(
#                 {
#                     "url": quote(row["Path"], safe="://&"),
#                     "summary": summary,
#                     "docket": row["RIJLongNumberOWSMTXT"],
#                     "name": row["RIJLongTitleOWSMTXT"],
#                     "date": row["RIJDateOWSDATE"].split(" ")[0],
#                 }
#             )
#
#     def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
#         if not self.downloader_executed:
#             self.html = self._download()
#
#             self._process_html()
#
#         for attr in self._all_attrs:
#             self.__setattr__(attr, getattr(self, f"_get_{attr}")())
#
#         self._clean_attributes()
#         if "case_name_shorts" in self._all_attrs:
#             self.case_name_shorts = self._get_case_name_shorts()
#         self._post_parse()
#         self._check_sanity()
#         self._date_sort()
#         self._make_hash()
#         return len(self.cases)

"""Scraper for the Rhode Island Supreme Court
CourtID: ri
Court Short Name: R.I.
Court Contact: helpdesk@courts.ri.gov, MFerris@courts.ri.gov (Ferris, Mirella), webmaster@courts.ri.gov
    https://www.courts.ri.gov/PDF/TelephoneDirectory.pdf
Author: Brian W. Carver
Date created: 2013-08-10
History:
    Date created: 2013-08-10 by Brian W. Carver
    2022-05-02: Updated by William E. Palin, to use JSON responses
"""
import json
from datetime import datetime
from urllib.parse import quote

import requests
from lxml import html

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url="https://www.courts.ri.gov/Courts/SupremeCourt/Pages/published-opinions.aspx#k=#l=1033"
        self.year_u="https://www.courts.ri.gov/Courts/SupremeCourt/Pages/published-opinions.aspx#Default=%7B%22k%22%3A%22%22%2C%22s%22%3A{}1%2C%22r%22%3A%5B%7B%22n%22%3A%22RIJYear%22%2C%22t%22%3A%5B%22%5C%22%C7%82%C7%82666c6f61743b233{}3{}3{}3{}2e3030303030303030303030%5C%22%22%5D%2C%22o%22%3A%22OR%22%2C%22k%22%3Afalse%2C%22m%22%3A%7B%22%5C%22%C7%82%C7%82666c6f61743b233{}3{}3{}3{}2e3030303030303030303030%5C%22%22%3A%22float%3B%23{}.00000000000%22%7D%7D%5D%7D"
        self.json_url ="https://www.courts.ri.gov/Courts/SupremeCourt/_vti_bin/client.svc/ProcessQuery"
        # self.search_key = "0e5a1158-d281-44df-aa6c-2a734804a382Default"
        self.search_key='97925624-a640-44cb-b6d7-bf2efa11c2bbDefault'
        row_limit=500
        self.requestDigest = ""
        self.headers = {
            "Referer": "https://www.courts.ri.gov/Courts/SupremeCourt/Pages/published-opinions.aspx",
            # "X-RequestDigest":"0x6393A8D5D33FFB310A0C9BC512C8E67EF945B58F7A8BDE5E996C5DDA69A1674DC229B1BD99841B2941DB473954ACE58DB1DBB83E72F0CC9C70774EBB806CE980,30 Jan 2025 07:39:48 -0000"
        }

        # self.data_xml = (
        #         '<Request xmlns="http://schemas.microsoft.com/sharepoint/clientquery/2009" SchemaVersion="15.0.0.0" LibraryVersion="16.0.0.0" ApplicationName="Javascript Library"><Actions><ObjectPath Id="1" ObjectPathId="0" /><SetProperty Id="2" ObjectPathId="0" Name="TimeZoneId">'
        #         f'<Parameter Type="Number">{row_limit}</Parameter></SetProperty><SetProperty Id="3" ObjectPathId="0" Name="QueryTemplate"><Parameter Type="String">RIJCourt:Supreme AND ContentType:RIJOpinion</Parameter></SetProperty><ObjectPath Id="5" ObjectPathId="4" /><Method Name="Add" Id="6" ObjectPathId="4"><Parameters><Parameter Type="String">RefinableDate03</Parameter><Parameter Type="Number">1</Parameter></Parameters></Method><SetProperty Id="7" ObjectPathId="0" Name="Culture"><Parameter Type="Number">1033</Parameter>'
        #         '</SetProperty><SetProperty Id="8" ObjectPathId="0" Name="RowsPerPage">'
        #         f'<Parameter Type="Number">{row_limit}</Parameter></SetProperty>'
        #         f'<SetProperty Id="9" ObjectPathId="0" Name="RowLimit"><Parameter Type="Number">{row_limit}</Parameter></SetProperty>'
        #         '<SetProperty Id="10" ObjectPathId="0" Name="TotalRowsExactMinimum"><Parameter Type="Number">11</Parameter></SetProperty><SetProperty Id="11" ObjectPathId="0" Name="SourceId"><Parameter Type="Guid">{8413cd39-2156-4e00-b54d-11efd9abdb89}</Parameter></SetProperty><ObjectPath Id="13" ObjectPathId="12" /><Method Name="SetQueryPropertyValue" Id="14" ObjectPathId="12"><Parameters><Parameter Type="String">SourceName</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">Local SharePoint Results</Property></Parameter></Parameters></Method><Method Name="SetQueryPropertyValue" Id="15" ObjectPathId="12"><Parameters><Parameter Type="String">SourceLevel</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">Ssa</Property></Parameter></Parameters></Method><SetProperty Id="16" ObjectPathId="0" Name="Refiners"><Parameter Type="String">RIJYear(deephits=100000,sort=name/descending,filter=30/0/*)</Parameter></SetProperty><ObjectPath Id="18" ObjectPathId="17" /><Method Name="Add" Id="19" ObjectPathId="17"><Parameters><Parameter Type="String">Path</Parameter></Parameters></Method><Method Name="Add" Id="20" ObjectPathId="17"><Parameters><Parameter Type="String">RIJLongTitleOWSMTXT</Parameter></Parameters></Method><Method Name="Add" Id="21" ObjectPathId="17"><Parameters><Parameter Type="String">RIJDateOWSDATE</Parameter></Parameters></Method><Method Name="Add" Id="22" ObjectPathId="17"><Parameters><Parameter Type="String">RIJLongNumberOWSMTXT</Parameter></Parameters></Method><Method Name="Add" Id="23" ObjectPathId="17"><Parameters><Parameter Type="String">RIJCaseSummaryOWSMTXT</Parameter></Parameters></Method><ObjectPath Id="25" ObjectPathId="24" /><Method Name="Add" Id="26" ObjectPathId="24"><Parameters><Parameter Type="String">Title</Parameter></Parameters></Method><Method Name="Add" Id="27" ObjectPathId="24"><Parameters><Parameter Type="String">Path</Parameter></Parameters></Method><Method Name="Add" Id="28" ObjectPathId="24"><Parameters><Parameter Type="String">Author</Parameter></Parameters></Method><Method Name="Add" Id="29" ObjectPathId="24"><Parameters><Parameter Type="String">SectionNames</Parameter></Parameters></Method><Method Name="Add" Id="30" ObjectPathId="24"><Parameters><Parameter Type="String">SiteDescription</Parameter></Parameters></Method><SetProperty Id="31" ObjectPathId="0" Name="TrimDuplicates"><Parameter Type="Boolean">false</Parameter></SetProperty><Method Name="SetQueryPropertyValue" Id="32" ObjectPathId="12"><Parameters><Parameter Type="String">CrossGeoQuery</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">false</Property></Parameter></Parameters></Method><Method Name="SetQueryPropertyValue" Id="33" ObjectPathId="12"><Parameters><Parameter Type="String">ListId</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">40c0cafe-01ad-4d6a-b051-d575016fceda</Property></Parameter></Parameters></Method><Method Name="SetQueryPropertyValue" Id="34" ObjectPathId="12"><Parameters><Parameter Type="String">ListItemId</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">25</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">2</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="Null" /></Parameter></Parameters></Method><SetProperty Id="35" ObjectPathId="0" Name="ResultsUrl"><Parameter Type="String">https://www.courts.ri.gov/Courts/SupremeCourt/Pages/published-opinions.aspx</Parameter></SetProperty><SetProperty Id="36" ObjectPathId="0" Name="BypassResultTypes"><Parameter Type="Boolean">true</Parameter></SetProperty><SetProperty Id="37" ObjectPathId="0" Name="ClientType"><Parameter Type="String"></Parameter></SetProperty><Method Name="SetQueryPropertyValue" Id="38" ObjectPathId="12"><Parameters><Parameter Type="String">QuerySession</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">af20b8b2-0377-41cd-b558-4de77021324f</Property></Parameter></Parameters></Method><SetProperty Id="39" ObjectPathId="0" Name="SafeQueryPropertiesTemplateUrl"><Parameter Type="String">querygroup://webroot/Pages/published-opinions.aspx?groupname=Default</Parameter></SetProperty><SetProperty Id="40" ObjectPathId="0" Name="IgnoreSafeQueryPropertiesTemplateUrl"><Parameter Type="Boolean">false</Parameter></SetProperty><Method Name="SetQueryPropertyValue" Id="41" ObjectPathId="12"><Parameters><Parameter Type="String">QueryDateTimeCulture</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">1033</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">2</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="Null" /></Parameter></Parameters></Method><ObjectPath Id="43" ObjectPathId="42" /><ExceptionHandlingScope Id="44"><TryScope Id="46"><Method Name="ExecuteQueries" Id="48" ObjectPathId="42"><Parameters>'
        #         f'<Parameter Type="Array"><Object Type="String">{self.search_key}</Object></Parameter><Parameter Type="Array"><Object ObjectPathId="0" />'
        #         '</Parameter><Parameter Type="Boolean">true</Parameter></Parameters></Method></TryScope><CatchScope Id="50" /></ExceptionHandlingScope></Actions><ObjectPaths><Constructor Id="0" TypeId="{80173281-fffd-47b6-9a49-312e06ff8428}" /><Property Id="4" ParentId="0" Name="SortList" /><Property Id="12" ParentId="0" Name="Properties" /><Property Id="17" ParentId="0" Name="SelectProperties" /><Property Id="24" ParentId="0" Name="HitHighlightedProperties" /><Constructor Id="42" TypeId="{8d2ac302-db2f-46fe-9015-872b35f15098}" /></ObjectPaths></Request>')

        self.data_xml = (
            '<Request xmlns="http://schemas.microsoft.com/sharepoint/clientquery/2009" SchemaVersion="15.0.0.0" LibraryVersion="16.0.0.0" ApplicationName="Javascript Library"><Actions><ObjectPath Id="1" ObjectPathId="0" /><SetProperty Id="2" ObjectPathId="0" Name="TimeZoneId">'
            f'<Parameter Type="Number">{row_limit}</Parameter></SetProperty><SetProperty Id="3" ObjectPathId="0" Name="QueryTemplate"><Parameter Type="String">RIJCourt:Supreme AND ContentType:RIJOpinion</Parameter></SetProperty><ObjectPath Id="5" ObjectPathId="4" /><Method Name="Add" Id="6" ObjectPathId="4"><Parameters><Parameter Type="String">RefinableDate03</Parameter><Parameter Type="Number">1</Parameter></Parameters></Method><SetProperty Id="7" ObjectPathId="0" Name="Culture"><Parameter Type="Number">1033</Parameter>'
            '</SetProperty><SetProperty Id="8" ObjectPathId="0" Name="RowsPerPage">'
            f'<Parameter Type="Number">{row_limit}</Parameter></SetProperty>'
            f'<SetProperty Id="9" ObjectPathId="0" Name="RowLimit"><Parameter Type="Number">{row_limit}</Parameter></SetProperty>'
            '<SetProperty Id="10" ObjectPathId="0" Name="TotalRowsExactMinimum"><Parameter Type="Number">11</Parameter></SetProperty><SetProperty Id="11" ObjectPathId="0" Name="SourceId"><Parameter Type="Guid">{8413cd39-2156-4e00-b54d-11efd9abdb89}</Parameter></SetProperty><ObjectPath Id="13" ObjectPathId="12" /><Method Name="SetQueryPropertyValue" Id="14" ObjectPathId="12"><Parameters><Parameter Type="String">SourceName</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">Local SharePoint Results</Property></Parameter></Parameters></Method><Method Name="SetQueryPropertyValue" Id="15" ObjectPathId="12"><Parameters><Parameter Type="String">SourceLevel</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">Ssa</Property></Parameter></Parameters></Method><SetProperty Id="16" ObjectPathId="0" Name="Refiners"><Parameter Type="String">RIJYear(deephits=100000,sort=name/descending,filter=30/0/*)</Parameter></SetProperty><ObjectPath Id="18" ObjectPathId="17" /><Method Name="Add" Id="19" ObjectPathId="17"><Parameters><Parameter Type="String">Path</Parameter></Parameters></Method><Method Name="Add" Id="20" ObjectPathId="17"><Parameters><Parameter Type="String">RIJLongTitleOWSMTXT</Parameter></Parameters></Method><Method Name="Add" Id="21" ObjectPathId="17"><Parameters><Parameter Type="String">RIJDateOWSDATE</Parameter></Parameters></Method><Method Name="Add" Id="22" ObjectPathId="17"><Parameters><Parameter Type="String">RIJLongNumberOWSMTXT</Parameter></Parameters></Method><Method Name="Add" Id="23" ObjectPathId="17"><Parameters><Parameter Type="String">RIJCaseSummaryOWSMTXT</Parameter></Parameters></Method><ObjectPath Id="25" ObjectPathId="24" /><Method Name="Add" Id="26" ObjectPathId="24"><Parameters><Parameter Type="String">Title</Parameter></Parameters></Method><Method Name="Add" Id="27" ObjectPathId="24"><Parameters><Parameter Type="String">Path</Parameter></Parameters></Method><Method Name="Add" Id="28" ObjectPathId="24"><Parameters><Parameter Type="String">Author</Parameter></Parameters></Method><Method Name="Add" Id="29" ObjectPathId="24"><Parameters><Parameter Type="String">SectionNames</Parameter></Parameters></Method><Method Name="Add" Id="30" ObjectPathId="24"><Parameters><Parameter Type="String">SiteDescription</Parameter></Parameters></Method><SetProperty Id="31" ObjectPathId="0" Name="TrimDuplicates"><Parameter Type="Boolean">false</Parameter></SetProperty><Method Name="SetQueryPropertyValue" Id="32" ObjectPathId="12"><Parameters><Parameter Type="String">CrossGeoQuery</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">false</Property></Parameter></Parameters></Method><Method Name="SetQueryPropertyValue" Id="33" ObjectPathId="12"><Parameters><Parameter Type="String">ListId</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">40c0cafe-01ad-4d6a-b051-d575016fceda</Property></Parameter></Parameters></Method><Method Name="SetQueryPropertyValue" Id="34" ObjectPathId="12"><Parameters><Parameter Type="String">ListItemId</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">25</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">2</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="Null" /></Parameter></Parameters></Method><SetProperty Id="35" ObjectPathId="0" Name="ResultsUrl"><Parameter Type="String">https://www.courts.ri.gov/Courts/SupremeCourt/Pages/published-opinions.aspx</Parameter></SetProperty><SetProperty Id="36" ObjectPathId="0" Name="BypassResultTypes"><Parameter Type="Boolean">true</Parameter></SetProperty><SetProperty Id="37" ObjectPathId="0" Name="ClientType"><Parameter Type="String"></Parameter></SetProperty><Method Name="SetQueryPropertyValue" Id="38" ObjectPathId="12"><Parameters><Parameter Type="String">QuerySession</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">af20b8b2-0377-41cd-b558-4de77021324f</Property></Parameter></Parameters></Method><SetProperty Id="39" ObjectPathId="0" Name="SafeQueryPropertiesTemplateUrl"><Parameter Type="String">querygroup://webroot/Pages/published-opinions.aspx?groupname=Default</Parameter></SetProperty><SetProperty Id="40" ObjectPathId="0" Name="IgnoreSafeQueryPropertiesTemplateUrl"><Parameter Type="Boolean">false</Parameter></SetProperty><Method Name="SetQueryPropertyValue" Id="41" ObjectPathId="12"><Parameters><Parameter Type="String">QueryDateTimeCulture</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">1033</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">2</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="Null" /></Parameter></Parameters></Method><ObjectPath Id="43" ObjectPathId="42" /><ExceptionHandlingScope Id="44"><TryScope Id="46"><Method Name="ExecuteQueries" Id="48" ObjectPathId="42"><Parameters>'
            f'<Parameter Type="Array"><Object Type="String">{self.search_key}</Object></Parameter><Parameter Type="Array"><Object ObjectPathId="0" />'
            '</Parameter><Parameter Type="Boolean">true</Parameter></Parameters></Method></TryScope><CatchScope Id="50" /></ExceptionHandlingScope></Actions><ObjectPaths><Constructor Id="0" TypeId="{80173281-fffd-47b6-9a49-312e06ff8428}" /><Property Id="4" ParentId="0" Name="SortList" /><Property Id="12" ParentId="0" Name="Properties" /><Property Id="17" ParentId="0" Name="SelectProperties" /><Property Id="24" ParentId="0" Name="HitHighlightedProperties" /><Constructor Id="42" TypeId="{8d2ac302-db2f-46fe-9015-872b35f15098}" /></ObjectPaths></Request>')

    def download_json(self):
        if self.test_mode_enabled():
            return json.load(open(self.json_url))

        response_json = self.request["session"].post(self.json_url,headers=self.headers,data=self.data_xml).json()
        return response_json


    def _process_html(self, start_date: datetime, end_date: datetime) -> None:
        html_string = html.tostring(self.html).decode('UTF-8')
        request_digest =str(html_string).split("formDigestElement.value")[3].split("'")[1]
        self.headers.update(
            {
                "X-RequestDigest":request_digest
            }
        )
        response_json = self.download_json()
        rows = response_json[-3][self.search_key][
            "ResultTables"
        ][0]["ResultRows"]
        for row in rows:
            # Summary can be None - which breaks CL so set it to empty string
            summary = row.get("RIJCaseSummaryOWSMTXT", "")
            summary = summary if summary else ""
            summary=summary.replace('\n','')
            date= row["RIJDateOWSDATE"].split(" ")[0]
            if datetime.strptime(date.strip(),
                                 "%m/%d/%Y") > start_date and datetime.strptime(
                date.strip(), "%m/%d/%Y") < end_date:
                name = row['RIJLongTitleOWSMTXT']
                url = quote(row['Path'], safe='://&')
                doc = row['RIJLongNumberOWSMTXT']
                docs = doc.replace('&nbsp;', '')
                docs = docs.replace('and',',')
                docs = docs.replace(' , ', ',')
                docs = docs.replace(' ,', ',')
                docs = docs.replace(', ', ',')
                docket = docs.split(',')
                date =  row["RIJDateOWSDATE"].split(" ")[0]
                # print(f"name : {name}")
                # # print(url)
                # print(f"url : {url}")
                # print(f"summary : {summary}")
                # print(f"docket : {docket}")
                # print(f'date : {date}')
                # print("-------------------------------------------------------------")
                self.cases.append(
                    {
                        "url": url,
                        "summary": summary,
                        "docket": docket,
                        "name": name,
                        "date": date,
                    }
                )


    # def download_year(self,start_year : int , end_year : int):
    #     for page in range(1):
    #         # self.url=self.u.format(page)
    #         y = start_year
    #         d=y%10
    #         c=(y//10)%10
    #         b=(y//100)%10
    #         a=(y//1000)%10
    #         self.url = self.year_u.format(page,a,b,c,d,a,b,c,d,y)
    #         print(self.url)
    #
    #         self.html=self._download()
    #         # print(html.tostring(self.html,pretty_print=True).decode('UTF-8'))
    #         self._process_html()

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:

        if not self.downloader_executed:
            self.html = self._download()

            self._process_html(start_date,end_date)

        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return len(self.cases)

    def get_court_name(self):
        return "Supreme Court of Rhode Island"

    def get_state_name(self):
        return "Rhode Island"

    def get_class_name(self):
        return "ri"

    def get_court_type(self):
        return "state"
