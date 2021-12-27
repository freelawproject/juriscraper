from lxml import html

from juriscraper.AbstractSite import logger
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = (
            "http://www.ca10.uscourts.gov/opinions/new/daily_decisions.rss"
        )
        self.court_id = self.__module__

    def _get_case_names(self):
        """Case name parsing
        Expected value for title_string:
            &lt;p&gt;Bazan-Martinez v. Garland&lt;/p&gt;
        """
        case_names = []
        for title_string in self.html.xpath("//item/title/text()"):
            try:
                p_element = html.etree.fromstring(str(title_string))
                title_string = p_element.xpath("/p/text()")[0]
                case_names.append(title_string)
            except:
                logger.error(f"Error while parsing case name: {title_string}")
                raise InsanityException(
                    f"Error while parsing case name: {title_string}"
                )
        return case_names

    def _get_download_urls(self):
        return [
            html.tostring(e, method="text").decode()
            for e in self.html.xpath("//item/link")
        ]

    def _get_case_dates(self):
        """Case date parsing
        Expected value for date_string:
            &lt;span class=&quot;date-display-single&quot; property=&quot;dc:date&quot; datatype=&quot;xsd:dateTime&quot; content=&quot;2021-11-16T00:00:00-07:00&quot;&gt;Tue Nov 16 2021&lt;/span&gt;
        """
        dates = []
        for date_string in self.html.xpath("//item/pubdate/text()"):
            try:
                span_element = html.etree.fromstring(str(date_string))
                date_string = span_element.xpath("/span/text()")[0]
                dates.append(convert_date_string(date_string))
            except:
                logger.error(f"Error while parsing case date: {date_string}")
                raise InsanityException(
                    f"Error while parsing case date: {date_string}"
                )
        return dates

    def _get_docket_numbers(self):
        """Case docket parsing
        Expected content in description tag:
            Docket#: 21-6001 - Date Issued: Mon Nov 15 2021 - Unpublished Order and Judgment
        """
        return [
            e.split(" - ")[0].split(":")[1]
            for e in self.html.xpath("//item/description/text()")
        ]

    def _get_precedential_statuses(self):
        """Case precedential status parsing
        Expected content in description tag:
            Docket#: 21-5062 - Date Issued: Fri Nov 12 2021 - Unpublished Order and Judgment
        Status:
            - Published: "Published Opinion"
            - Unpublished: "Unpublished Order and Judgment"
        """
        return [
            "Published"
            if "published opinion" in e.split(" - ")[2].lower()
            else "Unpublished"
            for e in self.html.xpath("//item/description/text()")
        ]

    def _get_lower_courts(self):
        """Case lower court name parsing
        namescpace "dc": "http://purl.org/dc/elements/1.1/"
        Tags:
            - <dc:creator>Board of Immigration Appeals</dc:creator>
        """
        return [
            e
            for e in self.html.xpath(
                "//item/creator/text()",
                namespaces={"dc": "http://purl.org/dc/elements/1.1/"},
            )
        ]
