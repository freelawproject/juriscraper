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

from lxml import html

from juriscraper.opinions.united_states.state import ri


class Site(ri.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url="https://www.courts.ri.gov/Courts/SupremeCourt/Pages/published-opinions.aspx#k=#l=1033"
        self.json_url ="https://www.courts.ri.gov/Courts/superiorcourt/_vti_bin/client.svc/ProcessQuery"
        row_limit=500
        self.requestDigest = ""
        self.headers = {
            "Referer": "https://www.courts.ri.gov/Pages/ood.aspx",
        }
        self.search_key='9b7f0f1a-76d0-47c4-9014-ad475b8a40afDefault'
        self.data_xml = ('''<Request xmlns="http://schemas.microsoft.com/sharepoint/clientquery/2009" SchemaVersion="15.0.0.0" LibraryVersion="16.0.0.0" ApplicationName="Javascript Library"><Actions><ObjectPath Id="1" ObjectPathId="0" /><SetProperty Id="2" ObjectPathId="0" Name="TimeZoneId"><Parameter Type="Number">10</Parameter></SetProperty><SetProperty Id="3" ObjectPathId="0" Name="QueryTemplate"><Parameter Type="String">{SearchBoxQuery} (ContentType:"RIJOpinion" OR ContentType:"RIJAdministrativeOrder" OR ContentType:"RIJExecutiveOrder" OR ContentType:"RIJDecision" OR ContentType:"RIJMicellaneousOrder" OR ContentType:"RIJPublishedOrder") </Parameter></SetProperty><ObjectPath Id="5" ObjectPathId="4" /><Method Name="Add" Id="6" ObjectPathId="4"><Parameters><Parameter Type="String">RefinableDate03</Parameter><Parameter Type="Number">1</Parameter></Parameters></Method><ObjectPath Id="8" ObjectPathId="7" /><Method Name="Add" Id="9" ObjectPathId="7"><Parameters><Parameter Type="String">RIJCourt:"ǂǂ4469737472696374"</Parameter></Parameters></Method><SetProperty Id="10" ObjectPathId="0" Name="Culture"><Parameter Type="Number">1033</Parameter></SetProperty><SetProperty Id="11" ObjectPathId="0" Name="RowsPerPage"><Parameter Type="Number">10</Parameter></SetProperty><SetProperty Id="12" ObjectPathId="0" Name="RowLimit"><Parameter Type="Number">10</Parameter></SetProperty><SetProperty Id="13" ObjectPathId="0" Name="TotalRowsExactMinimum"><Parameter Type="Number">11</Parameter></SetProperty><SetProperty Id="14" ObjectPathId="0" Name="SourceId"><Parameter Type="Guid">{8413cd39-2156-4e00-b54d-11efd9abdb89}</Parameter></SetProperty><ObjectPath Id="16" ObjectPathId="15" /><Method Name="SetQueryPropertyValue" Id="17" ObjectPathId="15"><Parameters><Parameter Type="String">SourceName</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">Local SharePoint Results</Property></Parameter></Parameters></Method><Method Name="SetQueryPropertyValue" Id="18" ObjectPathId="15"><Parameters><Parameter Type="String">SourceLevel</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">Ssa</Property></Parameter></Parameters></Method><SetProperty Id="19" ObjectPathId="0" Name="Refiners"><Parameter Type="String">RIJCourt(deephits=100000,sort=frequency/ascending,filter=15/0/*),ContentType(deephits=100000,filter=15/0/*),RIJYear(deephits=100000,sort=name/descending,filter=15/0/*)</Parameter></SetProperty><ObjectPath Id="21" ObjectPathId="20" /><Method Name="Add" Id="22" ObjectPathId="20"><Parameters><Parameter Type="String">Path</Parameter></Parameters></Method><Method Name="Add" Id="23" ObjectPathId="20"><Parameters><Parameter Type="String">RIJLongTitleOWSMTXT</Parameter></Parameters></Method><Method Name="Add" Id="24" ObjectPathId="20"><Parameters><Parameter Type="String">RIJDateOWSDATE</Parameter></Parameters></Method><Method Name="Add" Id="25" ObjectPathId="20"><Parameters><Parameter Type="String">RIJLongNumberOWSMTXT</Parameter></Parameters></Method><Method Name="Add" Id="26" ObjectPathId="20"><Parameters><Parameter Type="String">RIJCaseSummaryOWSMTXT</Parameter></Parameters></Method><ObjectPath Id="28" ObjectPathId="27" /><Method Name="Add" Id="29" ObjectPathId="27"><Parameters><Parameter Type="String">Title</Parameter></Parameters></Method><Method Name="Add" Id="30" ObjectPathId="27"><Parameters><Parameter Type="String">Path</Parameter></Parameters></Method><Method Name="Add" Id="31" ObjectPathId="27"><Parameters><Parameter Type="String">Author</Parameter></Parameters></Method><Method Name="Add" Id="32" ObjectPathId="27"><Parameters><Parameter Type="String">SectionNames</Parameter></Parameters></Method><Method Name="Add" Id="33" ObjectPathId="27"><Parameters><Parameter Type="String">SiteDescription</Parameter></Parameters></Method><SetProperty Id="34" ObjectPathId="0" Name="RankingModelId"><Parameter Type="String">8f6fd0bc-06f9-43cf-bbab-08c377e083f4</Parameter></SetProperty><SetProperty Id="35" ObjectPathId="0" Name="TrimDuplicates"><Parameter Type="Boolean">false</Parameter></SetProperty><Method Name="SetQueryPropertyValue" Id="36" ObjectPathId="15"><Parameters><Parameter Type="String">CrossGeoQuery</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">false</Property></Parameter></Parameters></Method><Method Name="SetQueryPropertyValue" Id="37" ObjectPathId="15"><Parameters><Parameter Type="String">ListId</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">815c0184-55cb-4e03-a379-a853eacc0d6a</Property></Parameter></Parameters></Method><Method Name="SetQueryPropertyValue" Id="38" ObjectPathId="15"><Parameters><Parameter Type="String">ListItemId</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">7</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">2</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="Null" /></Parameter></Parameters></Method><SetProperty Id="39" ObjectPathId="0" Name="ResultsUrl"><Parameter Type="String">https://www.courts.ri.gov/Pages/ood.aspx#Default={%22k%22:%22%22,%22r%22:[{%22n%22:%22RIJCourt%22,%22t%22:[%22\%22%C7%82%C7%824469737472696374\%22%22],%22o%22:%22OR%22,%22k%22:false,%22m%22:{%22\%22%C7%82%C7%824469737472696374\%22%22:%22District%22}}],%22l%22:1033}</Parameter></SetProperty><SetProperty Id="40" ObjectPathId="0" Name="BypassResultTypes"><Parameter Type="Boolean">true</Parameter></SetProperty><SetProperty Id="41" ObjectPathId="0" Name="ClientType"><Parameter Type="String">UI</Parameter></SetProperty><Method Name="SetQueryPropertyValue" Id="42" ObjectPathId="15"><Parameters><Parameter Type="String">QuerySession</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">ca307854-1baf-438a-8305-cca60983ff59</Property></Parameter></Parameters></Method><SetProperty Id="43" ObjectPathId="0" Name="ProcessPersonalFavorites"><Parameter Type="Boolean">false</Parameter></SetProperty><SetProperty Id="44" ObjectPathId="0" Name="SafeQueryPropertiesTemplateUrl"><Parameter Type="String">querygroup://webroot/Pages/ood.aspx?groupname=Default</Parameter></SetProperty><SetProperty Id="45" ObjectPathId="0" Name="IgnoreSafeQueryPropertiesTemplateUrl"><Parameter Type="Boolean">false</Parameter></SetProperty><Method Name="SetQueryPropertyValue" Id="46" ObjectPathId="15"><Parameters><Parameter Type="String">QueryDateTimeCulture</Parameter><Parameter TypeId="{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">1033</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">2</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="Null" /></Parameter></Parameters></Method><ObjectPath Id="48" ObjectPathId="47" /><ExceptionHandlingScope Id="49"><TryScope Id="51"><Method Name="ExecuteQueries" Id="53" ObjectPathId="47"><Parameters><Parameter Type="Array"><Object Type="String">9b7f0f1a-76d0-47c4-9014-ad475b8a40afDefault</Object></Parameter><Parameter Type="Array"><Object ObjectPathId="0" /></Parameter><Parameter Type="Boolean">true</Parameter></Parameters></Method></TryScope><CatchScope Id="55" /></ExceptionHandlingScope></Actions><ObjectPaths><Constructor Id="0" TypeId="{80173281-fffd-47b6-9a49-312e06ff8428}" /><Property Id="4" ParentId="0" Name="SortList" /><Property Id="7" ParentId="0" Name="RefinementFilters" /><Property Id="15" ParentId="0" Name="Properties" /><Property Id="20" ParentId="0" Name="SelectProperties" /><Property Id="27" ParentId="0" Name="HitHighlightedProperties" /><Constructor Id="47" TypeId="{8d2ac302-db2f-46fe-9015-872b35f15098}" /></ObjectPaths></Request>''')

    def _process_html(self, start_date: datetime, end_date: datetime) -> None:
        html_string = html.tostring(self.html).decode('UTF-8')
        request_digest =str(html_string).split("formDigestElement.value")[3].split("'")[1]
        self.headers.update(
            {
                "X-RequestDigest":request_digest
            }
        )
        response_json = self.download_json()
        print(response_json)
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
                                 "%m/%d/%Y") >= start_date and datetime.strptime(
                date.strip(), "%m/%d/%Y") <= end_date:
                name = row['RIJLongTitleOWSMTXT']
                url = quote(row['Path'], safe='://&')
                doc = row['RIJLongNumberOWSMTXT']
                if doc is None : docket=None
                else:
                    docs = doc.replace('&nbsp;', '')
                    docs = docs.replace('and',',')
                    docs = docs.replace(' , ', ',')
                    docs = docs.replace(' ,', ',')
                    docs = docs.replace(', ', ',')
                    docket = docs.split(',')
                date =  row["RIJDateOWSDATE"].split(" ")[0]

                self.cases.append(
                    {
                        "url": url,
                        "summary": summary,
                        "docket": docket,
                        "name": name,
                        "date": date,
                        "status": "Unknown"
                    }
                )
    def get_class_name(self):
        return "ri_dist"
