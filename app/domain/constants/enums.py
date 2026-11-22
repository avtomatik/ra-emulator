from enum import Enum, StrEnum


class Gender(Enum):
    FEMALE = "FEMALE"
    MALE = "MALE"


class RevocationRequestStatus(StrEnum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    REJECTED = "Rejected"


class RevocationReason(StrEnum):
    KEY_COMPROMISE = "KeyCompromise"
