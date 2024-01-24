citation_types = {
    "FEDERAL": 1,
    "STATE": 2,
    "STATE_REGIONAL": 3,
    "SPECIALTY": 4,
    "SCOTUS_EARLY": 5,
    "LEXIS": 6,
    "WEST": 7,
    "NEUTRAL": 8,
}


class OpinionType:
    COMBINED = "010combined"
    UNANIMOUS = "015unamimous"
    LEAD = "020lead"
    PLURALITY = "025plurality"
    CONCURRENCE = "030concurrence"
    CONCUR_IN_PART = "035concurrenceinpart"
    DISSENT = "040dissent"
    ADDENDUM = "050addendum"
    REMITTUR = "060remittitur"
    REHEARING = "070rehearing"
    ON_THE_MERITS = "080onthemerits"
    ON_MOTION_TO_STRIKE = "090onmotiontostrike"
