from enum import Enum


class UpdateResult(Enum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    INVALID_NAME = "invalid_name"
    INVALID_AMOUNT = "invalid_amount"
    INVALID_CATEGORY = "invalid_category"
    INVALID_PAYMENT_TYPE = "invalid_payment_type"


class AddResult(Enum):
    SUCCESS = "success"
    INVALID_NAME = "invalid_name"
    INVALID_AMOUNT = "invalid_amount"
    INVALID_CATEGORY = "invalid_category"
    INVALID_PAYMENT_TYPE = "invalid_payment_type"



class DeleteResult(Enum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
