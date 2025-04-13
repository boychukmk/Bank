from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, validator


class UserCSV(BaseModel):
    id: int
    login: str
    registration_date: date


class CreditCSV(BaseModel):
    id: int
    user_id: int
    issuance_date: date
    return_date: date
    actual_return_date: Optional[date]
    body: float
    percent: float


class DictionaryCSV(BaseModel):
    id: int
    name: str


class PlanCSV(BaseModel):
    id: int
    period: date
    sum: Decimal = Field(..., gt=0)
    category_id: int

    @validator("period")
    def must_be_first_day(cls, v: date):
        if v.day != 1:
            raise ValueError("Period must be the first day of the month")
        return v


class PaymentCSV(BaseModel):
    id: int
    sum: Decimal = Field(..., gt=0)
    payment_date: date
    credit_id: int
    type_id: int
