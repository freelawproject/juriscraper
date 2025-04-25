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
        # self.year_u="https://www.courts.ri.gov/Courts/SupremeCourt/Pages/published-opinions.aspx#Default=%7B%22k%22%3A%22%22%2C%22s%22%3A{}1%2C%22r%22%3A%5B%7B%22n%22%3A%22RIJYear%22%2C%22t%22%3A%5B%22%5C%22%C7%82%C7%82666c6f61743b233{}3{}3{}3{}2e3030303030303030303030%5C%22%22%5D%2C%22o%22%3A%22OR%22%2C%22k%22%3Afalse%2C%22m%22%3A%7B%22%5C%22%C7%82%C7%82666c6f61743b233{}3{}3{}3{}2e3030303030303030303030%5C%22%22%3A%22float%3B%23{}.00000000000%22%7D%7D%5D%7D"
        self.json_url ="https://www.courts.ri.gov/_vti_bin/client.svc/ProcessQuery"
        row_limit=500
        self.requestDigest = ""
        self.headers = {
            "Referer": "https://www.courts.ri.gov/Courts/superiorcourt/Pages/decisions-orders.aspx",
        }
        self.search_key='53c11700-e762-4f7a-8328-aac298e8b73aDefault'
        self.data_xml = (f'''<Request xmlns="http://schemas.microsoft.com/sharepoint/clientquery/2009" SchemaVersion="15.0.0.0" LibraryVersion="16.0.0.0" ApplicationName="Javascript Library"><Actions><ObjectPath Id="117" ObjectPathId="116" /><SetProperty Id="118" ObjectPathId="116" Name="ImpressionID"><Parameter Type="String">1287373_-1_1033</Parameter></SetProperty><SetProperty Id="119" ObjectPathId="116" Name="TimeZoneId"><Parameter Type="Number">{row_limit}</Parameter></SetProperty><SetProperty Id="120" ObjectPathId="116" Name="QueryText"><Parameter Type="String">(RIJCourt:'Supreme') AND (ContentType:'RIJExecutiveOrder' OR ContentType:'RIJPublishedOrder' OR ContentType:'RIJAdministrativeOrder' OR ContentType:'RIJMicellaneousOrder)</Parameter></SetProperty><SetProperty Id="121" ObjectPathId="116" Name="QueryTemplate"><Parameter Type="String">{{SearchBoxQuery}} (ContentType:"RIJOpinion" OR ContentType:"RIJAdministrativeOrder" OR ContentType:"RIJExecutiveOrder" OR ContentType:"RIJDecision" OR ContentType:"RIJMicellaneousOrder" OR ContentType:"RIJPublishedOrder") </Parameter></SetProperty><ObjectPath Id="123" ObjectPathId="122" /><Method Name="Add" Id="124" ObjectPathId="122"><Parameters><Parameter Type="String">RefinableDate03</Parameter><Parameter Type="Number">1</Parameter></Parameters></Method><SetProperty Id="125" ObjectPathId="116" Name="Culture"><Parameter Type="Number">1033</Parameter></SetProperty><SetProperty Id="126" ObjectPathId="116" Name="RowsPerPage"><Parameter Type="Number">{row_limit}</Parameter></SetProperty><SetProperty Id="127" ObjectPathId="116" Name="RowLimit"><Parameter Type="Number">{row_limit}</Parameter></SetProperty><SetProperty Id="128" ObjectPathId="116" Name="TotalRowsExactMinimum"><Parameter Type="Number">11</Parameter></SetProperty><SetProperty Id="129" ObjectPathId="116" Name="SourceId"><Parameter Type="Guid">{{8413cd39-2156-4e00-b54d-11efd9abdb89}}</Parameter></SetProperty><ObjectPath Id="131" ObjectPathId="130" /><Method Name="SetQueryPropertyValue" Id="132" ObjectPathId="130"><Parameters><Parameter Type="String">SourceName</Parameter><Parameter TypeId="{{b25ba502-71d7-4ae4-a701-4ca2fb1223be}}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">Local SharePoint Results</Property></Parameter></Parameters></Method><Method Name="SetQueryPropertyValue" Id="133" ObjectPathId="130"><Parameters><Parameter Type="String">SourceLevel</Parameter><Parameter TypeId="{{b25ba502-71d7-4ae4-a701-4ca2fb1223be}}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">Ssa</Property></Parameter></Parameters></Method><SetProperty Id="134" ObjectPathId="116" Name="Refiners"><Parameter Type="String">RIJCourt(deephits=100000,sort=frequency/ascending,filter=15/0/*),ContentType(deephits=100000,filter=15/0/*),RIJYear(deephits=100000,sort=name/descending,filter=15/0/*)</Parameter></SetProperty><ObjectPath Id="136" ObjectPathId="135" /><Method Name="Add" Id="137" ObjectPathId="135"><Parameters><Parameter Type="String">Path</Parameter></Parameters></Method><Method Name="Add" Id="138" ObjectPathId="135"><Parameters><Parameter Type="String">RIJLongTitleOWSMTXT</Parameter></Parameters></Method><Method Name="Add" Id="139" ObjectPathId="135"><Parameters><Parameter Type="String">RIJDateOWSDATE</Parameter></Parameters></Method><Method Name="Add" Id="140" ObjectPathId="135"><Parameters><Parameter Type="String">RIJLongNumberOWSMTXT</Parameter></Parameters></Method><Method Name="Add" Id="141" ObjectPathId="135"><Parameters><Parameter Type="String">RIJCaseSummaryOWSMTXT</Parameter></Parameters></Method><ObjectPath Id="143" ObjectPathId="142" /><Method Name="Add" Id="144" ObjectPathId="142"><Parameters><Parameter Type="String">Title</Parameter></Parameters></Method><Method Name="Add" Id="145" ObjectPathId="142"><Parameters><Parameter Type="String">Path</Parameter></Parameters></Method><Method Name="Add" Id="146" ObjectPathId="142"><Parameters><Parameter Type="String">Author</Parameter></Parameters></Method><Method Name="Add" Id="147" ObjectPathId="142"><Parameters><Parameter Type="String">SectionNames</Parameter></Parameters></Method><Method Name="Add" Id="148" ObjectPathId="142"><Parameters><Parameter Type="String">SiteDescription</Parameter></Parameters></Method><SetProperty Id="149" ObjectPathId="116" Name="RankingModelId"><Parameter Type="String">8f6fd0bc-06f9-43cf-bbab-08c377e083f4</Parameter></SetProperty><SetProperty Id="150" ObjectPathId="116" Name="TrimDuplicates"><Parameter Type="Boolean">false</Parameter></SetProperty><Method Name="SetQueryPropertyValue" Id="151" ObjectPathId="130"><Parameters><Parameter Type="String">CrossGeoQuery</Parameter><Parameter TypeId="{{b25ba502-71d7-4ae4-a701-4ca2fb1223be}}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">false</Property></Parameter></Parameters></Method><Method Name="SetQueryPropertyValue" Id="152" ObjectPathId="130"><Parameters><Parameter Type="String">ListId</Parameter><Parameter TypeId="{{b25ba502-71d7-4ae4-a701-4ca2fb1223be}}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">815c0184-55cb-4e03-a379-a853eacc0d6a</Property></Parameter></Parameters></Method><Method Name="SetQueryPropertyValue" Id="153" ObjectPathId="130"><Parameters><Parameter Type="String">ListItemId</Parameter><Parameter TypeId="{{b25ba502-71d7-4ae4-a701-4ca2fb1223be}}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">7</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">2</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="Null" /></Parameter></Parameters></Method><SetProperty Id="154" ObjectPathId="116" Name="ResultsUrl"><Parameter Type="String">https://www.courts.ri.gov/Pages/ood.aspx?k=(RIJCourt:%27Supreme%27)%20AND%20(ContentType:%27RIJExecutiveOrder%27%20OR%20ContentType:%27RIJPublishedOrder%27%20OR%20ContentType:%27RIJAdministrativeOrder%27%20OR%20ContentType:%27RIJMicellaneousOrder)#k=(RIJCourt%3A'Supreme')%20AND%20(ContentType%3A'RIJExecutiveOrder'%20OR%20ContentType%3A'RIJPublishedOrder'%20OR%20ContentType%3A'RIJAdministrativeOrder'%20OR%20ContentType%3A'RIJMicellaneousOrder)#s=11#l=1033</Parameter></SetProperty><SetProperty Id="155" ObjectPathId="116" Name="BypassResultTypes"><Parameter Type="Boolean">true</Parameter></SetProperty><SetProperty Id="156" ObjectPathId="116" Name="ClientType"><Parameter Type="String">UI</Parameter></SetProperty><Method Name="SetQueryPropertyValue" Id="157" ObjectPathId="130"><Parameters><Parameter Type="String">QuerySession</Parameter><Parameter TypeId="{{b25ba502-71d7-4ae4-a701-4ca2fb1223be}}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">0</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">1</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="String">ca307854-1baf-438a-8305-cca60983ff59</Property></Parameter></Parameters></Method><SetProperty Id="158" ObjectPathId="116" Name="ProcessPersonalFavorites"><Parameter Type="Boolean">false</Parameter></SetProperty><SetProperty Id="159" ObjectPathId="116" Name="SafeQueryPropertiesTemplateUrl"><Parameter Type="String">querygroup://webroot/Pages/ood.aspx?groupname=Default</Parameter></SetProperty><SetProperty Id="160" ObjectPathId="116" Name="IgnoreSafeQueryPropertiesTemplateUrl"><Parameter Type="Boolean">false</Parameter></SetProperty><Method Name="SetQueryPropertyValue" Id="161" ObjectPathId="130"><Parameters><Parameter Type="String">QueryDateTimeCulture</Parameter><Parameter TypeId="{{b25ba502-71d7-4ae4-a701-4ca2fb1223be}}"><Property Name="BoolVal" Type="Boolean">false</Property><Property Name="IntVal" Type="Number">1033</Property><Property Name="QueryPropertyValueTypeIndex" Type="Number">2</Property><Property Name="StrArray" Type="Null" /><Property Name="StrVal" Type="Null" /></Parameter></Parameters></Method><ObjectPath Id="163" ObjectPathId="162" /><ExceptionHandlingScope Id="164"><TryScope Id="166"><Method Name="ExecuteQueries" Id="168" ObjectPathId="162">
                        <Parameters><Parameter Type="Array"><Object Type="String">{self.search_key}</Object></Parameter><Parameter Type="Array"><Object ObjectPathId="116" /></Parameter><Parameter Type="Boolean">true</Parameter></Parameters></Method></TryScope><CatchScope Id="170" /></ExceptionHandlingScope></Actions><ObjectPaths><Constructor Id="116" TypeId="{{80173281-fffd-47b6-9a49-312e06ff8428}}" /><Property Id="122" ParentId="116" Name="SortList" /><Property Id="130" ParentId="116" Name="Properties" /><Property Id="135" ParentId="116" Name="SelectProperties" /><Property Id="142" ParentId="116" Name="HitHighlightedProperties" /><Constructor Id="162" TypeId="{{8d2ac302-db2f-46fe-9015-872b35f15098}}" /></ObjectPaths></Request>''')

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

                if "Published" in url:
                    status = "Published"
                elif "Executive" in url:
                    status="Executive"
                elif "Miscellaneous" in url:
                    status="Miscellaneous"
                elif "Administrative" in url :
                    status="Administrative"
                else:
                    status="Unknown"
                self.cases.append(
                    {
                        "url": url,
                        "summary": summary,
                        "docket": docket,
                        "name": name,
                        "date": date,
                        "status": status
                    }
                )
    def get_class_name(self):
        return "ri_ordr"
