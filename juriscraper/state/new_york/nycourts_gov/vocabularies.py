"""The vocabularies the New York Court of Appeals publishes on Court-PASS.

These are the values the scraper classifies its output into, so that a consumer
never has to read the Court's prose. Every member's value is what Court-PASS
itself prints, except for document types, where it is the abbreviation the
Court's file-naming convention uses
(https://www.nycourts.gov/ctapps/techspecs.htm).

Each is a ``str`` enum, so a member compares and serializes as that value.
``None`` -- never a member -- is what the scraper reports when the Court stated
nothing, or when a file name was too mangled to read; see
``filename_convention`` for how each field can come back unset.

Adding to these is expected. A Court-PASS value that no member covers is
reported as unrecognized rather than guessed at, which is the signal that the
Court has started publishing something new.
"""

from dataclasses import dataclass
from enum import Enum

__all__ = [
    "COURT_GENERATED_DOCTYPES",
    "CourtVocabulary",
    "DOCTYPE_LABELS",
    "NOT_ON_FILINGS_TABLE",
    "ROLE_LABELS",
    "FilingDocType",
    "FilingRole",
    "FilingType",
    "IssueCategory",
    "IssueClassification",
    "IssueSubcategory",
    "classify_issue",
    "filing_type_from_value",
]


class CourtVocabulary(str, Enum):
    """Base for the vocabularies below.

    A member is the string Court-PASS prints, so it compares and serializes as
    that string, and carries two more things: ``code``, a small integer that is
    part of the published vocabulary and never changes or gets reused, and
    ``label``, its display form.

    Codes 0 and 999 are reserved and never belong to a member, so that a
    consumer storing codes has a value for "the Court stated nothing" and one
    for "the Court stated something this vocabulary does not cover" -- the two
    cases these enums express as ``None``.
    """

    code: int
    label: str

    def __new__(cls, value: str, code: int, label: str) -> "CourtVocabulary":
        member = str.__new__(cls, value)
        member._value_ = value
        member.code = code
        member.label = label
        return member


class FilingType(CourtVocabulary):
    """The filing types the FILINGS table on a docket page lists.

    A filing the scraper reconstructed from a document has none of these: no
    table row named it. Its role and document type are still classified.
    """

    AD_APPELLANT_BRIEF = "AD - Appellant Brief", 1, "AD - Appellant Brief"
    AD_APPELLANT_REPLY_BRIEF = (
        "AD - Appellant Reply Brief",
        2,
        "AD - Appellant Reply Brief",
    )
    AD_APPENDIX = "AD - Appendix", 3, "AD - Appendix"
    AD_RECORD = "AD - Record", 4, "AD - Record"
    AD_RESPONDENT_APPENDIX = (
        "AD - Respondent Appendix",
        5,
        "AD - Respondent Appendix",
    )
    AD_RESPONDENT_BRIEF = "AD - Respondent Brief", 6, "AD - Respondent Brief"
    AMICUS_BRIEF = "Amicus Brief", 7, "Amicus Brief"
    APPELLANT_APPENDIX = "Appellant Appendix", 8, "Appellant Appendix"
    APPELLANT_BRIEF = "Appellant Brief", 9, "Appellant Brief"
    APPELLANT_COA_RECORD = "Appellant COA Record", 10, "Appellant COA Record"
    APPELLANT_RECORD = "Appellant Record", 11, "Appellant Record"
    APPELLANT_REPLY_BRIEF = (
        "Appellant Reply Brief",
        12,
        "Appellant Reply Brief",
    )
    APPELLANT_RESPONSE_TO_AMICUS_BRIEF = (
        "Appellant Response to Amicus Brief",
        13,
        "Appellant Response to Amicus Brief",
    )
    APPELLANT_SSM_LETTER = "Appellant SSM Letter", 14, "Appellant SSM Letter"
    APPELLANT_RESPONDENT_BRIEF = (
        "Appellant-Respondent Brief",
        15,
        "Appellant-Respondent Brief",
    )
    APPELLANT_RESPONDENT_REPLY_BRIEF = (
        "Appellant-Respondent Reply Brief",
        16,
        "Appellant-Respondent Reply Brief",
    )
    LAW_GUARDIAN_BRIEF = "Law Guardian Brief", 17, "Law Guardian Brief"
    LAW_GUARDIAN_SSM_LETTER = (
        "Law Guardian SSM letter",
        18,
        "Law Guardian SSM letter",
    )
    PETITIONER_BRIEF = "Petitioner Brief", 19, "Petitioner Brief"
    PETITIONER_REPLY_BRIEF = (
        "Petitioner Reply Brief",
        20,
        "Petitioner Reply Brief",
    )
    PETITIONER_RESPONSE_REVIEW = (
        "Petitioner Response - Review",
        21,
        "Petitioner Response - Review",
    )
    PETITIONER_RESPONSE_SUSPENSION = (
        "Petitioner Response - Suspension",
        22,
        "Petitioner Response - Suspension",
    )
    PRO_SE_SUPPLEMENTAL_BRIEF = (
        "Pro Se Supplemental Brief",
        23,
        "Pro Se Supplemental Brief",
    )
    RECORD_ON_REVIEW = "Record on Review", 24, "Record on Review"
    RESPONDENT_APPENDIX = "Respondent Appendix", 25, "Respondent Appendix"
    RESPONDENT_BRIEF = "Respondent Brief", 26, "Respondent Brief"
    RESPONDENT_COA_RECORD = (
        "Respondent COA Record",
        27,
        "Respondent COA Record",
    )
    RESPONDENT_RESPONSE_SUSPENSION = (
        "Respondent Response - Suspension",
        28,
        "Respondent Response - Suspension",
    )
    RESPONDENT_RESPONSE_TO_AMICUS_BRIEF = (
        "Respondent Response to Amicus Brief",
        29,
        "Respondent Response to Amicus Brief",
    )
    RESPONDENT_SSM_LETTER = (
        "Respondent SSM Letter",
        30,
        "Respondent SSM Letter",
    )
    RESPONDENT_APPELLANT_BRIEF = (
        "Respondent-Appellant Brief",
        31,
        "Respondent-Appellant Brief",
    )
    RESPONDENT_APPELLANT_REPLY_BRIEF = (
        "Respondent-Appellant Reply Brief",
        32,
        "Respondent-Appellant Reply Brief",
    )
    SCJC_DETERMINATION = "SCJC Determination", 33, "SCJC Determination"
    SCJC_RESPONSE_SUSPENSION = (
        "SCJC Response - Suspension",
        34,
        "SCJC Response - Suspension",
    )


class FilingRole(CourtVocabulary):
    """The role of the party a filing belongs to.

    Read from the filing type, or from the role segment of a file name, where
    filers use a wide range of abbreviations for each of these.
    """

    AMICUS = "amicus", 1, "Amicus"
    APPELLANT = "appellant", 2, "Appellant"
    APPELLANT_RESPONDENT = "appellant-respondent", 3, "Appellant-Respondent"
    LAW_GUARDIAN = "law guardian", 4, "Law Guardian"
    PETITIONER = "petitioner", 5, "Petitioner"
    PRO_SE = "pro se", 6, "Pro Se"
    RESPONDENT = "respondent", 7, "Respondent"
    RESPONDENT_APPELLANT = "respondent-appellant", 8, "Respondent-Appellant"
    SCJC = "scjc", 9, "SCJC"

    # ---- not a role the Court publishes; see FilingDocType's docstring ----

    INTERVENOR = "intervenor", 10, "Intervenor"
    """A party who intervened rather than appealing or answering -- most often
    the Attorney General, defending a statute's constitutionality on a criminal
    appeal. The FILINGS table has no intervenor filing type, but the ATTORNEY
    DETAILS section names the role for 80 parties and filers abbreviate it
    ``ivnr``. 20 files."""

    INTERVENOR_APPELLANT = "intervenor-appellant", 11, "Intervenor-Appellant"
    """An intervenor on the appellant's side; the court names this role for 20
    parties. Written ``-intervenor-app-`` in a file name, the same way a
    cross-appeal writes its two roles."""

    INTERVENOR_RESPONDENT = (
        "intervenor-respondent",
        12,
        "Intervenor-Respondent",
    )
    """An intervenor on the respondent's side; 36 parties."""


class FilingDocType(CourtVocabulary):
    """The kind of document a filing consists of.

    Values are the Court's own abbreviations. The three underscore-prefixed
    members are the court's own output rather than a party's filing, and
    ``_combined`` is one PDF that satisfies two filings at once.

    **Members with a code of 26 or higher are ours, not the Court's.** The
    Court's published abbreviation list
    (https://www.nycourts.gov/ctapps/techspecs.htm) covers the documents that
    carry a FILINGS-table filing type, and stops there -- but filers upload
    plenty that it does not name, and those arrived here as an unreadable
    doctype, which is worse than a wrong one: an unreadable type also disables
    the type veto in the matcher, leaving the file free to claim any FILINGS
    row left in the docket. Each of these was drawn from the corpus rather
    than invented, and the docstring on each says how many files it covers so
    a later reader can judge whether it earned its place.

    Their ``value`` is a plausible abbreviation in the Court's style but is
    *not* published by it, so nothing on a Court-PASS page will ever equal one
    -- they are reached only through the file-name patterns in
    :mod:`~juriscraper.state.new_york.nycourts_gov.filename_convention`. None
    of them appears in ``FILING_TYPE_MAP`` either, for the same reason, so all
    of them are listed in :data:`NOT_ON_FILINGS_TABLE`.

    Codes are assigned in the order members were added, not alphabetically,
    because a code, once published, never changes or gets reused.
    """

    AD_APPENDIX = "adappdx", 1, "AD - Appendix"
    AD_BRIEF = "adbrf", 2, "AD - Brief"
    AD_RECORD = "adrec", 3, "AD - Record"
    AD_REPLY_BRIEF = "adreplybrf", 4, "AD - Reply Brief"
    ADDENDUM = "addendum", 5, "Addendum"
    AMICUS_BRIEF = "amicbrf", 6, "Amicus Brief"
    APPENDIX = "appdx", 7, "Appendix"
    BRIEF = "brf", 8, "Brief"
    BRIEF_AND_APPENDIX = "_combined", 9, "Brief and Appendix"
    COMPENDIUM = "compendium", 10, "Compendium"
    DECISION = "_decision", 11, "Decision"
    EXHIBITS = "exhibits", 12, "Exhibits"
    MOTION = "mot", 13, "Motion"
    MOTION_FOR_LEAVE_TO_APPEAL = "motforlv", 14, "Motion for Leave to Appeal"
    OPPOSITION = "opp", 15, "Opposition"
    OPPOSITION_TO_MOTION_FOR_LEAVE_TO_APPEAL = (
        "opptomotforlv",
        16,
        "Opposition to Motion for Leave to Appeal",
    )
    ORAL_ARGUMENT_TRANSCRIPT = "_transcript", 17, "Oral Argument Transcript"
    ORAL_ARGUMENT_WEBCAST = "_webcast", 18, "Oral Argument Webcast"
    RECORD = "rec", 19, "Record"
    REPLY_BRIEF = "replybrf", 20, "Reply Brief"
    RESPONSE_TO_AMICUS_BRIEF = "brfrspamic", 21, "Response to Amicus Brief"
    SSM_LETTER = "ssmltrbrf", 22, "SSM Letter"
    SSM_REPLY_LETTER = "ssmreplyltrbrf", 23, "SSM Reply Letter"
    SUPPLEMENTAL_APPENDIX = "suppappdx", 24, "Supplemental Appendix"
    SUPPLEMENTAL_BRIEF = "suppbrf", 25, "Supplemental Brief"

    # ---- classifications the Court does not publish (see the docstring) ----

    PRE_SENTENCE_REPORT = "psr", 26, "Pre-Sentence Report"
    """The probation department's pre-sentence investigation report, filed as
    record material on a criminal appeal. Filers write ``PSI`` as often as
    ``PSR`` and frequently mark it confidential. 25 files."""

    AD_ORDER = "adorder", 27, "AD - Order"
    """An Appellate Division order, filed as part of the record. Distinct from
    ``_decision``, which is this Court's own output: a party filed this one,
    and the court that made it is not this court. 5 files."""

    AD_MOTION = "admot", 28, "AD - Motion"
    """A motion made in the Appellate Division -- usually for reargument or for
    leave to appeal here -- filed as record material. 11 files."""

    AFFIDAVIT_OF_SERVICE = "aos", 29, "Affidavit of Service"
    """Proof that a filing was served. Not a ``mot``: it is the paperwork
    accompanying some other document, and letting it read as a motion (the
    pattern for which matches a bare ``affidavit``) put it in reach of motion
    entries. 8 files."""

    JURISDICTIONAL_RESPONSE = "jurrsp", 30, "Jurisdictional Response"
    """A party's response to the Court's inquiry into its own jurisdiction over
    the appeal. 7 files."""

    APPELLATE_TERM_BRIEF = "atermbrf", 31, "Appellate Term - Brief"
    """A brief filed in the Appellate Term, the intermediate court for appeals
    from the New York City and district courts. The ``AD`` members cover the
    Appellate Division only, so these had nowhere to go. 7 files."""

    POST_ARGUMENT_BRIEF = "postargbrf", 32, "Post-Argument Brief"
    """A brief or submission filed after oral argument, usually at the Court's
    request. 5 files."""

    HEARING_TRANSCRIPT = "hearingtranscript", 33, "Hearing Transcript"
    """A transcript of proceedings *below* -- a trial, or a hearing before an
    administrative tribunal such as OATH -- filed by a party as part of the
    record.

    Deliberately separate from ``_transcript``, which is this Court's own
    recording of its oral argument. Reading a trial transcript as that made it
    court-generated, which excluded it from matching and labelled a party's
    record material as the court's output. 10 files."""


