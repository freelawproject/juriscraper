from .scotus_docket_report_htm import SCOTUSDocketReportHTM
from .scotus_docket_report_html import SCOTUSDocketReportHTML
from .scotus_docket_report_json import SCOTUSDocketReportJSON
from .scotus_email import SCOTUSEmail

# Alias for compatibility.
SCOTUSDocketReport = SCOTUSDocketReportJSON

__all__ = [
    "SCOTUSDocketReport",
    "SCOTUSDocketReportHTML",
    "SCOTUSDocketReportHTM",
    "SCOTUSDocketReportJSON",
    "SCOTUSEmail",
]
