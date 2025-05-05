import os
from datetime import datetime

import requests
from lxml import html

from casemine.constants import MAIN_PDF_PATH
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def download_pdf(self, data, objectId):
        year = int(data.__getitem__('year'))

        court_name = data.get('court_name')
        court_type = data.get('court_type')
        if str(court_type).__eq__('Federal'):
            state_name=data.get('circuit')
        else:
            state_name = data.get('state')
        opinion_type = data.get('opinion_type')
        pdf_name = data.get('pdf_url').split('/')[-1]
        print(pdf_name)

        if str(opinion_type).__eq__("Oral Argument"):
            path = MAIN_PDF_PATH + court_type + "/" + state_name + "/" + court_name + "/" + "oral arguments/" + str(year)
        else:
            path = MAIN_PDF_PATH + court_type + "/" + state_name + "/" + court_name + "/" + str(year)


        obj_id = str(objectId)
        download_pdf_path = os.path.join(path, f"{obj_id}.pdf")

        os.makedirs(path, exist_ok=True)
        payload = f"__VIEWSTATE=%2FwEPDwUKLTI3MzIyMDA2Ng9kFgICAQ9kFgQCAQ9kFgICBw8QDxYGHg1EYXRhVGV4dEZpZWxkBQhqdV9sbmFtZR4ORGF0YVZhbHVlRmllbGQFBWp1X2lkHgtfIURhdGFCb3VuZGdkEBUJCENhbGxhd2F5CUplbm5lbWFubgdLaWxsaWFuB01haG9uZXkHT2xkc2h1ZQVTYXVscwdTaHVsbWFuBlNwZWNpZQhTdGFmZm9yZBUJAjI1AjI0AjE4AjIxAjI2AjIyAjIwAjIzAjI3FCsDCWdnZ2dnZ2dnZ2RkAgUPZBYEAgEPDxYCHgdWaXNpYmxlaGRkAgMPPCsACwEADxYIHghEYXRhS2V5cxYAHgtfIUl0ZW1Db3VudAIGHglQYWdlQ291bnQCAR4VXyFEYXRhU291cmNlSXRlbUNvdW50AgZkFgJmD2QWDAIBD2QWEmYPDxYCHgRUZXh0BQZTcGVjaWVkZAIBDw8WAh8IBRsyMy0wMzAwNyB8IEdvb2RtYW4gdi4gQWRhaXJkZAICDw8WAh8IBQkzLzE4LzIwMjRkZAIDDw8WAh8IBeYGVGhlIENvdXJ0IGdyYW50ZWQgRGVmZW5kYW50JiMzOTtzIE1vdGlvbiB0byBEaXNtaXNzIEZpcnN0IEFtZW5kZWQgQ29tcGxhaW50IGZvciBGYWlsdXJlIHRvIFN0YXRlIGEgQ2xhaW0gdXBvbiBXaGljaCBSZWxpZWYgQ2FuIEJlIEdyYW50ZWQuIFRoZSBDb3VydCBoZWxkIHRoYXQgMSkgZGVuaWFsIG9mIFBsYWludGlmZiYjMzk7cyBtb3Rpb24gZm9yIGFuIGV4dGVuc2lvbiBvZiB0aW1lIHRvIG9iamVjdCB0byBEZWZlbmRhbnQmIzM5O3MgZGlzY2hhcmdlIHVuZGVyIDExIFUuUy5DLiAmYW1wO3NlY3Q7IDcyNyB3YXMgcHJvcGVybHkgZGVuaWVkIGJlY2F1c2UgUGxhaW50aWZmIGNpdGVkIGV4Y3VzYWJsZSBuZWdsZWN0IGR1ZSB0byBhIGxpZ2h0bmluZyBzdHJpa2UsIHdoaWNoIHdhcyBpbmFkZXF1YXRlIGZvciBhbiBleHRlbnNpb247IDIpIHRoZSBmaXJzdCBhbWVuZGVkIGNvbXBsYWludCBmYWlsZWQgdG8gc3RhdGUgYSBjYXVzZSBvZiBhY3Rpb24gdW5kZXIgMTEgVS5TLkMuICZhbXA7c2VjdDsgNTIzKGEpKDIpKEEpIGJlY2F1c2UgUGxhaW50aWZmIGFsbGVnZWQgbm8gZmFjdHMgdGhhdCBjb3VsZCBzdXBwb3J0IGEgY29uY2x1c2lvbiB0aGF0JmFtcDtuYnNwOyB0aGUgZGVidCB3YXMgb2J0YWluZWQgYnkgZmFsc2UgcHJldGVuc2VzLCBhIGZhbHNlIHJlcHJlc2VudGF0aW9uIG9yIGFjdHVhbCBmcmF1ZDsgYW5kIDMpIFBsYWludGlmZiYjMzk7cyBmaXJzdCBhbWVuZGVkIGNvbXBsYWludCB3YXMgbm90IHN1ZmZpY2llbnQgdG8gcHV0IGRlZmVuZGFudCBvbiBub3RpY2Ugb2YgYW55IFNlY3Rpb24gNzI3IGNsYWltIGJlY2F1c2UgaXQgbWVudGlvbmVkIG5laXRoZXIgZGVuaWFsIG9mIGRpc2NoYXJnZSBub3IgU2VjdGlvbiA3MjcuZGQCBA8PFgIfCAUQNzI3LCA1MjMoYSkoMiksIGRkAgUPDxYCHwgFDDQwMDQsIDcwMDgsIGRkAgcPZBYCAgEPDxYCHgtOYXZpZ2F0ZVVybAVaaHR0cHM6Ly9wbHVzLmxleGlzLmNvbS9hcGkvcGVybWFsaW5rL2QzOGRmM2Q0LWE2NWQtNDkyNy1iNmExLWQ2ZTljYzJjNGU3NC8%2FY29udGV4dD0xNTMwNjcxZGQCCA9kFgICAQ8PFgIfCQWXAWh0dHBzOi8vd3d3Lndlc3RsYXcuY29tL0RvY3VtZW50L0liYjQ2YjZiMGU2MDYxMWVlYmQyZmM1ZmQxYzdlMzgwZi9WaWV3L0Z1bGxUZXh0Lmh0bWw%2FdHJhbnNpdGlvblR5cGU9RGVmYXVsdCZjb250ZXh0RGF0YT0oc2MuRGVmYXVsdCkmVlI9My4wJlJTPWNibHQxLjBkZAIJDw8WAh8IBQMzNjhkZAICD2QWEmYPDxYCHwgFBlNwZWNpZWRkAgEPDxYCHwgFJzIzLTMwNTcyIHwgQmx1ZXdhdGVyIFdlbGxuZXNzIEdyb3VwIExMQ2RkAgIPDxYCHwgFCDQvOC8yMDI0ZGQCAw8PFgIfCAXgBFRoZSBDb3VydCBkZW5pZWQgY3JlZGl0b3ImIzM5O3MgTW90aW9uIHRvIEFsbG93IEZpbGluZyBvZiBQcm9vZiBvZiBDbGFpbSBBZnRlciBCYXIgRGF0ZS4gSW4gdGhpcyBDaGFwdGVyIDcgY2FzZSwgdGhlIENvdXJ0IGhlbGQgdGhhdCB0aGUgY3JlZGl0b3Igd2FzIG5vdCBlbnRpdGxlZCB0byBmaWxlIGEgcHJvb2Ygb2YgY2xhaW0gYWZ0ZXIgdGhlIGJhciBkYXRlIGJlY2F1c2UgdGhlIGRlYnRvciBwcm9wZXJseSBsaXN0ZWQgdGhlIGNyZWRpdG9yJiMzOTtzIGNvcnJlY3QgaG9tZSBhZGRyZXNzIG9uIHRoZSBzY2hlZHVsZXMgYW5kIG1haWxpbmcgbWF0cml4LCB0aGUgbm90aWNlIHdhcyBtYWlsZWQgdG8gdGhhdCBhZGRyZXNzLCBhbmQgbm90aGluZyBpbiB0aGUgY3JlZGl0b3ImIzM5O3MgZGVuaWFsIG9mIHJlY2VpcHQgb2YgdGhlIG5vdGljZSB3YXMgc3VmZmljaWVudCB0byBvdmVyY29tZSB0aGUgcHJlc3VtcHRpb24gdGhhdCBzaGUgYWN0dWFsbHkgcmVjZWl2ZWQgdGhlIG5vdGljZTsgbm90aGluZyBmaWxlZCBieSB0aGUgZGVidG9yIGluIHRoZSBjYXNlIHF1YWxpZmllZCBhcyBhbiBpbmZvcm1hbCBwcm9vZiBvZiBjbGFpbSB0aGF0IGNvdWxkIGJlIGFtZW5kZWQuZGQCBA8PFgIfCAUGJm5ic3A7ZGQCBQ8PFgIfCAUYMzAwMiwgOTAwNihiKSwgMzAwMihjKSwgZGQCBw9kFgICAQ8PFgIfCQVaaHR0cHM6Ly9wbHVzLmxleGlzLmNvbS9hcGkvcGVybWFsaW5rLzI2MDFhYzQ3LTQ0ODItNDFiZS1hNzU5LWQ2NGExZWFiOTkyMi8%2FY29udGV4dD0xNTMwNjcxZGQCCA9kFgICAQ8PFgIfCQWXAWh0dHBzOi8vd3d3Lndlc3RsYXcuY29tL0RvY3VtZW50L0kzNjM4MTBhMDAzNDcxMWVmOWFjYTk0MWY5YWQ4NzE0Zi9WaWV3L0Z1bGxUZXh0Lmh0bWw%2FdHJhbnNpdGlvblR5cGU9RGVmYXVsdCZjb250ZXh0RGF0YT0oc2MuRGVmYXVsdCkmVlI9My4wJlJTPWNibHQxLjBkZAIJDw8WAh8IBQMzNjlkZAIDD2QWEmYPDxYCHwgFBlNwZWNpZWRkAgEPDxYCHwgFGjIzLTQwMzMwIHwgS2VhbmUgTS4gUm9nZXJzZGQCAg8PFgIfCAUINy8xLzIwMjRkZAIDDw8WAh8IBe0EVGhlIENvdXJ0IGRlbmllZCBDaGFwdGVyIDcgVHJ1c3RlZSYjMzk7cyBTZWNvbmQgQW1lbmRlZCBNb3Rpb24gdG8gQXBwcm92ZSB0aGUgU2FsZSBSZWFsIGFuZCBQZXJzb25hbCBQcm9wZXJ0eSBGcmVlIGFuZCBDbGVhciBvZiBMaWVucywgQ2xhaW1zLCBFbmN1bWJyYW5jZXMsIGFuZCBJbnRlcmVzdHMgUHVyc3VhbnQgdG8gMTEgVS5TLkMuIFNlY3Rpb24gMzYzKGIpLCAoZikoMyksIGFuZCAobSkuIFRoZSBhc3NldHMgdGhlIFRydXN0ZWUgc291Z2h0IHRvIHNlbGwgd2VyZSBub3QgU2VjdGlvbiA1NDEoYSkgcHJvcGVydHkgb2YgdGhlIGVzdGF0ZTsgdGhlIGFzc2V0cyB3ZXJlIG93bmVkIGJ5IHNlcGFyYXRlIGxlZ2FsIGVudGl0aWVzLCBvZiB3aGljaCBEZWJ0b3Igd2FzIGEgc2hhcmVob2xkZXIvbWVtYmVyLiBUaGUgY3JlZGl0b3JzIG9mIHRoZSBzZXBhcmF0ZSBlbnRpdGllcyB3ZXJlIG5vdCBnaXZlbiBhZGVxdWF0ZSBub3RpY2Ugb2YgdGhlIHByb3Bvc2VkIHNhbGUuIEFkZGl0aW9uYWxseSwgdGhlIHNhbGUgd291bGQgbm90IGhhdmUgcHJvZHVjZWQgYSBtZWFuaW5nZnVsIGRpc3RyaWJ1dGlvbiB0byB0aGUgdW5zZWN1cmVkIGNyZWRpdG9ycyBvZiB0aGUgYmFua3J1cHRjeSBlc3RhdGUuZGQCBA8PFgIfCAUlMzYzKGIpLCAzNjMoZiksIDM2MyhtKSwgNTQxLCAzMjYoYSksIGRkAgUPDxYCHwgFEjYwMDQoYSksIDcwMDEoMiksIGRkAgcPZBYCAgEPDxYCHwkFWmh0dHBzOi8vcGx1cy5sZXhpcy5jb20vYXBpL3Blcm1hbGluay9kOGU5OWQ3YS03MDE1LTRjMzUtYTNmZi0wYzk1ZmY3ZjBmMzMvP2NvbnRleHQ9MTUzMDY3MWRkAggPZBYCAgEPDxYCHwkFlwFodHRwczovL3d3dy53ZXN0bGF3LmNvbS9Eb2N1bWVudC9JNWRhZmY1NDA0NGE1MTFlZmE5Nzc4MmE2ZDY2NTdiYWEvVmlldy9GdWxsVGV4dC5odG1sP3RyYW5zaXRpb25UeXBlPURlZmF1bHQmY29udGV4dERhdGE9KHNjLkRlZmF1bHQpJlZSPTMuMCZSUz1jYmx0MS4wZGQCCQ8PFgIfCAUDMzcwZGQCBA9kFhJmDw8WAh8IBQZTcGVjaWVkZAIBDw8WAh8IBSAyMS01MDEyNCB8IFNTJlMgU3BlY2lhbHRpZXMsIExMQ2RkAgIPDxYCHwgFCTgvMTUvMjAyNGRkAgMPDxYCHwgFtwRUaGUgQ291cnQgZGVuaWVkIENsYWltYW50JiMzOTtzIE1vdGlvbiBmb3IgUmVsaWVmIGZyb20gRGlzY2hhcmdlIEluanVuY3Rpb24gIGFuZC9vciBPcmRlciBEaXNjaGFyZ2luZyBEZWJ0cy4gVGhlIENsYWltYW50IGFsbGVnZWQgdG8gYmUgYW4gZW1wbG95ZWUgIG9mIERlYnRvciB3aG8gc3VmZmVyZWQgYSBwb3N0LXBldGl0aW9uIG9uLXRoZS1qb2IgaW5qdXJ5IGFuZCB3YXMgIHRoZXJlZm9yZSBlbnRpdGxlZCB0byBhbiBhZG1pbmlzdHJhdGl2ZSBleHBlbnNlIGNsYWltIHVuZGVyIFNlY3Rpb24gNTAzLiAgVGhlIENsYWltYW50JiMzOTtzIGFsbGVnZWQgaW5qdXJ5IG9jY3VycmVkIGJldHdlZW4gdGhlIFBldGl0aW9uIGRhdGUgYW5kICBDb25maXJtYXRpb24uIENsYWltYW50IHdhcyBub3RpY2VkIG9mIHRoZSBiYW5rcnVwdGN5IGNhc2UgZm91ciBtb250aHMgIGJlZm9yZSB0aGUgUGxhbiB3YXMgY29uZmlybWVkLCB5ZXQgdG9vayBubyBhY3Rpb24gaW4gdGhlIGJhbmtydXB0Y3kgY2FzZSAgdW50aWwgdGVuIG1vbnRocyBhZnRlciB0aGUgUGxhbiB3YXMgY29uZmlybWVkIGJ5IHRoZSBDb3VydC5kZAIEDw8WAh8IBSkxMTQxKGQpKDEpLCAxMDEoMTApLCAxMTkxKGEpLCAxMTQ0LCA1MDMsIGRkAgUPDxYCHwgFBjkwMDYsIGRkAgcPZBYCAgEPDxYCHwkFWmh0dHBzOi8vcGx1cy5sZXhpcy5jb20vYXBpL3Blcm1hbGluay9mNjQwNjVlZC0zNmUxLTQ2OTItYWMwMS01NTU0YjczY2NjZWQvP2NvbnRleHQ9MTUzMDY3MWRkAggPZBYCAgEPDxYCHwkFlwFodHRwczovL3d3dy53ZXN0bGF3LmNvbS9Eb2N1bWVudC9JNDUxOWJjMTA1ZmY3MTFlZmE5MTRjNTU3M2RhOGY3OTEvVmlldy9GdWxsVGV4dC5odG1sP3RyYW5zaXRpb25UeXBlPURlZmF1bHQmY29udGV4dERhdGE9KHNjLkRlZmF1bHQpJlZSPTMuMCZSUz1jYmx0MS4wZGQCCQ8PFgIfCAUDMzcxZGQCBQ9kFhJmDw8WAh8IBQZTcGVjaWVkZAIBDw8WAh8IBRQyNC0xMDIzMCB8IDcwMCBUcnVzdGRkAgIPDxYCHwgFCjEyLzI3LzIwMjRkZAIDDw8WAh8IBeQHVGhlIENvdXJ0IGdhdmUgZnVsbCBmYWl0aCBhbmQgY3JlZGl0IHRvIHRoZSBVLlMuIEJhbmtydXB0Y3kgQ291cnQgZm9yIHRoZSBEaXN0cmljdCBvZiBNYXJ5bGFuZCYjMzk7cyBydWxpbmcgaW1wb3NpbmcgYW4gZXF1aXRhYmxlIHNlcnZpdHVkZSBhbmQgcHJvc3BlY3RpdmUgc3RheSByZWxpZWYgb24gdGhlIE5hcGxlcyBwcm9wZXJ0eSBhbmQgcmVsYXRlZCBsaXRpZ2F0aW9uLiBBcyB0aGUgTWFyeWxhbmQgY291cnQmIzM5O3Mgb3JkZXIgcHJlY2x1ZGVkIHRoZSBhdXRvbWF0aWMgc3RheSBmcm9tIGFwcGx5aW5nIHRvIGFueSBiYW5rcnVwdGN5IGNhc2UgZmlsZWQgYnkgYW4gZW50aXR5IGFzc2VydGluZyBhbiBpbnRlcmVzdCBpbiB0aGUgTmFwbGVzIHByb3BlcnR5IGZvciBmb3VyIHllYXJzLCB0aGUgYXV0b21hdGljIHN0YXkgZGlkIG5vdCBhcHBseSBpbiB0aGlzIGNhc2UgZmlsZWQgYnkgNzAwIFRydXN0LiBUaGUgQ291cnQgZnVydGhlciByZWFzb25lZCB0aGF0IHVuZGVyIDExIFUuUy5DLiAmYW1wO3NlY3Q7IDM2MihiKSgyMCkgYW5kIChiKSg0KShCKSwgNzAwIFRydXN0IG11c3QgbW92ZSBmb3IgcmVsaWVmIGZyb20gdGhlIHByb3NwZWN0aXZlIHN0YXkgcmVsaWVmIG9yZGVyIGFuZCBzaG93IGNoYW5nZWQgY2lyY3Vtc3RhbmNlcyBvciBnb29kIGNhdXNlIHRvIGhhdmUgdGhlIGF1dG9tYXRpYyBzdGF5IGltcG9zZWQsIHdoaWNoIGl0IGZhaWxlZCB0byBkby4gR2l2ZW4gdGhlIHByaW5jaXBhbHMmIzM5OyBoaXN0b3J5IG9mIGFidXNpdmUgYmFua3J1cHRjeSBmaWxpbmdzIGFuZCBsaXRpZ2F0aW9uIHRhY3RpY3MsIHRoZSBDb3VydCByZXNlcnZlZCBqdXJpc2RpY3Rpb24gdG8gY29uc2lkZXIgc2FuY3Rpb25zIHVuZGVyIDExIFUuUy5DLiAmYW1wO3NlY3Q7IDEwNShhKSBhbmQgRmVkLiBSLiBCYW5rci4gUC4gOTAxMSBhZ2FpbnN0IHRoZSBEZWJ0b3IsIGl0cyBwcmluY2lwYWxzLCBhbmQgY291bnNlbCBmb3IgYW55IGltcHJvcGVyIGZpbGluZ3MuZGQCBA8PFgIfCAUnMzYyKGEpLCAzNjIoZCkoNCksIDM2MihiKSgyMCksIDEwNShhKSwgZGQCBQ8PFgIfCAUGOTAxMSwgZGQCBw9kFgICAQ8PFgIfCQVaaHR0cHM6Ly9wbHVzLmxleGlzLmNvbS9hcGkvcGVybWFsaW5rLzU4ZTQ2NTFhLWM1OGYtNGQ2Ny1hNjNhLTgwZWJjMzFkOGE4My8%2FY29udGV4dD0xNTMwNjcxZGQCCA9kFgICAQ8PFgIfCQWXAWh0dHBzOi8vd3d3Lndlc3RsYXcuY29tL0RvY3VtZW50L0k4ZDQzM2UzMGM2ZDYxMWVmYmIxOWEzODEwMmI3OTdjMS9WaWV3L0Z1bGxUZXh0Lmh0bWw%2FdHJhbnNpdGlvblR5cGU9RGVmYXVsdCZjb250ZXh0RGF0YT0oc2MuRGVmYXVsdCkmVlI9My4wJlJTPWNibHQxLjBkZAIJDw8WAh8IBQMzNzVkZAIGD2QWEmYPDxYCHwgFBlNwZWNpZWRkAgEPDxYCHwgFFDI0LTEwMjMwIHwgNzAwIFRydXN0ZGQCAg8PFgIfCAUJMS8xMC8yMDI1ZGQCAw8PFgIfCAXHA1RoZSBPcmRlciB0byBTaG93IENhdXNlIFdoeSBUaGlzIENhc2UgU2hvdWxkIE5vdCBCZSBUcmFuc2ZlcnJlZCB0byB0aGUgQmFua3J1cHRjeSBDb3VydCBmb3IgdGhlIE1pZGRsZSBEaXN0cmljdCBvZiBGbG9yaWRhLCBvciBEaXNtaXNzZWQgd2FzIG5vdCBzYXRpc2ZpZWQuIFZlbnVlIHdhcyBpbXByb3BlciB1bmRlciAyOCBVLlMuQy4gJmFtcDtzZWN0OyAxNDA4LiBQdXJzdWFudCB0byAyOCBVLlMuQy4gJmFtcDtzZWN0OyAxNDEyIGFuZCBCYW5rcnVwdGN5IFJ1bGUgMTAxNChhKSgyKSwgdGhlIENvdXJ0IHRyYW5zZmVycyB0aGUgY2FzZSB0byAgdGhlIEJhbmtydXB0Y3kgQ291cnQgZm9yIHRoZSBNaWRkbGUgRGlzdHJpY3Qgb2YgRmxvcmlkYSwgRm9ydCBNeWVycyBEaXZpc2lvbiwgaW4gdGhlIGludGVyZXN0IG9mIGp1c3RpY2UgYW5kIGZvciB0aGUgY29udmVuaWVuY2Ugb2YgdGhlIHBhcnRpZXMuZGQCBA8PFgIfCAUGJm5ic3A7ZGQCBQ8PFgIfCAUGMTAxNCwgZGQCBw9kFgICAQ8PFgIfCQVaaHR0cHM6Ly9wbHVzLmxleGlzLmNvbS9hcGkvcGVybWFsaW5rLzFjNDBlMDYyLTFlNTEtNDAzMS1iNTE2LTM2NjkxMzI0NzEwMC8%2FY29udGV4dD0xNTMwNjcxZGQCCA9kFgICAQ8PFgIfCQWXAWh0dHBzOi8vd3d3Lndlc3RsYXcuY29tL0RvY3VtZW50L0k3NDkzNzM2MGQxZGUxMWVmOTI0OWFhZDdjMzJjMzg0Yy9WaWV3L0Z1bGxUZXh0Lmh0bWw%2FdHJhbnNpdGlvblR5cGU9RGVmYXVsdCZjb250ZXh0RGF0YT0oc2MuRGVmYXVsdCkmVlI9My4wJlJTPWNibHQxLjBkZAIJDw8WAh8IBQMzNzZkZGT5I4MbgpmMuPtSaYvo6EN2Ec6Z8zUhrRI2d5J6D5WlLQ%3D%3D&__VIEWSTATEGENERATOR=033D317F&__EVENTVALIDATION=%2FwEdABmadiT0mY08jOrtPGdwlOkR3hooyY00bhlQsIVuWdvv8PI6SfyW1F9IqKRyQI%2FIh3A%2FIN93rEJOvI0ccjw5MCh15TNoT9SABSKBAmWUfTuyB%2F2h28GUbf6dU3epdJfc8PGekHDttqApilNxvRto5X6AbjIVeOQFYAeEhvpJaHoryCCvv0Q1A8FGtpiKC6U0ZivWZzyhTplPGPUd2UjBXShlkq%2B17CebcjCuwyFon9jG4jAMSGqXnxXvEojXYXacKXKt26SzxlG%2FvRwbnBAs3YcsjNCthHUZFsiImMTBhCXYFROsU%2FPHlNt5l0LSretZQBhQ658zPOWpoqtBxsGucJ2%2FBfapguS6OYFwN7hoQk5FPTzmltaUM7aEAN%2Bg9cP%2Fm12%2FDdi58i%2FdsQ6aLnYJIUBm3SVGc7TQTkaYRi7LxfsdG%2F4AvX0gewG1wiK%2FYWEzqDRqpcc5oMPYTdupjCr4AuB5zRXsQmDhqvXqDjWMHsfV%2F9wOrZfjwyIq3oKHih0toHm0zgx9sn74aNMBDOfXC8NZCTC%2FEsOU4wCr%2FQMsAXlqIBHBMls1yzHwzD3Df3LOzGg%3D&txtCaseNumber=&txtCodeNumber=&txtRuleNumber=&ddlJudge=23&txtDebtorDefendant=&txtStartDate=01%2F01%2F2024&txtEndDate=04%2F23%2F2025&txtKeyWord=&{pdf_name}=View+Opinion"

        try:
            response = requests.post(
                url="https://ecf.flnb.uscourts.gov/opinions/",
                data=payload,
                proxies={
                    "http": "http://p.webshare.io:9999",
                    "https": "http://p.webshare.io:9999"
                },
                timeout=120
            )
            response.raise_for_status()

            with open(download_pdf_path, 'wb') as file:
                file.write(response.content)

            self.judgements_collection.update_one({"_id": objectId},
                                                  {"$set": {"processed": 0}})

            print("PDF downloaded successfully.")
        except requests.RequestException as e:
            print(f"Error while downloading the PDF: {e}")
            self.judgements_collection.update_many({"_id": objectId}, {
                "$set": {"processed": 2}})
        return download_pdf_path

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Published"
        self.url="https://ecf.flnb.uscourts.gov/opinions/"
        self._opt_attrs = self._opt_attrs + ["associated_codes"] + ["associated_rules"]

        self.valid_keys.update({
            "associated_codes",
            "associated_rules"
        })
        self._all_attrs = self._req_attrs + self._opt_attrs

        for attr in self._all_attrs:
            self.__setattr__(attr, None)

    def _get_associated_codes(self):
        return self._get_optional_field_by_id("associated_codes")

    def _get_associated_rules(self):
        return self._get_optional_field_by_id("associated_rules")


    def _process_html(self) -> None:
        print("inside process")
        # print(self.html.xpath(".//table[@id='DGOpinionSearch']"))
        count=0
        for row in self.html.xpath(".//table[@id='DGOpinionSearch']//tr"):
            if count==0:
                count+=1
                continue
            judge = row.xpath(".//td[1]/text()")[0]
            text = row.xpath(".//td[2]/text()")[0]
            docket , name = text.split(' | ')
            date = row.xpath(".//td[3]/text()")[0]
            month, day, year = date.split('/')
            case_date = f"{day}/{month}/{year}"
            summ = row.xpath(".//td[4]/text()")[0]
            ass_code = row.xpath(".//td[5]/text()")[0]
            ass_code=ass_code.replace('\xa0','')
            code = ass_code.split(', ')
            ass_rules=row.xpath(".//td[6]/text()")[0]
            ass_rules=ass_rules.replace('\xa0','')
            rules = ass_rules.split(', ')
            url_name = row.xpath(".//td[7]/input/@name")[0]
            url = self.url + url_name

            self.cases.append({
                "name": name,
                "url": url,
                "docket": [docket],
                "judge": [judge],
                "summary":summ,
                "associated_codes":[item for item in code if item],
                "associated_rules":[item for item in rules if item],
                "date": date,
            })


    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        year, month, day=str(start_date.date()).split('-')
        start = f"{month}/{day}/{year}"
        year, month, day=str(end_date.date()).split('-')
        end = f"{month}/{day}/{year}"
        self.parameters = {
            "__VIEWSTATE":"/wEPDwUKLTI3MzIyMDA2Ng9kFgICAQ9kFgQCAQ9kFgICBw8QDxYGHg1EYXRhVGV4dEZpZWxkBQhqdV9sbmFtZR4ORGF0YVZhbHVlRmllbGQFBWp1X2lkHgtfIURhdGFCb3VuZGdkEBUJCENhbGxhd2F5CUplbm5lbWFubgdLaWxsaWFuB01haG9uZXkHT2xkc2h1ZQVTYXVscwdTaHVsbWFuBlNwZWNpZQhTdGFmZm9yZBUJAjI1AjI0AjE4AjIxAjI2AjIyAjIwAjIzAjI3FCsDCWdnZ2dnZ2dnZ2RkAgUPZBYCAgMPPCsACwBkZAWlhECD+YqK31wZ2btn2OnA2AIiv/I/5rdtN6F2oaGt",
            "__VIEWSTATEGENERATOR":"033D317F",
            "__EVENTVALIDATION":"/wEdABMS1F22Ko3Jwnw97E/GNrVx3hooyY00bhlQsIVuWdvv8PI6SfyW1F9IqKRyQI/Ih3A/IN93rEJOvI0ccjw5MCh15TNoT9SABSKBAmWUfTuyB/2h28GUbf6dU3epdJfc8PGekHDttqApilNxvRto5X6AbjIVeOQFYAeEhvpJaHoryCCvv0Q1A8FGtpiKC6U0ZivWZzyhTplPGPUd2UjBXShlkq+17CebcjCuwyFon9jG4jAMSGqXnxXvEojXYXacKXKt26SzxlG/vRwbnBAs3YcsjNCthHUZFsiImMTBhCXYFROsU/PHlNt5l0LSretZQBhQ658zPOWpoqtBxsGucJ2/BfapguS6OYFwN7hoQk5FPTzmltaUM7aEAN+g9cP/m12/Ddi58i/dsQ6aLnYJIUBms/1nYJKHtWLVL19X+9ovmE6A6urmLH5v5EoUP0iG22U=",
            "ddlJudge":"23",
            "txtStartDate":start,
            "txtEndDate":end,
            "btnSubmit":"Search"
        }
        self.method="POST"

        if not self.downloader_executed:
            self.html = self._download()
            self._process_html()

        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return 0

    def get_class_name(self):
        return "bank_nd_fla"

    def get_court_type(self):
        return "Bankruptcy"

    def get_state_name(self):
        return "11th Circuit"

    def get_court_name(self):
        return "Bankruptcy Court Northern District of Florida"
