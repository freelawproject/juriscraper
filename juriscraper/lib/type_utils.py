from enum import Enum


class OpinionType(Enum):
    UNANIMOUS = "015unamimous"
    MAJORITY = "020lead"
    PLURALITY = "025plurality"
    CONCURRENCE = "030concurrence"
    CONCURRING_IN_PART_AND_DISSENTING_IN_PART = "035concurrenceinpart"
    DISSENT = "040dissent"
    REMITTITUR = "060remittitur"
    REHEARING = "070rehearing"
    ON_THE_MERITS = "080onthemerits"
    ON_MOTION_TO_STRIKE_COST_BILL = "090onmotiontostrike"