class IssueCategory(CourtVocabulary):
    """The category of an issue the Court assigned to a case."""

    ACCOUNTS_AND_ACCOUNTING = (
        "Accounts and Accounting",
        1,
        "Accounts and Accounting",
    )
    ACTIONS = "Actions", 2, "Actions"
    ADMINISTRATIVE_LAW = "Administrative Law", 3, "Administrative Law"
    ADMIRALTY = "Admiralty", 4, "Admiralty"
    ADOPTION = "Adoption", 5, "Adoption"
    ADVERSE_POSSESSION = "Adverse Possession", 6, "Adverse Possession"
    AGRICULTURE = "Agriculture", 7, "Agriculture"
    ANIMALS = "Animals", 8, "Animals"
    APPEAL = "Appeal", 9, "Appeal"
    APPEARANCES = "Appearances", 10, "Appearances"
    APPRAISALS = "Appraisals", 11, "Appraisals"
    ARBITRATION = "Arbitration", 12, "Arbitration"
    ARREST = "Arrest", 13, "Arrest"
    ASSOCIATIONS = "Associations", 14, "Associations"
    ATTACHMENT = "Attachment", 15, "Attachment"
    ATTORNEY_GENERAL = "Attorney General", 16, "Attorney General"
    ATTORNEY_AND_CLIENT = "Attorney and Client", 17, "Attorney and Client"
    AVIATION = "Aviation", 18, "Aviation"
    BAIL = "Bail", 19, "Bail"
    BANKRUPTCY = "Bankruptcy", 20, "Bankruptcy"
    BANKS_AND_BANKING = "Banks and Banking", 21, "Banks and Banking"
    BILLS_NOTES_AND_CHECKS = (
        "Bills, Notes and Checks",
        22,
        "Bills, Notes and Checks",
    )
    BONDS = "Bonds", 23, "Bonds"
    BRIDGES = "Bridges", 24, "Bridges"
    BROKERS = "Brokers", 25, "Brokers"
    CARRIERS = "Carriers", 26, "Carriers"
    CHILDREN_BORN_OUT_OF_WEDLOCK = (
        "Children Born out of Wedlock",
        27,
        "Children Born out of Wedlock",
    )
    CIVIL_RIGHTS = "Civil Rights", 28, "Civil Rights"
    CIVIL_SERVICE = "Civil Service", 29, "Civil Service"
    COLLEGES_AND_UNIVERSITIES = (
        "Colleges and Universities",
        30,
        "Colleges and Universities",
    )
    COMPROMISE_AND_SETTLEMENT = (
        "Compromise and Settlement",
        31,
        "Compromise and Settlement",
    )
    CONDOMINIUMS_AND_COOPERATIVES = (
        "Condominiums and Cooperatives",
        32,
        "Condominiums and Cooperatives",
    )
    CONFLICT_OF_LAWS = "Conflict of Laws", 33, "Conflict of Laws"
    CONSTITUTIONAL_LAW = "Constitutional Law", 34, "Constitutional Law"
    CONSUMER_PROTECTION = "Consumer Protection", 35, "Consumer Protection"
    CONTEMPT = "Contempt", 36, "Contempt"
    CONTRACTS = "Contracts", 37, "Contracts"
    CONTRIBUTION = "Contribution", 38, "Contribution"
    CORPORATIONS = "Corporations", 39, "Corporations"
    COSTS = "Costs", 40, "Costs"
    COUNTIES = "Counties", 41, "Counties"
    COURTS = "Courts", 42, "Courts"
    COVENANTS = "Covenants", 43, "Covenants"
    CRIMES = "Crimes", 44, "Crimes"
    CRIMES_AND_CRIMINAL_PROCEDURE = (
        "Crimes and Criminal Procedure",
        45,
        "Crimes and Criminal Procedure",
    )
    DAMAGES = "Damages", 46, "Damages"
    DEAD_BODIES = "Dead Bodies", 47, "Dead Bodies"
    DECLARATORY_JUDGMENTS = (
        "Declaratory Judgments",
        48,
        "Declaratory Judgments",
    )
    DEEDS = "Deeds", 49, "Deeds"
    DISCLOSURE = "Disclosure", 50, "Disclosure"
    DISMISSAL_AND_NONSUIT = (
        "Dismissal and Nonsuit",
        51,
        "Dismissal and Nonsuit",
    )
    DISTRICT_AND_PROSECUTING_ATTORNEYS = (
        "District and Prosecuting Attorneys",
        52,
        "District and Prosecuting Attorneys",
    )
    ELECTIONS = "Elections", 53, "Elections"
    EMINENT_DOMAIN = "Eminent Domain", 54, "Eminent Domain"
    EMPLOYMENT_RELATIONSHIPS = (
        "Employment Relationships",
        55,
        "Employment Relationships",
    )
    ENVIRONMENTAL_CONSERVATION = (
        "Environmental Conservation",
        56,
        "Environmental Conservation",
    )
    EQUITY = "Equity", 57, "Equity"
    ESTOPPEL = "Estoppel", 58, "Estoppel"
    EVIDENCE = "Evidence", 59, "Evidence"
    EXECUTORS_AND_ADMINISTRATORS = (
        "Executors and Administrators",
        60,
        "Executors and Administrators",
    )
    FRAUD = "Fraud", 61, "Fraud"
    FRAUDS_STATUTE_OF = "Frauds, Statute of", 62, "Frauds, Statute of"
    GAS_AND_OIL = "Gas and Oil", 63, "Gas and Oil"
    GIFTS = "Gifts", 64, "Gifts"
    GRAND_JURY = "Grand Jury", 65, "Grand Jury"
    GUARDIAN_AND_WARD = "Guardian and Ward", 66, "Guardian and Ward"
    HABEAS_CORPUS = "Habeas Corpus", 67, "Habeas Corpus"
    HEALTH = "Health", 68, "Health"
    HIGHWAYS = "Highways", 69, "Highways"
    HORSE_RACING = "Horse Racing", 70, "Horse Racing"
    HOSPITALS = "Hospitals", 71, "Hospitals"
    HUSBAND_AND_WIFE = "Husband and Wife", 72, "Husband and Wife"
    INCAPACITATED_AND_MENTALLY_DISABLED_PERSONS = (
        "Incapacitated and Mentally Disabled Persons",
        73,
        "Incapacitated and Mentally Disabled Persons",
    )
    INDEMNITY = "Indemnity", 74, "Indemnity"
    INFANTS = "Infants", 75, "Infants"
    INJUNCTIONS = "Injunctions", 76, "Injunctions"
    INSURANCE = "Insurance", 77, "Insurance"
    INTEREST = "Interest", 78, "Interest"
    INTERNATIONAL_LAW = "International Law", 79, "International Law"
    INTOXICATING_LIQUORS = "Intoxicating Liquors", 80, "Intoxicating Liquors"
    JUDGES = "Judges", 81, "Judges"
    JUDGMENTS = "Judgments", 82, "Judgments"
    JURY = "Jury", 83, "Jury"
    LABOR = "Labor", 84, "Labor"
    LABOR_UNIONS = "Labor Unions", 85, "Labor Unions"
    LANDLORD_AND_TENANT = "Landlord and Tenant", 86, "Landlord and Tenant"
    LEGISLATURE = "Legislature", 87, "Legislature"
    LIBEL_AND_SLANDER = "Libel and Slander", 88, "Libel and Slander"
    LICENSES = "Licenses", 89, "Licenses"
    LIENS = "Liens", 90, "Liens"
    LIMITATION_OF_ACTIONS = (
        "Limitation of Actions",
        91,
        "Limitation of Actions",
    )
    LIMITED_LIABILITY_COMPANIES = (
        "Limited Liability Companies",
        92,
        "Limited Liability Companies",
    )
    LOCAL_LAWS = "Local Laws", 93, "Local Laws"
    MARRIAGE = "Marriage", 94, "Marriage"
    MENTAL_HEALTH = "Mental Health", 95, "Mental Health"
    MINES_AND_MINERALS = "Mines and Minerals", 96, "Mines and Minerals"
    MONOPOLIES = "Monopolies", 97, "Monopolies"
    MORTGAGES = "Mortgages", 98, "Mortgages"
    MOTIONS_AND_ORDERS = "Motions and Orders", 99, "Motions and Orders"
    MOTOR_VEHICLES = "Motor Vehicles", 100, "Motor Vehicles"
    MUNICIPAL_CORPORATIONS = (
        "Municipal Corporations",
        101,
        "Municipal Corporations",
    )
    NAMES = "Names", 102, "Names"
    NATIVE_AMERICANS = "Native Americans", 103, "Native Americans"
    NAVIGABLE_WATERS = "Navigable Waters", 104, "Navigable Waters"
    NEGLIGENCE = "Negligence", 105, "Negligence"
    NEWSPAPERS = "Newspapers", 106, "Newspapers"
    PARDON = "Pardon", 107, "Pardon"
    PARENT_AND_CHILD = "Parent and Child", 108, "Parent and Child"
    PARKS_AND_PARKWAYS = "Parks and Parkways", 109, "Parks and Parkways"
    PAROLE = "Parole", 110, "Parole"
    PARTIES = "Parties", 111, "Parties"
    PARTITION = "Partition", 112, "Partition"
    PARTNERSHIP = "Partnership", 113, "Partnership"
    PHYSICIANS_AND_SURGEONS = (
        "Physicians and Surgeons",
        114,
        "Physicians and Surgeons",
    )
    PLEADING = "Pleading", 115, "Pleading"
    POWERS = "Powers", 116, "Powers"
    PRINCIPAL_AND_AGENT = "Principal and Agent", 117, "Principal and Agent"
    PRISONS_AND_PRISONERS = (
        "Prisons and Prisoners",
        118,
        "Prisons and Prisoners",
    )
    PROCEEDING_AGAINST_BODY_OR_OFFICER = (
        "Proceeding Against Body or Officer",
        119,
        "Proceeding Against Body or Officer",
    )
    PROCESS = "Process", 120, "Process"
    PRODUCTS_LIABILITY = "Products Liability", 121, "Products Liability"
    PUBLIC_AUTHORITIES = "Public Authorities", 122, "Public Authorities"
    PUBLIC_HOUSING = "Public Housing", 123, "Public Housing"
    PUBLIC_OFFICERS = "Public Officers", 124, "Public Officers"
    PUBLIC_UTILITIES = "Public Utilities", 125, "Public Utilities"
    RECEIVERS = "Receivers", 126, "Receivers"
    RECORDS = "Records", 127, "Records"
    RELEASE = "Release", 128, "Release"
    RELIGIOUS_CORPORATIONS_AND_ASSOCIATIONS = (
        "Religious Corporations and Associations",
        129,
        "Religious Corporations and Associations",
    )
    SCHOOLS = "Schools", 130, "Schools"
    SEAMEN = "Seamen", 131, "Seamen"
    SEARCHES_AND_SEIZURES = (
        "Searches and Seizures",
        132,
        "Searches and Seizures",
    )
    SECURED_TRANSACTIONS = "Secured Transactions", 133, "Secured Transactions"
    SOCIAL_SERVICES = "Social Services", 134, "Social Services"
    SPECIFIC_PERFORMANCE = "Specific Performance", 135, "Specific Performance"
    STATE = "State", 136, "State"
    STATUTES = "Statutes", 137, "Statutes"
    STIPULATIONS = "Stipulations", 138, "Stipulations"
    SUBROGATION = "Subrogation", 139, "Subrogation"
    SURETYSHIP_AND_GUARANTEE = (
        "Suretyship and Guarantee",
        140,
        "Suretyship and Guarantee",
    )
    TAXATION = "Taxation", 141, "Taxation"
    TELECOMMUNICATIONS = "Telecommunications", 142, "Telecommunications"
    TORTS = "Torts", 143, "Torts"
    TRIAL = "Trial", 144, "Trial"
    TRUSTS = "Trusts", 145, "Trusts"
    UNEMPLOYMENT_INSURANCE = (
        "Unemployment Insurance",
        146,
        "Unemployment Insurance",
    )
    UNITED_STATES = "United States", 147, "United States"
    USURY = "Usury", 148, "Usury"
    VENDOR_AND_PURCHASER = "Vendor and Purchaser", 149, "Vendor and Purchaser"
    WATERS_AND_WATERCOURSES = (
        "Waters and Watercourses",
        150,
        "Waters and Watercourses",
    )
    WILLS = "Wills", 151, "Wills"
    WITNESSES = "Witnesses", 152, "Witnesses"
    WORKERS_COMPENSATION = (
        "Workers' Compensation",
        153,
        "Workers' Compensation",
    )


