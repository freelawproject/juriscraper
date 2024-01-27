validation_schema = {
    "type": "object",
    "properties": {
        "case_names": {"type": "string"},
        "case_dates": {"type": "string", "format": "date-time"},
        "download_urls": {"type": "string"},
        "precedential_statuses": {"enum": ["Published", "Unpublished"]},
        "blocked_statuses": {"type": "boolean"},
        "date_filed_is_approximate": {"type": "boolean"},
        "citation": {"type": "string"},
        "docket": {"type": "string"},
    },
    "required": [
        "case_dates",
        "case_names",
        "download_urls",
        "precedential_statuses",
        "date_filed_is_approximate",
    ],
}
