from app_utils import log_into_pacer, EgressPacerSession

cookie = log_into_pacer(
    username="mlissner.flp",
    password="mHUwBkSVkWUhm67J5ZwBXn8pu8a44qZ9UpBS92m!",
)
s = EgressPacerSession(cookies=cookie)

"""
pacer_court_id = "ca3"
docket_number = "24-3311"

pacer_case_id = "300601"
pacer_doc_id = "03319001890"

magic_number = None
"""

""" report = PossibleCaseNumberApi(pacer_court_id, s)
report.query(docket_number)
print(report.data()) """


""" report = AppellateAttachmentPage(pacer_court_id, s)
report.query("003010683163")
print(report.response.text)

"""



"""
report = AppellateDocketReport(pacer_court_id, s)
response = report.download_pdf(pacer_case_id=123944, pacer_doc_id="003014857371")
with open('./test.pdf', 'wb') as f:
    f.write(response.content)

"""

report = FreeOpinionReport(pacer_court_id, s)
response , msg = report.download_pdf(pacer_case_id=124072, pacer_doc_id="003014872899", appellate=True)
print(msg)
print(response.content)


"""
report.query(
    docket_number=docket_number,
    show_docket_entries=True,
    show_panel_info=True,
    show_party_atty_info=True,
    show_caption=True,
)
print(report.metadata)
print(report.response.text)
print("*"*200)
print(report.response.content)
print("*"*200)
print(report.docket_entries)
print(report.parties)
"""


""" r, _ = report._query_pdf_download(
    None, pacer_doc_id, None, got_receipt="0"
)
 """