class IssueSubcategory(CourtVocabulary):
    """The subcategory of an issue the Court assigned to a case.

    Flat rather than nested under :class:`IssueCategory`, because the Court
    reuses a subcategory across categories -- "Accounting" appears under both
    Receivers and Trusts, and 44 others are shared the same way.
    """

    ABUSED_OR_NEGLECTED_CHILD = (
        "Abused or Neglected Child",
        1,
        "Abused or Neglected Child",
    )
    ACADEMIC_AND_MOOT_QUESTIONS = (
        "Academic and Moot Questions",
        2,
        "Academic and Moot Questions",
    )
    ACCELERATION_CLAUSE = "Acceleration Clause", 3, "Acceleration Clause"
    ACCOUNT = "Account", 4, "Account"
    ACCOUNT_STATED = "Account Stated", 5, "Account Stated"
    ACCOUNTING = "Accounting", 6, "Accounting"
    ACCUSATORY_INSTRUMENT = "Accusatory Instrument", 7, "Accusatory Instrument"
    ACKNOWLEDGMENT_OF_PATERNITY = (
        "Acknowledgment of Paternity",
        8,
        "Acknowledgment of Paternity",
    )
    ACT_OF_STATE_DOCTRINE = "Act of State Doctrine", 9, "Act of State Doctrine"
    ACTION_AGAINST_ACCOUNTANTS = (
        "Action against Accountants",
        10,
        "Action against Accountants",
    )
    ACTION_AGAINST_INSURER = (
        "Action against Insurer",
        11,
        "Action against Insurer",
    )
    ACTION_AGAINST_UNION = "Action against Union", 12, "Action against Union"
    ACTION_BY_ASSOCIATION = (
        "Action by Association",
        13,
        "Action by Association",
    )
    ACTIONABLE_WORDS = "Actionable Words", 14, "Actionable Words"
    ACTIONABLE_WRONG = "Actionable Wrong", 15, "Actionable Wrong"
    ACTIONS_IN_WHICH_RECOVERABLE = (
        "Actions in Which Recoverable",
        16,
        "Actions in Which Recoverable",
    )
    ADMINISTRATIVE_INSPECTIONS = (
        "Administrative Inspections",
        17,
        "Administrative Inspections",
    )
    ADMINISTRATIVE_REVIEW = (
        "Administrative Review",
        18,
        "Administrative Review",
    )
    ADMISSION = "Admission", 19, "Admission"
    ADMISSION_AGAINST_INTEREST = (
        "Admission against Interest",
        20,
        "Admission against Interest",
    )
    ADMISSION_TO_PRACTICE = (
        "Admission to Practice",
        21,
        "Admission to Practice",
    )
    ADOPTION_OF_ADULT = "Adoption of Adult", 22, "Adoption of Adult"
    ADOPTION_OF_LOCAL_LAWS = (
        "Adoption of Local Laws",
        23,
        "Adoption of Local Laws",
    )
    ADULT_CARE_FACILITIES = (
        "Adult Care Facilities",
        24,
        "Adult Care Facilities",
    )
    ADVANCE_PAYMENT = "Advance Payment", 25, "Advance Payment"
    AFFIRMATIVE_DEFENSE = "Affirmative Defense", 26, "Affirmative Defense"
    AGENCY_DEFENSE_IN_NARCOTICS_PROSECUTION = (
        "Agency Defense in Narcotics Prosecution",
        27,
        "Agency Defense in Narcotics Prosecution",
    )
    AGENTS_AND_BROKERS = "Agents and Brokers", 28, "Agents and Brokers"
    AGGRAVATED_UNLICENSED_OPERATION_OF_MOTOR_VEHICLE = (
        "Aggravated Unlicensed Operation of Motor Vehicle",
        29,
        "Aggravated Unlicensed Operation of Motor Vehicle",
    )
    AGREEMENT_FOR_BENEFIT_OF_THIRD_PERSONS = (
        "Agreement for Benefit of Third Persons",
        30,
        "Agreement for Benefit of Third Persons",
    )
    AGREEMENT_TO_ARBITRATE = (
        "Agreement to Arbitrate",
        31,
        "Agreement to Arbitrate",
    )
    AIR_POLLUTION_CONTROL = (
        "Air Pollution Control",
        32,
        "Air Pollution Control",
    )
    AMBIGUOUS_CONTRACTS = "Ambiguous Contracts", 33, "Ambiguous Contracts"
    AMENDMENT = "Amendment", 34, "Amendment"
    ANNEXATION_OF_SCHOOL_DISTRICT = (
        "Annexation of School District",
        35,
        "Annexation of School District",
    )
    ANSWER = "Answer", 36, "Answer"
    APPARENT_AUTHORITY = "Apparent Authority", 37, "Apparent Authority"
    APPEAL = "Appeal", 38, "Appeal"
    APPEAL_AS_OF_RIGHT = "Appeal as of Right", 39, "Appeal as of Right"
    APPEALABLE_PAPER = "Appealable Paper", 40, "Appealable Paper"
    APPEARANCE_BY_CORPORATION_COUNSEL = (
        "Appearance by Corporation Counsel",
        41,
        "Appearance by Corporation Counsel",
    )
    APPELLATE_DIVISION = "Appellate Division", 42, "Appellate Division"
    APPOINTMENT = "Appointment", 43, "Appointment"
    APPOINTMENT_AND_PROMOTION = (
        "Appointment and Promotion",
        44,
        "Appointment and Promotion",
    )
    APPOINTMENT_OF_GUARDIAN = (
        "Appointment of Guardian",
        45,
        "Appointment of Guardian",
    )
    APPORTIONMENT = "Apportionment", 46, "Apportionment"
    APPORTIONMENT_OF_LIABILITY_AMONG_JOINT_TORTFEASORS = (
        "Apportionment of Liability among Joint Tortfeasors",
        47,
        "Apportionment of Liability among Joint Tortfeasors",
    )
    APPROPRIATIONS = "Appropriations", 48, "Appropriations"
    ARCHITECT_S_MALPRACTICE = (
        "Architect's Malpractice",
        49,
        "Architect's Malpractice",
    )
    ARGUMENT_AND_CONDUCT_OF_COUNSEL = (
        "Argument and Conduct of Counsel",
        50,
        "Argument and Conduct of Counsel",
    )
    ARRAIGNMENT = "Arraignment", 51, "Arraignment"
    ARREST = "Arrest", 52, "Arrest"
    ARSON = "Arson", 53, "Arson"
    ASSAULT = "Assault", 54, "Assault"
    ASSESSMENT = "Assessment", 55, "Assessment"
    ASSIGNMENT_OF_COUNSEL = (
        "Assignment of Counsel",
        56,
        "Assignment of Counsel",
    )
    ASSISTED_OUTPATIENT_TREATMENT = (
        "Assisted Outpatient Treatment",
        57,
        "Assisted Outpatient Treatment",
    )
    ASSUMPTION_OF_RISK = "Assumption of Risk", 58, "Assumption of Risk"
    AT_WILL_EMPLOYMENT = "At-Will Employment", 59, "At-Will Employment"
    ATTEMPT = "Attempt", 60, "Attempt"
    ATTORNEY_S_LIEN = "Attorney's Lien", 61, "Attorney's Lien"
    AUTOMATIC_RENEWAL = "Automatic Renewal", 62, "Automatic Renewal"
    AUTOMOBILE_INSURANCE = "Automobile Insurance", 63, "Automobile Insurance"
    AVAILABILITY_OF_DEFENSE = (
        "Availability of Defense",
        64,
        "Availability of Defense",
    )
    AWARD = "Award", 65, "Award"
    AWARD_IN_EXCESS_OF_ARBITRATOR_S_POWERS = (
        "Award in Excess of Arbitrator's Powers",
        66,
        "Award in Excess of Arbitrator's Powers",
    )
    BAIL_BONDS = "Bail Bonds", 67, "Bail Bonds"
    BALLOTS = "Ballots", 68, "Ballots"
    BANK_ACCOUNTS = "Bank Accounts", 69, "Bank Accounts"
    BENEFITS = "Benefits", 70, "Benefits"
    BEST_EVIDENCE_RULE = "Best Evidence Rule", 71, "Best Evidence Rule"
    BIDS_AND_BIDDERS = "Bids and Bidders", 72, "Bids and Bidders"
    BOARD_OF_DIRECTORS = "Board of Directors", 73, "Board of Directors"
    BOARD_OF_EDUCATION = "Board of Education", 74, "Board of Education"
    BREACH_OF_FIDUCIARY_DUTY = (
        "Breach of Fiduciary Duty",
        75,
        "Breach of Fiduciary Duty",
    )
    BREACH_OR_PERFORMANCE_OF_CONTRACT = (
        "Breach or Performance of Contract",
        76,
        "Breach or Performance of Contract",
    )
    BURGLARY = "Burglary", 77, "Burglary"
    BUS_DRIVERS = "Bus Drivers", 78, "Bus Drivers"
    BUSINESS_INSURANCE = "Business Insurance", 79, "Business Insurance"
    BUSINESS_AND_FINANCIAL_TAX = (
        "Business and Financial Tax",
        80,
        "Business and Financial Tax",
    )
    CALCULATION_OF_SENTENCE = (
        "Calculation of Sentence",
        81,
        "Calculation of Sentence",
    )
    CANCELLATION = "Cancellation", 82, "Cancellation"
    CAPACITY_TO_SUE = "Capacity to Sue", 83, "Capacity to Sue"
    CARRIER_S_LIEN = "Carrier's Lien", 84, "Carrier's Lien"
    CASHIER_S_CHECK = "Cashier's Check", 85, "Cashier's Check"
    CAUSAL_RELATION = "Causal Relation", 86, "Causal Relation"
    CERTIFICATION_OF_RETIRED_JUSTICE_TO_REMAIN_IN_OFFICE = (
        "Certification of Retired Justice to Remain in Office",
        87,
        "Certification of Retired Justice to Remain in Office",
    )
    CERTIORARI = "Certiorari", 88, "Certiorari"
    CHANGE_OF_NAME = "Change of Name", 89, "Change of Name"
    CHARTER_SCHOOLS = "Charter Schools", 90, "Charter Schools"
    CHEMICAL_TESTS = "Chemical Tests", 91, "Chemical Tests"
    CIVIL_CONTEMPT = "Civil Contempt", 92, "Civil Contempt"
    CLAIM_AGAINST_STATE = "Claim against State", 93, "Claim against State"
    CLAIM_IN_AMENDED_PLEADING = (
        "Claim in Amended Pleading",
        94,
        "Claim in Amended Pleading",
    )
    CLAIMS_AGAINST_ESTATE = (
        "Claims against Estate",
        95,
        "Claims against Estate",
    )
    CLAIMS_AGAINST_PUBLIC_AUTHORITIES = (
        "Claims against Public Authorities",
        96,
        "Claims against Public Authorities",
    )
    CLASS_ACTIONS = "Class Actions", 97, "Class Actions"
    CLASSIFICATION = "Classification", 98, "Classification"
    COERCION = "Coercion", 99, "Coercion"
    COLLATERAL_ESTOPPEL = "Collateral Estoppel", 100, "Collateral Estoppel"
    COLLATERAL_SOURCE_OF_PAYMENT = (
        "Collateral Source of Payment",
        101,
        "Collateral Source of Payment",
    )
    COLLECTIVE_BARGAINING = (
        "Collective Bargaining",
        102,
        "Collective Bargaining",
    )
    COLLECTIVE_BARGAINING_AGREEMENT = (
        "Collective Bargaining Agreement",
        103,
        "Collective Bargaining Agreement",
    )
    COLLISION = "Collision", 104, "Collision"
    COMMENCEMENT = "Commencement", 105, "Commencement"
    COMMENCEMENT_OF_ACTION_AFTER_TERMINATION_OF_PRIOR_ACTION = (
        "Commencement of Action after Termination of Prior Action",
        106,
        "Commencement of Action after Termination of Prior Action",
    )
    COMMISSION_OF_CORRECTION = (
        "Commission of Correction",
        107,
        "Commission of Correction",
    )
    COMMON_CHARGES_AND_SPECIAL_ASSESSMENTS = (
        "Common Charges and Special Assessments",
        108,
        "Common Charges and Special Assessments",
    )
    COMMUNITY_COLLEGE = "Community College", 109, "Community College"
    COMPARATIVE_NEGLIGENCE = (
        "Comparative Negligence",
        110,
        "Comparative Negligence",
    )
    COMPENSATION = "Compensation", 111, "Compensation"
    COMPENSATION_AND_BENEFITS = (
        "Compensation and Benefits",
        112,
        "Compensation and Benefits",
    )
    COMPLAINT = "Complaint", 113, "Complaint"
    COMPTROLLER = "Comptroller", 114, "Comptroller"
    COMPULSORY_ARBITRATION = (
        "Compulsory Arbitration",
        115,
        "Compulsory Arbitration",
    )
    COMPUTATION = "Computation", 116, "Computation"
    CONDITION_PRECEDENT = "Condition Precedent", 117, "Condition Precedent"
    CONDITIONAL_RELEASE = "Conditional Release", 118, "Conditional Release"
    CONDITIONS_OF_CONFINEMENT = (
        "Conditions of Confinement",
        119,
        "Conditions of Confinement",
    )
    CONDUCT_OF_TRIAL_JUDGE = (
        "Conduct of Trial Judge",
        120,
        "Conduct of Trial Judge",
    )
    CONFESSION = "Confession", 121, "Confession"
    CONFESSION_OF_JUDGMENT = (
        "Confession of Judgment",
        122,
        "Confession of Judgment",
    )
    CONFIRMING_OR_VACATING_AWARD = (
        "Confirming or Vacating Award",
        123,
        "Confirming or Vacating Award",
    )
    CONFLICTS_OF_INTEREST = (
        "Conflicts of Interest",
        124,
        "Conflicts of Interest",
    )
    CONSCIOUS_PAIN_AND_SUFFERING = (
        "Conscious Pain and Suffering",
        125,
        "Conscious Pain and Suffering",
    )
    CONSEQUENTIAL_DAMAGES = (
        "Consequential Damages",
        126,
        "Consequential Damages",
    )
    CONSOLIDATION_AND_SEVERANCE = (
        "Consolidation and Severance",
        127,
        "Consolidation and Severance",
    )
    CONSPIRACY = "Conspiracy", 128, "Conspiracy"
    CONSTRUCTION = "Construction", 129, "Construction"
    CONSTRUCTION_OF_POLICY = (
        "Construction of Policy",
        130,
        "Construction of Policy",
    )
    CONSTRUCTIVE_DISCHARGE = (
        "Constructive Discharge",
        131,
        "Constructive Discharge",
    )
    CONSTRUCTIVE_FRAUD = "Constructive Fraud", 132, "Constructive Fraud"
    CONSTRUCTIVE_TRUST = "Constructive Trust", 133, "Constructive Trust"
    CONSUMER_CREDIT = "Consumer Credit", 134, "Consumer Credit"
    CONTRACT_FOR_SALE_OF_REAL_PROPERTY = (
        "Contract for Sale of Real Property",
        135,
        "Contract for Sale of Real Property",
    )
    CONTRACTUAL_INDEMNIFICATION = (
        "Contractual Indemnification",
        136,
        "Contractual Indemnification",
    )
    CONTRACTUAL_LIMITATION_OF_LIABILITY = (
        "Contractual Limitation of Liability",
        137,
        "Contractual Limitation of Liability",
    )
    CONTRACTUAL_LIMITATIONS_PERIOD = (
        "Contractual Limitations Period",
        138,
        "Contractual Limitations Period",
    )
    CONTRIBUTIONS = "Contributions", 139, "Contributions"
    CONTRIBUTORY_NEGLIGENCE = (
        "Contributory Negligence",
        140,
        "Contributory Negligence",
    )
    CONTROLLED_SUBSTANCES = (
        "Controlled Substances",
        141,
        "Controlled Substances",
    )
    CONVERSION_OF_ARTICLE_78_PROCEEDING_TO_DECLARATORY_JUDGMENT_ACTION = (
        "Conversion of Article 78 Proceeding to Declaratory Judgment Action",
        142,
        "Conversion of Article 78 Proceeding to Declaratory Judgment Action",
    )
    COOPERATIVE_APARTMENTS = (
        "Cooperative Apartments",
        143,
        "Cooperative Apartments",
    )
    CORROBORATION_OF_ACCOMPLICE_TESTIMONY = (
        "Corroboration of Accomplice Testimony",
        144,
        "Corroboration of Accomplice Testimony",
    )
    COUNSEL_FEES = "Counsel Fees", 145, "Counsel Fees"
    COUNTY_EXECUTIVE = "County Executive", 146, "County Executive"
    COURT_OF_APPEALS = "Court of Appeals", 147, "Court of Appeals"
    COURT_OF_CLAIMS = "Court of Claims", 148, "Court of Claims"
    COVENANT_RUNNING_WITH_LAND = (
        "Covenant Running with Land",
        149,
        "Covenant Running with Land",
    )
    COVENANT_OF_GOOD_FAITH_AND_FAIR_DEALING = (
        "Covenant of Good Faith and Fair Dealing",
        150,
        "Covenant of Good Faith and Fair Dealing",
    )
    COVERAGE = "Coverage", 151, "Coverage"
    CREATION = "Creation", 152, "Creation"
    CRIMINAL_CONTEMPT = "Criminal Contempt", 153, "Criminal Contempt"
    CRIMINAL_NEGLIGENCE = "Criminal Negligence", 154, "Criminal Negligence"
    CRIMINALLY_NEGLIGENT_HOMICIDE = (
        "Criminally Negligent Homicide",
        155,
        "Criminally Negligent Homicide",
    )
    CUSTODY = "Custody", 156, "Custody"
    DAMAGES = "Damages", 157, "Damages"
    DANGEROUS_INSTRUMENT = "Dangerous Instrument", 158, "Dangerous Instrument"
    DE_FACTO_APPROPRIATION = (
        "De Facto Appropriation",
        159,
        "De Facto Appropriation",
    )
    DEALERS = "Dealers", 160, "Dealers"
    DEATH_BENEFITS = "Death Benefits", 161, "Death Benefits"
    DECEPTIVE_ACTS_AND_PRACTICES = (
        "Deceptive Acts and Practices",
        162,
        "Deceptive Acts and Practices",
    )
    DEFAULT_JUDGMENT = "Default Judgment", 163, "Default Judgment"
    DEFECTIVE_PROCEEDING = "Defective Proceeding", 164, "Defective Proceeding"
    DEFECTIVELY_DESIGNED_PRODUCT = (
        "Defectively Designed Product",
        165,
        "Defectively Designed Product",
    )
    DEFENDANT_AS_WITNESS = "Defendant as Witness", 166, "Defendant as Witness"
    DEFENSE_AND_INDEMNIFICATION_OF_EMPLOYEE = (
        "Defense and Indemnification of Employee",
        167,
        "Defense and Indemnification of Employee",
    )
    DEFICIENCY_JUDGMENTS = "Deficiency Judgments", 168, "Deficiency Judgments"
    DELEGATION_OF_LEGISLATIVE_POWER = (
        "Delegation of Legislative Power",
        169,
        "Delegation of Legislative Power",
    )
    DELIBERATIONS = "Deliberations", 170, "Deliberations"
    DENIAL = "Denial", 171, "Denial"
    DENIAL_OF_REMAINING_FAMILY_MEMBER_STATUS = (
        "Denial of Remaining Family Member Status",
        172,
        "Denial of Remaining Family Member Status",
    )
    DENTISTS = "Dentists", 173, "Dentists"
    DESIGNATING_PETITIONS = (
        "Designating Petitions",
        174,
        "Designating Petitions",
    )
    DETERMINATION_OF_CLAIM_TO_REAL_PROPERTY = (
        "Determination of Claim to Real Property",
        175,
        "Determination of Claim to Real Property",
    )
    DIPLOMA_BY_ESTOPPEL_DOCTRINE = (
        "Diploma by Estoppel Doctrine",
        176,
        "Diploma by Estoppel Doctrine",
    )
    DIRECTORS_AND_OFFICERS_LIABILITY_POLICY = (
        "Directors and Officers Liability Policy",
        177,
        "Directors and Officers Liability Policy",
    )
    DISABILITY_BENEFITS = "Disability Benefits", 178, "Disability Benefits"
    DISABILITY_INSURANCE = "Disability Insurance", 179, "Disability Insurance"
    DISCIPLINARY_PROCEEDINGS = (
        "Disciplinary Proceedings",
        180,
        "Disciplinary Proceedings",
    )
    DISCIPLINARY_PUNISHMENT = (
        "Disciplinary Punishment",
        181,
        "Disciplinary Punishment",
    )
    DISCIPLINE_OF_INMATES = (
        "Discipline of Inmates",
        182,
        "Discipline of Inmates",
    )
    DISCLAIMER_OF_COVERAGE = (
        "Disclaimer of Coverage",
        183,
        "Disclaimer of Coverage",
    )
    DISCLOSURE = "Disclosure", 184, "Disclosure"
    DISCONTINUANCE = "Discontinuance", 185, "Discontinuance"
    DISCOVERY_AND_INSPECTION = (
        "Discovery and Inspection",
        186,
        "Discovery and Inspection",
    )
    DISCRIMINATION_BASED_ON_AGE = (
        "Discrimination Based on Age",
        187,
        "Discrimination Based on Age",
    )
    DISCRIMINATION_BASED_ON_DISABILITY = (
        "Discrimination Based on Disability",
        188,
        "Discrimination Based on Disability",
    )
    DISCRIMINATION_BASED_ON_GENDER = (
        "Discrimination Based on Gender",
        189,
        "Discrimination Based on Gender",
    )
    DISCRIMINATION_BASED_ON_MARITAL_STATUS = (
        "Discrimination Based on Marital Status",
        190,
        "Discrimination Based on Marital Status",
    )
    DISCRIMINATION_BASED_ON_PREVIOUS_CRIMINAL_PROSECUTION = (
        "Discrimination Based on Previous Criminal Prosecution",
        191,
        "Discrimination Based on Previous Criminal Prosecution",
    )
    DISCRIMINATION_BASED_ON_SEXUAL_ORIENTATION = (
        "Discrimination Based on Sexual Orientation",
        192,
        "Discrimination Based on Sexual Orientation",
    )
    DISCRIMINATION_IN_EMPLOYMENT = (
        "Discrimination in Employment",
        193,
        "Discrimination in Employment",
    )
    DISCRIMINATION_IN_HOUSING = (
        "Discrimination in Housing",
        194,
        "Discrimination in Housing",
    )
    DISCRIMINATORY_RENTAL_PRACTICES = (
        "Discriminatory Rental Practices",
        195,
        "Discriminatory Rental Practices",
    )
    DISINTERMENT = "Disinterment", 196, "Disinterment"
    DISMISSAL = "Dismissal", 197, "Dismissal"
    DISMISSAL_OF_COMPLAINT = (
        "Dismissal of Complaint",
        198,
        "Dismissal of Complaint",
    )
    DISMISSAL_OF_PETITION = (
        "Dismissal of Petition",
        199,
        "Dismissal of Petition",
    )
    DISORDERLY_CONDUCT = "Disorderly Conduct", 200, "Disorderly Conduct"
    DISQUALIFICATION = "Disqualification", 201, "Disqualification"
    DISQUALIFICATION_FOR_FALSE_REPRESENTATION = (
        "Disqualification for False Representation",
        202,
        "Disqualification for False Representation",
    )
    DISQUALIFICATION_OR_TERMINATION_AS_MEDICAID_PROVIDER = (
        "Disqualification or Termination as Medicaid Provider",
        203,
        "Disqualification or Termination as Medicaid Provider",
    )
    DISREGARDING_CORPORATE_ENTITY = (
        "Disregarding Corporate Entity",
        204,
        "Disregarding Corporate Entity",
    )
    DISSOLUTION = "Dissolution", 205, "Dissolution"
    DIVORCE = "Divorce", 206, "Divorce"
    DOCTRINE_OF_ADMINISTRATIVE_FINALITY = (
        "Doctrine of Administrative Finality",
        207,
        "Doctrine of Administrative Finality",
    )
    DOCUMENTARY_EVIDENCE = "Documentary Evidence", 208, "Documentary Evidence"
    DONNELLY_ACT = "Donnelly Act", 209, "Donnelly Act"
    DOUBLE_JEOPARDY = "Double Jeopardy", 210, "Double Jeopardy"
    DRAM_SHOP_ACT = "Dram Shop Act", 211, "Dram Shop Act"
    DUE_PROCESS_OF_LAW = "Due Process of Law", 212, "Due Process of Law"
    DUTY = "Duty", 213, "Duty"
    DUTY_TO_DEFEND_AND_INDEMNIFY = (
        "Duty to Defend and Indemnify",
        214,
        "Duty to Defend and Indemnify",
    )
    DUTY_TO_DEFEND_OR_INDEMNIFY_PUBLIC_EMPLOYEE = (
        "Duty to Defend or Indemnify Public Employee",
        215,
        "Duty to Defend or Indemnify Public Employee",
    )
    EAVESDROPPING = "Eavesdropping", 216, "Eavesdropping"
    EAVESDROPPING_WARRANTS = (
        "Eavesdropping Warrants",
        217,
        "Eavesdropping Warrants",
    )
    EDUCATION_OF_CHILDREN_WITH_DISABILITIES = (
        "Education of Children with Disabilities",
        218,
        "Education of Children with Disabilities",
    )
    ELECTION_OF_REMEDIES = "Election of Remedies", 219, "Election of Remedies"
    ELECTIONS = "Elections", 220, "Elections"
    ELECTIVE_SHARE_OF_SURVIVING_SPOUSE = (
        "Elective Share of Surviving Spouse",
        221,
        "Elective Share of Surviving Spouse",
    )
    EMERGENCY_ADMISSION_TO_HOSPITAL = (
        "Emergency Admission to Hospital",
        222,
        "Emergency Admission to Hospital",
    )
    EMERGENCY_DOCTRINE = "Emergency Doctrine", 223, "Emergency Doctrine"
    EMPLOYEE_OR_INDEPENDENT_CONTRACTOR = (
        "Employee or Independent Contractor",
        224,
        "Employee or Independent Contractor",
    )
    EMPLOYMENT_CONTRACTS = "Employment Contracts", 225, "Employment Contracts"
    ENDANGERING_WELFARE_OF_CHILD = (
        "Endangering Welfare of Child",
        226,
        "Endangering Welfare of Child",
    )
    ENFORCEMENT = "Enforcement", 227, "Enforcement"
    ENTERPRISE_CORRUPTION = (
        "Enterprise Corruption",
        228,
        "Enterprise Corruption",
    )
    ENVIRONMENTAL_IMPACT_STATEMENT = (
        "Environmental Impact Statement",
        229,
        "Environmental Impact Statement",
    )
    ENVIRONMENTAL_QUALITY_REVIEW = (
        "Environmental Quality Review",
        230,
        "Environmental Quality Review",
    )
    EQUAL_ACCESS_TO_JUSTICE_ACT = (
        "Equal Access to Justice Act",
        231,
        "Equal Access to Justice Act",
    )
    EQUAL_PROTECTION_OF_LAWS = (
        "Equal Protection of Laws",
        232,
        "Equal Protection of Laws",
    )
    EQUITABLE_DISTRIBUTION = (
        "Equitable Distribution",
        233,
        "Equitable Distribution",
    )
    EQUITABLE_ESTOPPEL = "Equitable Estoppel", 234, "Equitable Estoppel"
    ESCAPE = "Escape", 235, "Escape"
    EVICTION = "Eviction", 236, "Eviction"
    EVIDENCE = "Evidence", 237, "Evidence"
    EXAMINATION_BEFORE_TRIAL = (
        "Examination before Trial",
        238,
        "Examination before Trial",
    )
    EXAMINATION_OF_CLAIMS = (
        "Examination of Claims",
        239,
        "Examination of Claims",
    )
    EXCESS_COVERAGE = "Excess Coverage", 240, "Excess Coverage"
    EXCLUSIONS = "Exclusions", 241, "Exclusions"
    EXCLUSIVENESS_OF_REMEDY = (
        "Exclusiveness of Remedy",
        242,
        "Exclusiveness of Remedy",
    )
    EXECUTION = "Execution", 243, "Execution"
    EXECUTIVE_CLEMENCY = "Executive Clemency", 244, "Executive Clemency"
    EXEMPTION_FROM_LIABILITY_FOR_NEGLIGENCE = (
        "Exemption from Liability for Negligence",
        245,
        "Exemption from Liability for Negligence",
    )
    EXEMPTION_FROM_PUBLIC_HEARING = (
        "Exemption from Public Hearing",
        246,
        "Exemption from Public Hearing",
    )
    EXEMPTIONS = "Exemptions", 247, "Exemptions"
    EXISTENCE_OF_EMPLOYER_EMPLOYEE_RELATIONSHIP = (
        "Existence of Employer-Employee Relationship",
        248,
        "Existence of Employer-Employee Relationship",
    )
    EXPERT_WITNESS = "Expert Witness", 249, "Expert Witness"
    EXPOSURE_TO_TOXIC_SUBSTANCES = (
        "Exposure to Toxic Substances",
        250,
        "Exposure to Toxic Substances",
    )
    EXTENSION_OF_STATUTE_OF_LIMITATIONS = (
        "Extension of Statute of Limitations",
        251,
        "Extension of Statute of Limitations",
    )
    EXTENT_OF_DISABILITY = "Extent of Disability", 252, "Extent of Disability"
    FAILURE_TO_ENTER_DEFAULT_JUDGMENT_WITHIN_ONE_YEAR = (
        "Failure to Enter Default Judgment within One Year",
        253,
        "Failure to Enter Default Judgment within One Year",
    )
    FAILURE_TO_EXHAUST_ADMINISTRATIVE_REMEDIES = (
        "Failure to Exhaust Administrative Remedies",
        254,
        "Failure to Exhaust Administrative Remedies",
    )
    FAILURE_TO_SERVE_COMPLAINT = (
        "Failure to Serve Complaint",
        255,
        "Failure to Serve Complaint",
    )
    FAILURE_TO_WARN_OF_DANGER = (
        "Failure to Warn of Danger",
        256,
        "Failure to Warn of Danger",
    )
    FAIR_COMMENT = "Fair Comment", 257, "Fair Comment"
    FAIR_TRIAL = "Fair Trial", 258, "Fair Trial"
    FALSE_IMPRISONMENT = "False Imprisonment", 259, "False Imprisonment"
    FALSIFYING_BUSINESS_RECORDS = (
        "Falsifying Business Records",
        260,
        "Falsifying Business Records",
    )
    FAMILY_OFFENSE = "Family Offense", 261, "Family Offense"
    FEDERAL_ARBITRATION_ACT = (
        "Federal Arbitration Act",
        262,
        "Federal Arbitration Act",
    )
    FEDERAL_CIVIL_RIGHTS_CLAIM = (
        "Federal Civil Rights Claim",
        263,
        "Federal Civil Rights Claim",
    )
    FEDERAL_PREEMPTION = "Federal Preemption", 264, "Federal Preemption"
    FEES = "Fees", 265, "Fees"
    FINALITY_OF_JUDGMENTS_AND_ORDERS = (
        "Finality of Judgments and Orders",
        266,
        "Finality of Judgments and Orders",
    )
    FINANCIAL_DISCLOSURE = "Financial Disclosure", 267, "Financial Disclosure"
    FINANCIAL_SANCTIONS_AGAINST_ATTORNEY = (
        "Financial Sanctions against Attorney",
        268,
        "Financial Sanctions against Attorney",
    )
    FIREARMS = "Firearms", 269, "Firearms"
    FIREFIGHTERS = "Firefighters", 270, "Firefighters"
    FIRST_AMENDMENT_RIGHTS = (
        "First Amendment Rights",
        271,
        "First Amendment Rights",
    )
    FITNESS_TO_PROCEED_TO_TRIAL = (
        "Fitness to Proceed to Trial",
        272,
        "Fitness to Proceed to Trial",
    )
    FOOD_STAMP_ALLOWANCE = "Food Stamp Allowance", 273, "Food Stamp Allowance"
    FORECLOSURE = "Foreclosure", 274, "Foreclosure"
    FOREIGN_CORPORATION = "Foreign Corporation", 275, "Foreign Corporation"
    FOREIGN_JUDGMENT = "Foreign Judgment", 276, "Foreign Judgment"
    FORESEEABILITY = "Foreseeability", 277, "Foreseeability"
    FORGED_INDORSEMENT = "Forged Indorsement", 278, "Forged Indorsement"
    FORGERY = "Forgery", 279, "Forgery"
    FORMATION_OF_CONTRACT = (
        "Formation of Contract",
        280,
        "Formation of Contract",
    )
    FORUM_NON_CONVENIENS = "Forum Non Conveniens", 281, "Forum Non Conveniens"
    FOSTER_CARE = "Foster Care", 282, "Foster Care"
    FOUR_MONTH_STATUTE_OF_LIMITATIONS = (
        "Four-Month Statute of Limitations",
        283,
        "Four-Month Statute of Limitations",
    )
    FOUR_YEAR_STATUTE_OF_LIMITATIONS = (
        "Four-Year Statute of Limitations",
        284,
        "Four-Year Statute of Limitations",
    )
    FRANCHISE_TAX_ON_BUSINESS_CORPORATIONS = (
        "Franchise Tax on Business Corporations",
        285,
        "Franchise Tax on Business Corporations",
    )
    FRAUD = "Fraud", 286, "Fraud"
    FRAUD_IN_INDUCEMENT = "Fraud in Inducement", 287, "Fraud in Inducement"
    FREEDOM_OF_INFORMATION_LAW = (
        "Freedom of Information Law",
        288,
        "Freedom of Information Law",
    )
    FREEDOM_OF_RELIGION = "Freedom of Religion", 289, "Freedom of Religion"
    FREEDOM_OF_SPEECH = "Freedom of Speech", 290, "Freedom of Speech"
    FREEDOM_OF_WORSHIP = "Freedom of Worship", 291, "Freedom of Worship"
    FRIVOLOUS_CONDUCT = "Frivolous Conduct", 292, "Frivolous Conduct"
    FULL_FAITH_AND_CREDIT = (
        "Full Faith and Credit",
        293,
        "Full Faith and Credit",
    )
    FUNDS_TRANSFERS = "Funds Transfers", 294, "Funds Transfers"
    FUTURE_DAMAGES = "Future Damages", 295, "Future Damages"
    GARBAGE_DISPOSAL = "Garbage Disposal", 296, "Garbage Disposal"
    GAS_AND_OIL_LEASE = "Gas and Oil Lease", 297, "Gas and Oil Lease"
    GENERAL_CORPORATION_TAX = (
        "General Corporation Tax",
        298,
        "General Corporation Tax",
    )
    GIFT_OF_PUBLIC_FUNDS = "Gift of Public Funds", 299, "Gift of Public Funds"
    GRIEVANCES = "Grievances", 300, "Grievances"
    GUARANTEE_OF_PROMISSORY_NOTE = (
        "Guarantee of Promissory Note",
        301,
        "Guarantee of Promissory Note",
    )
    GUARDIAN_FOR_PERSONAL_NEEDS_OR_PROPERTY_MANAGEMENT = (
        "Guardian for Personal Needs or Property Management",
        302,
        "Guardian for Personal Needs or Property Management",
    )
    HARASSMENT = "Harassment", 303, "Harassment"
    HARMLESS_AND_PREJUDICIAL_ERROR = (
        "Harmless and Prejudicial Error",
        304,
        "Harmless and Prejudicial Error",
    )
    HARNESS_RACES = "Harness Races", 305, "Harness Races"
    HATE_CRIMES = "Hate Crimes", 306, "Hate Crimes"
    HAZARDOUS_WASTE = "Hazardous Waste", 307, "Hazardous Waste"
    HEARING = "Hearing", 308, "Hearing"
    HIGHWAY_BY_USE = "Highway by Use", 309, "Highway by Use"
    HINDERING_PROSECUTION = (
        "Hindering Prosecution",
        310,
        "Hindering Prosecution",
    )
    HOME_IMPROVEMENT_CONTRACTORS = (
        "Home Improvement Contractors",
        311,
        "Home Improvement Contractors",
    )
    HOME_RULE_POWERS = "Home Rule Powers", 312, "Home Rule Powers"
    HOMEOWNER_S_INSURANCE = (
        "Homeowner's Insurance",
        313,
        "Homeowner's Insurance",
    )
    HOSTILE_POSSESSION = "Hostile Possession", 314, "Hostile Possession"
    HOTEL_AND_MOTEL_OCCUPANCY_TAX = (
        "Hotel and Motel Occupancy Tax",
        315,
        "Hotel and Motel Occupancy Tax",
    )
    HOURS_AND_WAGES = "Hours and Wages", 316, "Hours and Wages"
    HUNTING_AND_FISHING_LICENSES = (
        "Hunting and Fishing Licenses",
        317,
        "Hunting and Fishing Licenses",
    )
    IDENTIFICATION_OF_DEFENDANT = (
        "Identification of Defendant",
        318,
        "Identification of Defendant",
    )
    ILLEGAL_CONTRACTS = "Illegal Contracts", 319, "Illegal Contracts"
    IMPLIED_COVENANTS = "Implied Covenants", 320, "Implied Covenants"
    IMPROPER_LABOR_PRACTICES = (
        "Improper Labor Practices",
        321,
        "Improper Labor Practices",
    )
    INADEQUATE_AND_EXCESSIVE_DAMAGES = (
        "Inadequate and Excessive Damages",
        322,
        "Inadequate and Excessive Damages",
    )
    INDICTMENT = "Indictment", 323, "Indictment"
    INDUSTRIAL_DEVELOPMENT_AGENCIES = (
        "Industrial Development Agencies",
        324,
        "Industrial Development Agencies",
    )
    INDUSTRIAL_DEVELOPMENT_AGENCY = (
        "Industrial Development Agency",
        325,
        "Industrial Development Agency",
    )
    INFORMATION = "Information", 326, "Information"
    INFORMERS = "Informers", 327, "Informers"
    INJURIES_ARISING_OUT_OF_AND_IN_COURSE_OF_EMPLOYMENT = (
        "Injuries Arising out of and in Course of Employment",
        328,
        "Injuries Arising out of and in Course of Employment",
    )
    INJURIES_TO_BICYCLIST = (
        "Injuries to Bicyclist",
        329,
        "Injuries to Bicyclist",
    )
    INJURIES_TO_FIREFIGHTERS = (
        "Injuries to Firefighters",
        330,
        "Injuries to Firefighters",
    )
    INJURIES_TO_PEDESTRIANS = (
        "Injuries to Pedestrians",
        331,
        "Injuries to Pedestrians",
    )
    INJURIES_TO_POLICE_OFFICERS = (
        "Injuries to Police Officers",
        332,
        "Injuries to Police Officers",
    )
    INSANITY = "Insanity", 333, "Insanity"
    INSTRUCTIONS = "Instructions", 334, "Instructions"
    INSURANCE_FRAUD = "Insurance Fraud", 335, "Insurance Fraud"
    INTENTIONAL_INFLICTION_OF_EMOTIONAL_DISTRESS = (
        "Intentional Infliction of Emotional Distress",
        336,
        "Intentional Infliction of Emotional Distress",
    )
    INTER_VIVOS_GIFT = "Inter Vivos Gift", 337, "Inter Vivos Gift"
    INTEREST_ON_JUDGMENT = "Interest on Judgment", 338, "Interest on Judgment"
    INTERFERENCE_WITH_CONTRACTUAL_RELATIONS = (
        "Interference with Contractual Relations",
        339,
        "Interference with Contractual Relations",
    )
    INTERNAL_TRIBAL_AFFAIRS = (
        "Internal Tribal Affairs",
        340,
        "Internal Tribal Affairs",
    )
    INTERNET_SERVICES = "Internet Services", 341, "Internet Services"
    INTERVENTION = "Intervention", 342, "Intervention"
    INTOXICATION = "Intoxication", 343, "Intoxication"
    INVERSE_CONDEMNATION = "Inverse Condemnation", 344, "Inverse Condemnation"
    INVESTIGATORY_POWERS = "Investigatory Powers", 345, "Investigatory Powers"
    INVOLUNTARY_ADMINISTRATION_OF_DRUG = (
        "Involuntary Administration of Drug",
        346,
        "Involuntary Administration of Drug",
    )
    INVOLUNTARY_COMMITMENT = (
        "Involuntary Commitment",
        347,
        "Involuntary Commitment",
    )
    JONES_ACT = "Jones Act", 348, "Jones Act"
    JUDICIAL_ESTOPPEL = "Judicial Estoppel", 349, "Judicial Estoppel"
    JUDICIAL_REVIEW = "Judicial Review", 350, "Judicial Review"
    JUDICIAL_REVIEW_OF_ACADEMIC_DISCRETION = (
        "Judicial Review of Academic Discretion",
        351,
        "Judicial Review of Academic Discretion",
    )
    JUDICIAL_SALARIES = "Judicial Salaries", 352, "Judicial Salaries"
    JURISDICTION = "Jurisdiction", 353, "Jurisdiction"
    JURISDICTION_OF_OFFENSES = (
        "Jurisdiction of Offenses",
        354,
        "Jurisdiction of Offenses",
    )
    JURORS = "Jurors", 355, "Jurors"
    JUSTIFICATION = "Justification", 356, "Justification"
    JUVENILE_DELINQUENTS = "Juvenile Delinquents", 357, "Juvenile Delinquents"
    JUVENILE_OFFENDER = "Juvenile Offender", 358, "Juvenile Offender"
    JUVENILE_OFFENDERS = "Juvenile Offenders", 359, "Juvenile Offenders"
    KIDNAPPING = "Kidnapping", 360, "Kidnapping"
    KNOWLEDGE_OF_VICIOUS_PROPENSITY = (
        "Knowledge of Vicious Propensity",
        361,
        "Knowledge of Vicious Propensity",
    )
    LACK_OF_INFORMED_CONSENT = (
        "Lack of Informed Consent",
        362,
        "Lack of Informed Consent",
    )
    LANDMARKS = "Landmarks", 363, "Landmarks"
    LARCENY = "Larceny", 364, "Larceny"
    LAW_GOVERNING_CONTRACT_ACTIONS = (
        "Law Governing Contract Actions",
        365,
        "Law Governing Contract Actions",
    )
    LAW_GOVERNING_TORT_ACTIONS = (
        "Law Governing Tort Actions",
        366,
        "Law Governing Tort Actions",
    )
    LAW_OF_THE_CASE = "Law of the Case", 367, "Law of the Case"
    LEASE = "Lease", 368, "Lease"
    LEAVING_SCENE_OF_INCIDENT = (
        "Leaving Scene of Incident",
        369,
        "Leaving Scene of Incident",
    )
    LESSER_INCLUDED_OFFENSE = (
        "Lesser Included Offense",
        370,
        "Lesser Included Offense",
    )
    LETTERS_OF_ADMINISTRATION = (
        "Letters of Administration",
        371,
        "Letters of Administration",
    )
    LIABILITY_INSURANCE = "Liability Insurance", 372, "Liability Insurance"
    LIABILITY_FOR_ACTS_OF_INDEPENDENT_CONTRACTOR = (
        "Liability for Acts of Independent Contractor",
        373,
        "Liability for Acts of Independent Contractor",
    )
    LIABILITY_FOR_ANIMAL_BITE = (
        "Liability for Animal Bite",
        374,
        "Liability for Animal Bite",
    )
    LIABILITY_FOR_INJURIES = (
        "Liability for Injuries",
        375,
        "Liability for Injuries",
    )
    LIABILITY_OF_MANUFACTURER_S_SUCCESSOR_CORPORATION = (
        "Liability of Manufacturer's Successor Corporation",
        376,
        "Liability of Manufacturer's Successor Corporation",
    )
    LIABILITY_OF_PARENT_CORPORATION = (
        "Liability of Parent Corporation",
        377,
        "Liability of Parent Corporation",
    )
    LICENSES = "Licenses", 378, "Licenses"
    LIFE_INSURANCE = "Life Insurance", 379, "Life Insurance"
    LIMITATION_OF_RIGHT_TO_COMPENSATION = (
        "Limitation of Right to Compensation",
        380,
        "Limitation of Right to Compensation",
    )
    LIMITED_PARTNERSHIP = "Limited Partnership", 381, "Limited Partnership"
    LIQUIDATED_DAMAGES = "Liquidated Damages", 382, "Liquidated Damages"
    LIQUIDATION_OF_INSURER = (
        "Liquidation of Insurer",
        383,
        "Liquidation of Insurer",
    )
    LOAN_BROKERS = "Loan Brokers", 384, "Loan Brokers"
    LOCAL_REGULATION = "Local Regulation", 385, "Local Regulation"
    LOFT_LAW = "Loft Law", 386, "Loft Law"
    LONGSHORE_AND_HARBOR_WORKERS_COMPENSATION_ACT = (
        "Longshore and Harbor Workers' Compensation Act",
        387,
        "Longshore and Harbor Workers' Compensation Act",
    )
    LOSS_OR_DESTRUCTION_OF_EVIDENCE = (
        "Loss or Destruction of Evidence",
        388,
        "Loss or Destruction of Evidence",
    )
    MAINTENANCE = "Maintenance", 389, "Maintenance"
    MAINTENANCE_OF_PREMISES = (
        "Maintenance of Premises",
        390,
        "Maintenance of Premises",
    )
    MALICIOUS_PROSECUTION = (
        "Malicious Prosecution",
        391,
        "Malicious Prosecution",
    )
    MALPRACTICE = "Malpractice", 392, "Malpractice"
    MALPRACTICE_INSURANCE = (
        "Malpractice Insurance",
        393,
        "Malpractice Insurance",
    )
    MANDAMUS = "Mandamus", 394, "Mandamus"
    MANSLAUGHTER = "Manslaughter", 395, "Manslaughter"
    MARITAL_RESIDENCE = "Marital Residence", 396, "Marital Residence"
    MARITIME_ACTION = "Maritime Action", 397, "Maritime Action"
    MARTIN_ACT = "Martin Act", 398, "Martin Act"
    MATERIAL_EXEMPT_FROM_DISCLOSURE = (
        "Material Exempt from Disclosure",
        399,
        "Material Exempt from Disclosure",
    )
    MATTERS_APPEALABLE = "Matters Appealable", 400, "Matters Appealable"
    MATTERS_ARBITRABLE = "Matters Arbitrable", 401, "Matters Arbitrable"
    MEASURE_OF_DAMAGES = "Measure of Damages", 402, "Measure of Damages"
    MECHANIC_S_LIEN = "Mechanic's Lien", 403, "Mechanic's Lien"
    MEDICAID_REIMBURSEMENT_PAYMENTS = (
        "Medicaid Reimbursement Payments",
        404,
        "Medicaid Reimbursement Payments",
    )
    MEDICAID_REIMBURSEMENT_RATES = (
        "Medicaid Reimbursement Rates",
        405,
        "Medicaid Reimbursement Rates",
    )
    MEDICAL_ASSISTANCE = "Medical Assistance", 406, "Medical Assistance"
    MEDICAL_MALPRACTICE = "Medical Malpractice", 407, "Medical Malpractice"
    MEDICAL_RECORDS_AND_REPORTS = (
        "Medical Records and Reports",
        408,
        "Medical Records and Reports",
    )
    MEDICAL_AND_SURGICAL_TREATMENT = (
        "Medical and Surgical Treatment",
        409,
        "Medical and Surgical Treatment",
    )
    MEDICARE_REIMBURSEMENT_PAYMENTS = (
        "Medicare Reimbursement Payments",
        410,
        "Medicare Reimbursement Payments",
    )
    MEETINGS = "Meetings", 411, "Meetings"
    MEMBERS_AND_MANAGERS = "Members and Managers", 412, "Members and Managers"
    MENTAL_ANGUISH = "Mental Anguish", 413, "Mental Anguish"
    MERGER = "Merger", 414, "Merger"
    MILK_CONTROL = "Milk Control", 415, "Milk Control"
    MINED_LAND_RECLAMATION_LAW = (
        "Mined Land Reclamation Law",
        416,
        "Mined Land Reclamation Law",
    )
    MISCONDUCT_BY_ATTORNEY = (
        "Misconduct by Attorney",
        417,
        "Misconduct by Attorney",
    )
    MISTAKE = "Mistake", 418, "Mistake"
    MISTRIAL = "Mistrial", 419, "Mistrial"
    MOBILE_HOME_PARKS = "Mobile Home Parks", 420, "Mobile Home Parks"
    MORTGAGE_RECORDING_TAX = (
        "Mortgage Recording Tax",
        421,
        "Mortgage Recording Tax",
    )
    MOTION_PROCEDURE = "Motion Procedure", 422, "Motion Procedure"
    MOTION_TO_DISMISS = "Motion to Dismiss", 423, "Motion to Dismiss"
    MURDER = "Murder", 424, "Murder"
    NECESSARY_PARTIES = "Necessary Parties", 425, "Necessary Parties"
    NEGLIGENCE = "Negligence", 426, "Negligence"
    NEGLIGENT_SUPERVISION = (
        "Negligent Supervision",
        427,
        "Negligent Supervision",
    )
    NEW_YORK_CITY_HUMAN_RIGHTS_LAW = (
        "New York City Human Rights Law",
        428,
        "New York City Human Rights Law",
    )
    NO_FAULT_AUTOMOBILE_INSURANCE = (
        "No-Fault Automobile Insurance",
        429,
        "No-Fault Automobile Insurance",
    )
    NOMINATING_PETITIONS = "Nominating Petitions", 430, "Nominating Petitions"
    NOTICE_OF_CLAIM = "Notice of Claim", 431, "Notice of Claim"
    NOTICE_OF_DEFICIENCY = "Notice of Deficiency", 432, "Notice of Deficiency"
    NOTICE_OF_INTENTION_TO_ARBITRATE = (
        "Notice of Intention to Arbitrate",
        433,
        "Notice of Intention to Arbitrate",
    )
    NOTICE_OF_STREET_DEFECT = (
        "Notice of Street Defect",
        434,
        "Notice of Street Defect",
    )
    NUISANCE = "Nuisance", 435, "Nuisance"
    NURSING_HOMES = "Nursing Homes", 436, "Nursing Homes"
    OBSTRUCTING_GOVERNMENTAL_ADMINISTRATION = (
        "Obstructing Governmental Administration",
        437,
        "Obstructing Governmental Administration",
    )
    OFFICIAL_MISCONDUCT = "Official Misconduct", 438, "Official Misconduct"
    OIL_SPILL_CLEANUP = "Oil Spill Cleanup", 439, "Oil Spill Cleanup"
    ONE_YEAR_STATUTE_OF_LIMITATIONS = (
        "One-Year Statute of Limitations",
        440,
        "One-Year Statute of Limitations",
    )
    OPERATING_VEHICLE_WHILE_UNDER_INFLUENCE_OF_ALCOHOL_OR_DRUGS = (
        "Operating Vehicle while Under Influence of Alcohol or Drugs",
        441,
        "Operating Vehicle while Under Influence of Alcohol or Drugs",
    )
    OPERATOR_S_LICENSE = "Operator's License", 442, "Operator's License"
    OPINIONS = "Opinions", 443, "Opinions"
    ORAL_MODIFICATION_OF_WRITTEN_AGREEMENT = (
        "Oral Modification of Written Agreement",
        444,
        "Oral Modification of Written Agreement",
    )
    ORDER_OF_PROTECTION = "Order of Protection", 445, "Order of Protection"
    ORDER_TO_SHOW_CAUSE = "Order to Show Cause", 446, "Order to Show Cause"
    OWNER_OF_VEHICLE = "Owner of Vehicle", 447, "Owner of Vehicle"
    OWNER_S_CONSENT_TO_USE_OF_VEHICLE = (
        "Owner's Consent to Use of Vehicle",
        448,
        "Owner's Consent to Use of Vehicle",
    )
    PAROL_EVIDENCE_RULE = "Parol Evidence Rule", 449, "Parol Evidence Rule"
    PART_PERFORMANCE = "Part Performance", 450, "Part Performance"
    PARTITION_OR_SALE = "Partition or Sale", 451, "Partition or Sale"
    PARTNERSHIP_AGREEMENT = (
        "Partnership Agreement",
        452,
        "Partnership Agreement",
    )
    PATERNITY_PROCEEDING = "Paternity Proceeding", 453, "Paternity Proceeding"
    PATIENT_IN_CUSTODY_OF_COMMISSIONER_OF_MENTAL_HEALTH = (
        "Patient in Custody of Commissioner of Mental Health",
        454,
        "Patient in Custody of Commissioner of Mental Health",
    )
    PENALTY_FOR_FAILURE_TO_DISCLOSE = (
        "Penalty for Failure to Disclose",
        455,
        "Penalty for Failure to Disclose",
    )
    PERJURY = "Perjury", 456, "Perjury"
    PERMITS = "Permits", 457, "Permits"
    PERSONAL_INCOME_TAX = "Personal Income Tax", 458, "Personal Income Tax"
    PERSONS_IN_NEED_OF_SUPERVISION = (
        "Persons in Need of Supervision",
        459,
        "Persons in Need of Supervision",
    )
    PETITION = "Petition", 460, "Petition"
    PLACE_OF_TRIAL = "Place of Trial", 461, "Place of Trial"
    PLANNING = "Planning", 462, "Planning"
    PLEA_BARGAINING = "Plea Bargaining", 463, "Plea Bargaining"
    PLEA_OF_GUILTY = "Plea of Guilty", 464, "Plea of Guilty"
    POLICE = "Police", 465, "Police"
    POLITICAL_PARTIES = "Political Parties", 466, "Political Parties"
    POOR_PERSONS = "Poor Persons", 467, "Poor Persons"
    POSSESSION_OF_FORGED_INSTRUMENT = (
        "Possession of Forged Instrument",
        468,
        "Possession of Forged Instrument",
    )
    POSSESSION_OF_STOLEN_PROPERTY = (
        "Possession of Stolen Property",
        469,
        "Possession of Stolen Property",
    )
    POSSESSION_OF_WEAPON = "Possession of Weapon", 470, "Possession of Weapon"
    POWER_OF_APPOINTMENT = "Power of Appointment", 471, "Power of Appointment"
    POWER_OF_ATTORNEY = "Power of Attorney", 472, "Power of Attorney"
    POWERS = "Powers", 473, "Powers"
    PRECLUSION_ORDER = "Preclusion Order", 474, "Preclusion Order"
    PREEMPTION_BY_STATE = "Preemption by State", 475, "Preemption by State"
    PREJUDGMENT_INTEREST = "Prejudgment Interest", 476, "Prejudgment Interest"
    PRELIMINARY_INJUNCTION = (
        "Preliminary Injunction",
        477,
        "Preliminary Injunction",
    )
    PRENUPTIAL_AGREEMENT = "Prenuptial Agreement", 478, "Prenuptial Agreement"
    PRESERVATION_OF_ISSUE_FOR_REVIEW = (
        "Preservation of Issue for Review",
        479,
        "Preservation of Issue for Review",
    )
    PREVAILING_RATE_OF_WAGES = (
        "Prevailing Rate of Wages",
        480,
        "Prevailing Rate of Wages",
    )
    PREVERDICT_INTEREST = "Preverdict Interest", 481, "Preverdict Interest"
    PRIMA_FACIE_TORT = "Prima Facie Tort", 482, "Prima Facie Tort"
    PRIMARY_ELECTIONS = "Primary Elections", 483, "Primary Elections"
    PRIORITY = "Priority", 484, "Priority"
    PRIVILEGE = "Privilege", 485, "Privilege"
    PRIVILEGES_AND_IMMUNITIES_CLAUSE = (
        "Privileges and Immunities Clause",
        486,
        "Privileges and Immunities Clause",
    )
    PROBATE = "Probate", 487, "Probate"
    PROCUREMENT = "Procurement", 488, "Procurement"
    PROHIBITION = "Prohibition", 489, "Prohibition"
    PROMISSORY_ESTOPPEL = "Promissory Estoppel", 490, "Promissory Estoppel"
    PROMOTING_OBSCENE_SEXUAL_PERFORMANCE_BY_CHILD = (
        "Promoting Obscene Sexual Performance by Child",
        491,
        "Promoting Obscene Sexual Performance by Child",
    )
    PROOF_OF_OTHER_CRIMES = (
        "Proof of Other Crimes",
        492,
        "Proof of Other Crimes",
    )
    PROOF_OF_PRIOR_CONVICTIONS = (
        "Proof of Prior Convictions",
        493,
        "Proof of Prior Convictions",
    )
    PROPER_FORUM = "Proper Forum", 494, "Proper Forum"
    PROPER_PARTIES = "Proper Parties", 495, "Proper Parties"
    PROPERTY_INSURANCE = "Property Insurance", 496, "Property Insurance"
    PROPRIETARY_LEASE = "Proprietary Lease", 497, "Proprietary Lease"
    PROTECTIVE_ORDER = "Protective Order", 498, "Protective Order"
    PROXIMATE_CAUSE = "Proximate Cause", 499, "Proximate Cause"
    PUBLIC_ASSISTANCE = "Public Assistance", 500, "Public Assistance"
    PUBLIC_EMPLOYEES_FAIR_EMPLOYMENT_ACT = (
        "Public Employees' Fair Employment Act",
        501,
        "Public Employees' Fair Employment Act",
    )
    PUBLIC_EMPLOYMENT_RELATIONS_BOARD = (
        "Public Employment Relations Board",
        502,
        "Public Employment Relations Board",
    )
    PUBLIC_FIGURE = "Public Figure", 503, "Public Figure"
    PUBLIC_RIGHT_OF_USE = "Public Right of Use", 504, "Public Right of Use"
    PUBLIC_SERVICE_COMMISSION = (
        "Public Service Commission",
        505,
        "Public Service Commission",
    )
    PUBLIC_TRUST_DOCTRINE = (
        "Public Trust Doctrine",
        506,
        "Public Trust Doctrine",
    )
    PUBLIC_USE = "Public Use", 507, "Public Use"
    PUBLIC_WORKS_CONTRACTS = (
        "Public Works Contracts",
        508,
        "Public Works Contracts",
    )
    PUNITIVE_DAMAGES = "Punitive Damages", 509, "Punitive Damages"
    QUANTUM_MERUIT = "Quantum Meruit", 510, "Quantum Meruit"
    RAPE = "Rape", 511, "Rape"
    RATE_MAKING = "Rate Making", 512, "Rate Making"
    REAL_ESTATE_BROKERS = "Real Estate Brokers", 513, "Real Estate Brokers"
    REAL_PROPERTY_TAX = "Real Property Tax", 514, "Real Property Tax"
    REAL_PROPERTY_TRANSFER_GAINS_TAX = (
        "Real Property Transfer Gains Tax",
        515,
        "Real Property Transfer Gains Tax",
    )
    REARGUMENT_OR_RENEWAL = (
        "Reargument or Renewal",
        516,
        "Reargument or Renewal",
    )
    RECKLESS_ENDANGERMENT = (
        "Reckless Endangerment",
        517,
        "Reckless Endangerment",
    )
    RECOGNIZANCE = "Recognizance", 518, "Recognizance"
    RECOUPMENT_OF_OVERPAYMENTS = (
        "Recoupment of Overpayments",
        519,
        "Recoupment of Overpayments",
    )
    RECUSAL = "Recusal", 520, "Recusal"
    REDISTRICTING_PLAN = "Redistricting Plan", 521, "Redistricting Plan"
    REGISTER_OF_CHILD_ABUSE_AND_MALTREATMENT = (
        "Register of Child Abuse and Maltreatment",
        522,
        "Register of Child Abuse and Maltreatment",
    )
    REGULATION_OF_BILLBOARDS = (
        "Regulation of Billboards",
        523,
        "Regulation of Billboards",
    )
    REGULATION_OF_TAXICAB_BUSINESS = (
        "Regulation of Taxicab Business",
        524,
        "Regulation of Taxicab Business",
    )
    REINSTATEMENT = "Reinstatement", 525, "Reinstatement"
    REINSURANCE = "Reinsurance", 526, "Reinsurance"
    RELIANCE = "Reliance", 527, "Reliance"
    RELIEF_FROM_JUDGMENT = "Relief from Judgment", 528, "Relief from Judgment"
    REMOVAL_FROM_OFFICE = "Removal from Office", 529, "Removal from Office"
    REMOVAL_OF_GUARDIAN = "Removal of Guardian", 530, "Removal of Guardian"
    RENT = "Rent", 531, "Rent"
    RENT_REGULATION = "Rent Regulation", 532, "Rent Regulation"
    RENT_SUBSIDY = "Rent Subsidy", 533, "Rent Subsidy"
    RENTAL_CARS = "Rental Cars", 534, "Rental Cars"
    REOPENING_CASE = "Reopening Case", 535, "Reopening Case"
    RES_IPSA_LOQUITUR = "Res Ipsa Loquitur", 536, "Res Ipsa Loquitur"
    RES_JUDICATA = "Res Judicata", 537, "Res Judicata"
    RESISTING_ARREST = "Resisting Arrest", 538, "Resisting Arrest"
    RESPONDEAT_SUPERIOR = "Respondeat Superior", 539, "Respondeat Superior"
    RESTRICTIVE_COVENANT_IN_EMPLOYMENT_CONTRACT = (
        "Restrictive Covenant in Employment Contract",
        540,
        "Restrictive Covenant in Employment Contract",
    )
    RESTRICTIVE_COVENANTS = (
        "Restrictive Covenants",
        541,
        "Restrictive Covenants",
    )
    RESUBMISSION_OF_CHARGES = (
        "Resubmission of Charges",
        542,
        "Resubmission of Charges",
    )
    RETIREMENT_AND_PENSION_BENEFITS = (
        "Retirement and Pension Benefits",
        543,
        "Retirement and Pension Benefits",
    )
    RETROACTIVE_APPLICATION_OF_STATUTE = (
        "Retroactive Application of Statute",
        544,
        "Retroactive Application of Statute",
    )
    REVIVAL_OF_TIME_BARRED_CLAIMS = (
        "Revival of Time-Barred Claims",
        545,
        "Revival of Time-Barred Claims",
    )
    REVOCATION = "Revocation", 546, "Revocation"
    REVOCATION_OR_SUSPENSION_OF_LICENSE = (
        "Revocation or Suspension of License",
        547,
        "Revocation or Suspension of License",
    )
    REVOCATION_OR_SUSPENSION_OF_OPERATOR_S_LICENSE = (
        "Revocation or Suspension of Operator's License",
        548,
        "Revocation or Suspension of Operator's License",
    )
    RIGHT_OF_CONFRONTATION = (
        "Right of Confrontation",
        549,
        "Right of Confrontation",
    )
    RIGHT_OF_PRIVACY = "Right of Privacy", 550, "Right of Privacy"
    RIGHT_OF_SEPULCHER = "Right of Sepulcher", 551, "Right of Sepulcher"
    RIGHT_OF_SUBROGATION = "Right of Subrogation", 552, "Right of Subrogation"
    RIGHT_TO_APPEAR_BEFORE_GRAND_JURY = (
        "Right to Appear before Grand Jury",
        553,
        "Right to Appear before Grand Jury",
    )
    RIGHT_TO_BAIL = "Right to Bail", 554, "Right to Bail"
    RIGHT_TO_BEAR_ARMS = "Right to Bear Arms", 555, "Right to Bear Arms"
    RIGHT_TO_COUNSEL = "Right to Counsel", 556, "Right to Counsel"
    RIGHT_TO_JURY_TRIAL = "Right to Jury Trial", 557, "Right to Jury Trial"
    RIGHT_TO_PUBLIC_TRIAL = (
        "Right to Public Trial",
        558,
        "Right to Public Trial",
    )
    RIGHT_TO_REMAIN_SILENT = (
        "Right to Remain Silent",
        559,
        "Right to Remain Silent",
    )
    RIGHT_TO_REPRESENTATION_PRO_SE = (
        "Right to Representation Pro Se",
        560,
        "Right to Representation Pro Se",
    )
    RIGHT_TO_SPEEDY_TRIAL = (
        "Right to Speedy Trial",
        561,
        "Right to Speedy Trial",
    )
    RIGHT_TO_BE_PRESENT_AT_TRIAL = (
        "Right to be Present at Trial",
        562,
        "Right to be Present at Trial",
    )
    RIPENESS_DOCTRINE = "Ripeness Doctrine", 563, "Ripeness Doctrine"
    ROAMING_ON_HIGHWAY = "Roaming on Highway", 564, "Roaming on Highway"
    ROBBERY = "Robbery", 565, "Robbery"
    RULE_MAKING = "Rule Making", 566, "Rule Making"
    SAFE_PLACE_TO_WORK = "Safe Place to Work", 567, "Safe Place to Work"
    SALES_AND_USE_TAXES = "Sales and Use Taxes", 568, "Sales and Use Taxes"
    SCIENTIFIC_EVIDENCE = "Scientific Evidence", 569, "Scientific Evidence"
    SCOPE_OF_DISCLOSURE = "Scope of Disclosure", 570, "Scope of Disclosure"
    SCOPE_OF_GUARANTEE = "Scope of Guarantee", 571, "Scope of Guarantee"
    SCOPE_OF_RELEASE = "Scope of Release", 572, "Scope of Release"
    SCOPE_OF_REMEDY = "Scope of Remedy", 573, "Scope of Remedy"
    SEALING_OF_RECORDS = "Sealing of Records", 574, "Sealing of Records"
    SEARCH_WARRANT = "Search Warrant", 575, "Search Warrant"
    SECURITY_AGREEMENTS = "Security Agreements", 576, "Security Agreements"
    SELECTION_OF_JURY = "Selection of Jury", 577, "Selection of Jury"
    SELECTIVE_PROSECUTION = (
        "Selective Prosecution",
        578,
        "Selective Prosecution",
    )
    SENTENCE = "Sentence", 579, "Sentence"
    SEPARATION_OF_POWERS = "Separation of Powers", 580, "Separation of Powers"
    SERVICE_OF_PROCESS = "Service of Process", 581, "Service of Process"
    SETTLEMENT_AGREEMENT = "Settlement Agreement", 582, "Settlement Agreement"
    SEX_OFFENDERS = "Sex Offenders", 583, "Sex Offenders"
    SEXUAL_ABUSE = "Sexual Abuse", 584, "Sexual Abuse"
    SHAREHOLDERS_DERIVATIVE_ACTION = (
        "Shareholders' Derivative Action",
        585,
        "Shareholders' Derivative Action",
    )
    SHIELD_LAW = "Shield Law", 586, "Shield Law"
    SIDEWALKS = "Sidewalks", 587, "Sidewalks"
    SIX_YEAR_STATUTE_OF_LIMITATIONS = (
        "Six-Year Statute of Limitations",
        588,
        "Six-Year Statute of Limitations",
    )
    SLANDER_PER_SE = "Slander Per Se", 589, "Slander Per Se"
    SMALL_CLAIMS = "Small Claims", 590, "Small Claims"
    SNOW_AND_ICE = "Snow and Ice", 591, "Snow and Ice"
    SODOMY = "Sodomy", 592, "Sodomy"
    SOVEREIGN_IMMUNITY = "Sovereign Immunity", 593, "Sovereign Immunity"
    SOVEREIGN_IMMUNITY_OF_TRIBE = (
        "Sovereign Immunity of Tribe",
        594,
        "Sovereign Immunity of Tribe",
    )
    SPECIAL_CONDITIONS = "Special Conditions", 595, "Special Conditions"
    SPECIAL_FUNDS = "Special Funds", 596, "Special Funds"
    SPECIAL_PROSECUTOR = "Special Prosecutor", 597, "Special Prosecutor"
    STALKING = "Stalking", 598, "Stalking"
    STANDING = "Standing", 599, "Standing"
    STATE_AID_TO_SCHOOL_DISTRICTS = (
        "State Aid to School Districts",
        600,
        "State Aid to School Districts",
    )
    STATE_CONSTITUTIONAL_LAW = (
        "State Constitutional Law",
        601,
        "State Constitutional Law",
    )
    STATE_DIVISION_OF_HUMAN_RIGHTS = (
        "State Division of Human Rights",
        602,
        "State Division of Human Rights",
    )
    STAY = "Stay", 603, "Stay"
    STAY_OF_ACTION = "Stay of Action", 604, "Stay of Action"
    STAY_OF_ARBITRATION = "Stay of Arbitration", 605, "Stay of Arbitration"
    STIPULATION_IN_OPEN_COURT = (
        "Stipulation in Open Court",
        606,
        "Stipulation in Open Court",
    )
    STIPULATION_OF_SETTLEMENT = (
        "Stipulation of Settlement",
        607,
        "Stipulation of Settlement",
    )
    STRICT_LIABILITY = "Strict Liability", 608, "Strict Liability"
    STUDENTS = "Students", 609, "Students"
    SUBPOENA = "Subpoena", 610, "Subpoena"
    SUBROGATION_RIGHTS_OF_INSURER = (
        "Subrogation Rights of Insurer",
        611,
        "Subrogation Rights of Insurer",
    )
    SUCCESSION_RIGHTS = "Succession Rights", 612, "Succession Rights"
    SUFFICIENCY_OF_MEMORANDUM = (
        "Sufficiency of Memorandum",
        613,
        "Sufficiency of Memorandum",
    )
    SUFFICIENCY_OF_PLEADING = (
        "Sufficiency of Pleading",
        614,
        "Sufficiency of Pleading",
    )
    SUMMARY_JUDGMENT = "Summary Judgment", 615, "Summary Judgment"
    SUPPLEMENTARY_PROCEEDINGS = (
        "Supplementary Proceedings",
        616,
        "Supplementary Proceedings",
    )
    SUPPORT = "Support", 617, "Support"
    SUPPRESSION_HEARING = "Suppression Hearing", 618, "Suppression Hearing"
    SUPREMACY_CLAUSE = "Supremacy Clause", 619, "Supremacy Clause"
    SURROGATE_S_COURT = "Surrogate's Court", 620, "Surrogate's Court"
    SUSTAINING_LIFE_OF_PERSON_IN_PERMANENT_VEGETATIVE_STATE = (
        "Sustaining Life of Person in Permanent Vegetative State",
        621,
        "Sustaining Life of Person in Permanent Vegetative State",
    )
    TAKING_OF_PROPERTY = "Taking of Property", 622, "Taking of Property"
    TAMPERING_WITH_WITNESS = (
        "Tampering with Witness",
        623,
        "Tampering with Witness",
    )
    TAX_LIENS_TAX_SALES_AND_TAX_TITLES = (
        "Tax Liens, Tax Sales and Tax Titles",
        624,
        "Tax Liens, Tax Sales and Tax Titles",
    )
    TAX_ON_CIGARETTES_AND_TOBACCO_PRODUCTS = (
        "Tax on Cigarettes and Tobacco Products",
        625,
        "Tax on Cigarettes and Tobacco Products",
    )
    TAXPAYER_S_ACTION = "Taxpayer's Action", 626, "Taxpayer's Action"
    TEACHERS = "Teachers", 627, "Teachers"
    TEMPORARY_RESTRAINING_ORDER = (
        "Temporary Restraining Order",
        628,
        "Temporary Restraining Order",
    )
    TENANTS_IN_COMMON = "Tenants in Common", 629, "Tenants in Common"
    TERMINATION_OF_EMPLOYMENT = (
        "Termination of Employment",
        630,
        "Termination of Employment",
    )
    TERMINATION_OF_PARENTAL_RIGHTS = (
        "Termination of Parental Rights",
        631,
        "Termination of Parental Rights",
    )
    THIRD_PARTY_ACTION = "Third-Party Action", 632, "Third-Party Action"
    TIMELINESS = "Timeliness", 633, "Timeliness"
    TIMELINESS_OF_PROSECUTION = (
        "Timeliness of Prosecution",
        634,
        "Timeliness of Prosecution",
    )
    TOLLING = "Tolling", 635, "Tolling"
    TORT_LIABILITY = "Tort Liability", 636, "Tort Liability"
    TOXIC_TORTS = "Toxic Torts", 637, "Toxic Torts"
    TRADEMARK_COUNTERFEITING = (
        "Trademark Counterfeiting",
        638,
        "Trademark Counterfeiting",
    )
    TRAFFIC_INFRACTIONS = "Traffic Infractions", 639, "Traffic Infractions"
    TRANSFER_OF_STOCK = "Transfer of Stock", 640, "Transfer of Stock"
    TRANSFER_TO_OTHER_COURT = (
        "Transfer to Other Court",
        641,
        "Transfer to Other Court",
    )
    TRANSPORTATION_OF_PUPILS = (
        "Transportation of Pupils",
        642,
        "Transportation of Pupils",
    )
    TREATMENT_AND_CARE_OF_INJURED_EMPLOYEES = (
        "Treatment and Care of Injured Employees",
        643,
        "Treatment and Care of Injured Employees",
    )
    TRESPASSING = "Trespassing", 644, "Trespassing"
    TRIAL = "Trial", 645, "Trial"
    TUITION_FOR_NONRESIDENTS = (
        "Tuition for Nonresidents",
        646,
        "Tuition for Nonresidents",
    )
    UNAUTHORIZED_PRACTICE_OF_LAW = (
        "Unauthorized Practice of Law",
        647,
        "Unauthorized Practice of Law",
    )
    UNINCORPORATED_BUSINESS_INCOME_TAX = (
        "Unincorporated Business Income Tax",
        648,
        "Unincorporated Business Income Tax",
    )
    UNJUST_CONVICTION_AND_IMPRISONMENT_ACT = (
        "Unjust Conviction and Imprisonment Act",
        649,
        "Unjust Conviction and Imprisonment Act",
    )
    UNJUST_ENRICHMENT = "Unjust Enrichment", 650, "Unjust Enrichment"
    UNLAWFUL_ASSEMBLY = "Unlawful Assembly", 651, "Unlawful Assembly"
    UNLAWFUL_SEARCH_AND_SEIZURE = (
        "Unlawful Search and Seizure",
        652,
        "Unlawful Search and Seizure",
    )
    UNLAWFULLY_DEALING_WITH_CHILD = (
        "Unlawfully Dealing with Child",
        653,
        "Unlawfully Dealing with Child",
    )
    UNLICENSED_GENERAL_VENDING = (
        "Unlicensed General Vending",
        654,
        "Unlicensed General Vending",
    )
    UNSAFE_BUILDINGS = "Unsafe Buildings", 655, "Unsafe Buildings"
    USE_AND_OCCUPANCY = "Use and Occupancy", 656, "Use and Occupancy"
    VACATUR_OF_JUDGMENT = "Vacatur of Judgment", 657, "Vacatur of Judgment"
    VACATUR_OF_JUDGMENT_OF_CONVICTION = (
        "Vacatur of Judgment of Conviction",
        658,
        "Vacatur of Judgment of Conviction",
    )
    VACATUR_OF_ORDER = "Vacatur of Order", 659, "Vacatur of Order"
    VALIDITY = "Validity", 660, "Validity"
    VALIDITY_OF_ORDINANCE = (
        "Validity of Ordinance",
        661,
        "Validity of Ordinance",
    )
    VALIDITY_OF_REGULATION = (
        "Validity of Regulation",
        662,
        "Validity of Regulation",
    )
    VALIDITY_OF_STATUTE = "Validity of Statute", 663, "Validity of Statute"
    VALUATION = "Valuation", 664, "Valuation"
    VERDICT = "Verdict", 665, "Verdict"
    VEXATIOUS_PRO_SE_LITIGATION = (
        "Vexatious Pro Se Litigation",
        666,
        "Vexatious Pro Se Litigation",
    )
    VIOLATION_OF_MUNICIPAL_CODE = (
        "Violation of Municipal Code",
        667,
        "Violation of Municipal Code",
    )
    VIOLATION_OF_STATUTORY_DUTY = (
        "Violation of Statutory Duty",
        668,
        "Violation of Statutory Duty",
    )
    VISITATION = "Visitation", 669, "Visitation"
    VISITATION_RIGHTS_OF_GRANDPARENTS = (
        "Visitation Rights of Grandparents",
        670,
        "Visitation Rights of Grandparents",
    )
    VOLUNTARY_WITHDRAWAL_FROM_LABOR_MARKET = (
        "Voluntary Withdrawal from Labor Market",
        671,
        "Voluntary Withdrawal from Labor Market",
    )
    WAGES = "Wages", 672, "Wages"
    WAIVER = "Waiver", 673, "Waiver"
    WAIVER_OF_RIGHT_TO_APPEAL = (
        "Waiver of Right to Appeal",
        674,
        "Waiver of Right to Appeal",
    )
    WANT_OF_PROSECUTION = "Want of Prosecution", 675, "Want of Prosecution"
    WATER_SUPPLY = "Water Supply", 676, "Water Supply"
    WATER_AND_SEWER_RATES = (
        "Water and Sewer Rates",
        677,
        "Water and Sewer Rates",
    )
    WHAT_CONSTITUTES = "What Constitutes", 678, "What Constitutes"
    WHAT_LAW_GOVERNS = "What Law Governs", 679, "What Law Governs"
    WHAT_STATUTE_GOVERNS = "What Statute Governs", 680, "What Statute Governs"
    WHEN_CAUSE_OF_ACTION_ACCRUES = (
        "When Cause of Action Accrues",
        681,
        "When Cause of Action Accrues",
    )
    WHEN_CLAIM_FOR_INDEMNIFICATION_AVAILABLE = (
        "When Claim for Indemnification Available",
        682,
        "When Claim for Indemnification Available",
    )
    WHEN_REMEDY_APPROPRIATE = (
        "When Remedy Appropriate",
        683,
        "When Remedy Appropriate",
    )
    WHEN_REMEDY_AVAILABLE = (
        "When Remedy Available",
        684,
        "When Remedy Available",
    )
    WHISTLEBLOWER_LAW = "Whistleblower Law", 685, "Whistleblower Law"
    WITNESSES = "Witnesses", 686, "Witnesses"
    WRONGFUL_DISCHARGE = "Wrongful Discharge", 687, "Wrongful Discharge"
    YOUTHFUL_OFFENDERS = "Youthful Offenders", 688, "Youthful Offenders"
    ZONING = "Zoning", 689, "Zoning"


