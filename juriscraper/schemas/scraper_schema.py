"""
The schemas correspond to Courtlistener's Django models, which mirror
the DB models. These schemas should be updated when the CL models are updated

We keep the comments on the fields to a minimal. For further documentation
check CL models.py files
"""

# Citations are usually returned as a string, and parsed by `eyecite`
# Currently, this schema would be used by structured citations returned
# from `extract_from_text` step
# citation.type reference:
# 1 - Federal
# 2 - State
# 3 - State Regional
# 4 - Specialty
# 5 - Scotus Early
# 6 - Lexis
# 7 - West
# 8 - Neutral
citation = {
    "type": "object",
    "properties": {
        "volume": {"type": "integer"},
        "reporter": {"type": "string"},
        "page": {"type": "string"},
        "type": {"enum": [1, 2, 3, 4, 5, 6, 7, 8]},
    },
    "required": ["volume", "reporter", "page", "type"],
}


originating_court_information = {
    "type": "object",
    "properties": {
        "docket_number": {"type": "string"},
        "assigned_to_str": {"type": "string"},
        "ordering_judge_str": {"type": "string"},
        "court_reporter": {"type": "string"},
        "date_disposed": {"type": "string", "format": "date-time"},
        "date_filed": {"type": "string", "format": "date-time"},
        "date_judgment": {"type": "string", "format": "date-time"},
        "date_judgment_eod": {"type": "string", "format": "date-time"},
        "date_filed_noa": {"type": "string", "format": "date-time"},
        "date_received_coa": {"type": "string", "format": "date-time"},
    },
}


opinion = {
    "type": "object",
    "properties": {
        "author_str": {"type": "string"},
        "per_curiam": {"type": "boolean"},
        "joined_by_str": {"type": "string"},
        "page_count": {"type": "integer"},
        "download_url": {"type": "string"},
        "type": {
            "enum": [
                "010combined",
                "015unamimous",
                "020lead",
                "025plurality",
                "030concurrence",
                "035concurrenceinpart",
                "040dissent",
                "050addendum",
                "060remittitur",
                "070rehearing",
                "080onthemerits",
                "090onmotiontostrike",
            ]
        },
    },
    "required": ["download_url"],
}

# panel -> people_db.Person
# non_participating_judges -> people_db.Person
# source
# citation_count
# docket_id
cluster = {
    "type": "object",
    "properties": {
        "judges": {"type": "string"},
        "date_filed": {"type": "string", "format": "date-time"},
        "date_filed_is_approximate": {"type": "boolean"},
        "case_name_short": {"type": "string"},
        "case_name": {"type": "string"},
        "case_name_full": {"type": "string"},
        "scdb_votes_minority": {"type": "integer"},
        "scdb_votes_majority": {"type": "integer"},
        "scdb_id": {"type": "string"},
        "attorneys": {"type": "string"},
        "procedural_history": {"type": "string"},
        "nature_of_suit": {"type": "string"},
        "posture": {"type": "string"},
        "syllabus": {"type": "string"},
        "headnotes": {"type": "string"},
        "summary": {"type": "string"},
        "history": {"type": "string"},
        "other_dates": {"type": "string"},
        "cross_reference": {"type": "string"},
        "correction": {"type": "string"},
        "date_blocked": {"type": "string", "format": "date-time"},
        "blocked": {"type": "boolean"},
        "arguments": {"type": "string"},
        "headmatter": {"type": "string"},
        "precedential_status": {
            "enum": [
                "Published",
                "Unpublished",
                "Errata",
                "Separate",
                "In-chambers",
                "Relating-to",
                "Unknown",
            ]
        },
        # C stands for "Court Website". Since we are scraping court websites
        # This is the only option that we can output
        "source": {"enum": ["C"]},
    },
    "required": [
        "date_filed",
        "date_filed_is_approximate",
        "case_name",
        "precedential_status",
    ],
}

docket = {
    "type": "object",
    "properties": {
        # 2 stands for "Scraper". Since we are scraping this is the only
        # option to output
        "source": {"enum": [2]},
        "court": {"type": "string"},
        "appeal_from_str": {"type": "string"},
        "appeal_from": {"type": "string"},
        "assigned_to_str": {"type": "string"},
        "referred_to_str": {"type": "string"},
        "panel_str": {"type": "string"},
        "date_filed": {"type": "string", "format": "date-time"},
        "date_terminated": {"type": "string", "format": "date-time"},
        "date_last_filing": {"type": "string", "format": "date-time"},
        "case_name": {"type": "string"},
        "case_name_short": {"type": "string"},
        "case_name_full": {"type": "string"},
        "docket_number": {"type": "string"},
        "cause": {"type": "string"},
        "jury_demand": {"type": "string"},
        "appellate_fee_status": {"type": "string"},
        "date_blocked": {"type": "string", "format": "date-time"},
        "blocked": {"type": "boolean"},
        "originating_court_information": originating_court_information,
    },
    "required": [
        "docket_number",
        "case_name"
    ],
}


legacy = {
    "type": "object",
    "properties": {
        "case_names": {"type": "string"},
        "case_dates": {"type": "string", "format": "date-time"},
        "download_urls": {"type": "string"},
        "precedential_statuses": {"enum": ["Published", "Unpublished"]},
        "date_filed_is_approximate": {"type": "boolean"},
        "blocked_statuses": {"type": "boolean"},
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
