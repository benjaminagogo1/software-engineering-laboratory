from enum import Enum


class UpdateResult(Enum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    INVALID_AMOUNT = "invalid_amount"


class AddResult(Enum):
    SUCCESS = "success"
    INVALID_NAME = "invalid_name"
    INVALID_AMOUNT = "invalid_amount"