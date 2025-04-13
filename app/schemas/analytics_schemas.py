from pydantic import BaseModel
from datetime import date
from typing import Union


class BaseCreditInfo(BaseModel):
    issuance_date: date
    is_closed: bool


class ClosedCreditInfo(BaseCreditInfo):
    is_closed: bool = True
    return_date: date
    body: float
    percent: float
    total_payments: float


class OpenCreditInfo(BaseCreditInfo):
    is_closed: bool = False
    return_date: date
    overdue_days: int
    body: float
    percent: float
    body_payments: float
    percent_payments: float


UserCreditInfo = Union[ClosedCreditInfo, OpenCreditInfo]


class PlansPerformanceOut(BaseModel):
    month: date
    category: str
    plan_sum: float
    actual_sum: float
    performance_percent: float


class YearPerformanceOut(BaseModel):
    month: str
    credit_count: int
    plan_credit_sum: float
    actual_credit_sum: float
    credit_performance_percent: float
    payment_count: int
    plan_payment_sum: float
    actual_payment_sum: float
    payment_performance_percent: float
    credit_share_percent_of_year: float
    payment_share_percent_of_year: float