#: Display form per document type, used to compose a filing type for documents
#: the FILINGS table never listed. Phrased to read like the Court's own
#: vocabulary so real and reconstructed entries display together.
DOCTYPE_LABELS: dict[FilingDocType, str] = {
    doctype: doctype.label for doctype in FilingDocType
}

#: Display form of each role.
ROLE_LABELS: dict[FilingRole, str] = {role: role.label for role in FilingRole}

#: Document types the court produces rather than a party filing. These never
#: correspond to a FILINGS row.
COURT_GENERATED_DOCTYPES: frozenset[FilingDocType] = frozenset(
    {
        FilingDocType.DECISION,
        FilingDocType.ORAL_ARGUMENT_TRANSCRIPT,
        FilingDocType.ORAL_ARGUMENT_WEBCAST,
    }
)

#: Document types the FILINGS table never enumerates. A *filed* document of one
#: of these types having no FILINGS row is expected, not a failed match -- so a
#: reconstructed entry whose document type is in this set is normal, while one
#: outside it means the table omitted something it usually lists.
NOT_ON_FILINGS_TABLE: frozenset[FilingDocType] = frozenset(
    {
        FilingDocType.MOTION,
        FilingDocType.OPPOSITION,
        FilingDocType.MOTION_FOR_LEAVE_TO_APPEAL,
        FilingDocType.OPPOSITION_TO_MOTION_FOR_LEAVE_TO_APPEAL,
        FilingDocType.COMPENDIUM,
        FilingDocType.ADDENDUM,
        FilingDocType.EXHIBITS,
        FilingDocType.SSM_REPLY_LETTER,
        FilingDocType.SUPPLEMENTAL_APPENDIX,
        FilingDocType.AD_BRIEF,
        FilingDocType.AD_RECORD,
        FilingDocType.AD_APPENDIX,
        FilingDocType.AD_REPLY_BRIEF,
        # Every doctype the Court does not itself publish belongs here by
        # construction: no FILINGS filing type maps to one, so a file of this
        # type can never have a row to be missing from.
        FilingDocType.PRE_SENTENCE_REPORT,
        FilingDocType.AD_ORDER,
        FilingDocType.AD_MOTION,
        FilingDocType.AFFIDAVIT_OF_SERVICE,
        FilingDocType.JURISDICTIONAL_RESPONSE,
        FilingDocType.APPELLATE_TERM_BRIEF,
        FilingDocType.POST_ARGUMENT_BRIEF,
        FilingDocType.HEARING_TRANSCRIPT,
    }
)

