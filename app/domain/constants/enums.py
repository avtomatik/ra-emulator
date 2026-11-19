from enum import Enum, StrEnum


class Gender(Enum):
    FEMALE = "FEMALE"
    MALE = "MALE"


class RevocationRequestStatus(StrEnum):
    COMPLETED = "Completed"


class RevocationReason(StrEnum):
    KEY_COMPROMISE = "KeyCompromise"
