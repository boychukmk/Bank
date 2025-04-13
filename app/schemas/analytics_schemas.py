from pydantic import BaseModel
from datetime import date
from typing import Optional


class UserCreditInfo(BaseModel):
    issuance_date: date
    is_closed: bool
    return_date: Optional[date]
    body: Optional[float]
    percent: Optional[float]
    total_payments: Optional[float]
    deadline: Optional[date]
    overdue_days: Optional[int]
    body_paid: Optional[float]
    percent_paid: Optional[float]


class PlansPerformanceOut(BaseModel):
    month: date
    category: str
    plan_sum: float
    actual_sum: float
    performance_percent: float


class YearPerformanceOut(BaseModel):
    month: str
    year: int
    issue_count: int
    plan_issue_sum: float
    actual_issue_sum: float
    issue_performance_percent: float
    payment_count: int
    plan_payment_sum: float
    actual_payment_sum: float
    payment_performance_percent: float
    issue_share: float
    payment_share: float