# --------------------------------------------------------------------------
# Lookups and issue classification
# --------------------------------------------------------------------------

_FILING_TYPES_BY_VALUE: dict[str, FilingType] = {
    filing_type.value: filing_type for filing_type in FilingType
}
_ISSUE_CATEGORIES_BY_VALUE: dict[str, IssueCategory] = {
    category.value: category for category in IssueCategory
}
_ISSUE_SUBCATEGORIES_BY_VALUE: dict[str, IssueSubcategory] = {
    subcategory.value: subcategory for subcategory in IssueSubcategory
}


def filing_type_from_value(raw: str | None) -> FilingType | None:
    """Read a FILINGS-table filing type.

    :param raw: The string the table printed. Whitespace is collapsed, since
        the table is inconsistent about it.
    :return: The matching :class:`FilingType`, or ``None`` when the table
        printed nothing or printed a type this vocabulary does not cover.
    """
    if not raw:
        return None
    return _FILING_TYPES_BY_VALUE.get(" ".join(raw.split()))


@dataclass(frozen=True)
class IssueClassification:
    """The reading of one issue string from a case-details page.

    :ivar raw: The issue exactly as Court-PASS stated it.
    :ivar category: The category, or ``None`` when this vocabulary does not
        cover what the Court stated.
    :ivar subcategory: The subcategory, ``None`` when the Court stated a bare
        category, and also ``None`` when the vocabulary does not cover it.
    :ivar recognized: Whether every part the Court stated was covered. ``False``
        is the signal that the Court has added a category or subcategory.
    """

    raw: str
    category: IssueCategory | None = None
    subcategory: IssueSubcategory | None = None
    recognized: bool = False


def classify_issue(raw: str) -> IssueClassification:
    """Read an issue string as ``(category, subcategory)``.

    The Court writes an issue as a category and a subcategory joined by a double
    dash -- ``Judgments--Confession of Judgment`` -- and never nests further
    than that. It states roughly 13% of issues as a bare category.

    :param raw: The issue as Court-PASS stated it.
    :return: The classification, always carrying ``raw`` so an unrecognized
        value is never lost.
    """
    category_part, _, subcategory_part = raw.partition("--")
    category = _ISSUE_CATEGORIES_BY_VALUE.get(category_part.strip())
    if not subcategory_part.strip():
        return IssueClassification(
            raw=raw, category=category, recognized=category is not None
        )
    subcategory = _ISSUE_SUBCATEGORIES_BY_VALUE.get(subcategory_part.strip())
    return IssueClassification(
        raw=raw,
        category=category,
        subcategory=subcategory,
        recognized=category is not None and subcategory is not None,
    )
