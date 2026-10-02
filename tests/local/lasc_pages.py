"""The markup the Los Angeles Superior Court's sites print.

What the court serves is the subject of every test in this package, so the
shapes it serves are built here rather than spelled out again in each test
module: a change to the site's markup is then one edit, and the tests can't
drift into disagreeing about what the court sends.

The pages captured under ``tests/examples/state/california/lasc`` are the
real thing, and the parsers are checked against them. These builders are for
the cases a captured page can't show: a row the court left half empty, a
courtroom with nothing scheduled, a session partway through.
"""

from juriscraper.state.california.lasc.calendar import CalendarLocation

# -- The calendar site ---------------------------------------------------

LOCATION = CalendarLocation(
    value="LAM;LA;Stanley Mosk Courthouse;111 North Hill Street",
    location_code="LAM",
    courthouse="Stanley Mosk Courthouse",
)

# The page a session starts at: the disclaimer, and nothing else to post.
DISCLAIMER_PAGE = """
<html><body><form>
  <input type="hidden" name="__VIEWSTATE" value="first">
  <input type="submit" name="ctl00$body$butDisclaimer"
         id="body_butDisclaimer" value="I Agree">
</form></body></html>
"""


def calendar_row(
    case_number: str = "23STCV04845",
    case_name: str = "MOSLEY VS LA MONARCA BAKERY",
    hearing_date: str = "09/21/2026",
    hearing_time: str = "8:30 AM",
    event: str = "Jury Trial",
    date_filed: str = "03/06/2023",
) -> str:
    """One row of a courtroom's calendar, as the court prints one."""
    return (
        f'<tr><td valign="top">{hearing_date}</td>'
        f'<td valign="top">{hearing_time}</td>'
        f'<td valign="top">{event}</td>'
        f'<td valign="top"><a href="CalendarCase.aspx?caseNumber='
        f'{case_number}" >{case_number}</a></td>'
        f'<td valign="top">{case_name}</td>'
        f'<td valign="top">{date_filed}</td></tr>'
    )


def calendar_page(
    *rows: str,
    departments: tuple[str, ...] = ("310",),
    locations: tuple[CalendarLocation, ...] = (LOCATION,),
    disclaimer: bool = False,
) -> str:
    """The calendar's search form, and whatever the last post returned.

    Every page the site serves after the disclaimer carries the whole form,
    which is what lets a courthouse's departments be swept from each result.
    A courtroom with nothing scheduled gets a sentence instead of a table.

    :param rows: The rows of the result table, from `calendar_row`.
    :param departments: The departments the chosen courthouse offers.
    :param locations: The courthouses the site publishes calendars for.
    :param disclaimer: Whether to carry the disclaimer button as well.
    :return: The page.
    """
    listed = "".join(
        f'<option value="{location.value}">{location.courthouse}</option>'
        for location in locations
    )
    options = "".join(f'<option value="{d}">{d}</option>' for d in departments)
    accept = (
        '<input type="submit" name="ctl00$body$butDisclaimer" '
        'id="body_butDisclaimer" value="I Agree">'
        if disclaimer
        else ""
    )
    results = (
        '<table id="body_calendarDeptDate_tblResults">'
        "<tr><th>Date</th><th>Time</th><th>Event</th><th>Case</th>"
        "<th>Title</th><th>File Date</th></tr>"
        f"{''.join(rows)}</table>"
        if rows
        else "There is no calendar for that department."
    )
    return f"""
    <html><body><form id="lascwebform">
      <input type="hidden" name="__VIEWSTATE" value="state">
      <input type="hidden" name="Loc" value="LAM">
      <input type="hidden" name="hdnType" value="">
      <select name="ctl00$body$ddlLocation2" id="body_ddlLocation2">
        <option value="">Select</option>{listed}
      </select>
      <select name="ctl00$body$ddlDept" id="body_ddlDept">{options}</select>
      <input name="ctl00$body$dateFrom" id="body_dateFrom" value="">
      <input name="ctl00$body$dateTo" id="body_dateTo" value="">
      {accept}
      {results}
    </form></body></html>
    """


# -- The tentative rulings site ------------------------------------------

CASE_NAME_STYLE = 'style="text-decoration: underline; font-weight: bold;"'


def ruling_header(
    case_number: str = "24NNCV01819",
    hearing_date: str = "September 14, 2026",
    department: str = "X",
) -> str:
    """The header a courtroom opens each of its rulings with."""
    return (
        f"<B> Case Number: </B> {case_number}&nbsp;&nbsp;&nbsp;"
        f"<B> Hearing Date: </B>  {hearing_date}&nbsp;&nbsp;&nbsp;"
        f"<B> Dept: </B> {department}<P> "
    )


def ruling(
    case_number: str = "24NNCV01819",
    text: str = "Motion to compel is granted.",
) -> str:
    """One ruling, header and all, as a courtroom publishes it."""
    return ruling_header(case_number=case_number) + text


def rulings_page(*rulings: str) -> str:
    """A courtroom's rulings page, which drops the courtroom list.

    :param rulings: The rulings, each opening with a `ruling_header`.
    :return: The page.
    """
    blocks = "".join(
        f'<HR SIZE = 4 NOSHADE > <P>{one}<SPAN name="wp">' for one in rulings
    )
    return (
        '<html><body><input type="hidden" name="__VIEWSTATE" value="state">'
        '<div>Notice to litigants.<span name="wp"></span><BR>'
        f"{blocks}<HR></div><p>Footer</p></body></html>"
    )


def rulings_search_page(*options: str) -> str:
    """The rulings search page, which lists every publishing courtroom.

    :param options: The option values, e.g. ``ALH,X,09/14/2026``.
    :return: The page.
    """
    listed = "".join(
        f'<option value="{value}">(Courthouse: Dept. {value})</option>'
        for value in options
    )
    return f"""
    <html><body><form>
      <input type="hidden" name="__VIEWSTATE" value="state">
      <select name="ctl00$body$List2DeptDate" id="body_List2DeptDate">
        {listed}
      </select>
    </form></body></html>
    """
