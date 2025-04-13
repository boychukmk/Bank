from datetime import date
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import ForeignKey, Numeric, String, Float, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(String(50), unique=True)
    registration_date: Mapped[date] = mapped_column(Date)

    credits: Mapped[List["Credit"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Credit(Base):
    __tablename__ = "credits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    issuance_date: Mapped[date] = mapped_column(Date)
    return_date: Mapped[date] = mapped_column(Date)
    actual_return_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    body: Mapped[float] = mapped_column(Float)
    percent: Mapped[float] = mapped_column(Float)

    user: Mapped["User"] = relationship(back_populates="credits")
    payments: Mapped[List["Payment"]] = relationship(back_populates="credit", cascade="all, delete-orphan")


class Dictionary(Base):
    __tablename__ = "dictionary"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    period: Mapped[date] = mapped_column(Date)
    sum: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    category_id: Mapped[int] = mapped_column(ForeignKey("dictionary.id"))

    category: Mapped["Dictionary"] = relationship()


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sum: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    payment_date: Mapped[date] = mapped_column(Date)
    credit_id: Mapped[int] = mapped_column(ForeignKey("credits.id", ondelete="CASCADE"))
    type_id: Mapped[int] = mapped_column(ForeignKey("dictionary.id"))

    credit: Mapped["Credit"] = relationship(back_populates="payments")
    type: Mapped["Dictionary"] = relationship()
