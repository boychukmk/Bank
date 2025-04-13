from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class UserBase(BaseModel):
    login: str
    registration_date: date


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    id: int


class CreditBase(BaseModel):
    user_id: int
    issuance_date: date
    return_date: date
    actual_return_date: date | None
    body: Decimal
    percent: Decimal


class CreditCreate(CreditBase):
    pass


class CreditRead(CreditBase):
    id: int


class DictionaryBase(BaseModel):
    name: str


class DictionaryCreate(DictionaryBase):
    pass


class DictionaryRead(DictionaryBase):
    id: int


class PlanBase(BaseModel):
    period: date
    sum: Decimal
    category_id: int


class PlanCreate(PlanBase):
    pass


class PlanRead(PlanBase):
    id: int


class PaymentBase(BaseModel):
    sum: Decimal
    payment_date: date
    credit_id: int
    type_id: int


class PaymentCreate(PaymentBase):
    pass


class PaymentRead(PaymentBase):
    id: int
