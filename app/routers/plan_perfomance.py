from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, case, extract
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from typing import List

from app.core.database import get_db
from app.models import Plan, Dictionary, Credit, Payment
from app.schemas.analytics_schemas import PlansPerformanceOut, YearPerformanceOut

router = APIRouter()


@router.get("/month_performance", response_model=List[PlansPerformanceOut])
async def get_plans_performance(
        target_date: date = Query(...),
        db: AsyncSession = Depends(get_db)
) -> List[PlansPerformanceOut]:
    start_of_month = date(target_date.year, target_date.month, 1)

    payment_sum_case = func.sum(
        case(
            (Dictionary.name == "збір", Payment.sum),
            else_=0
        )
    )

    credit_sum_case = func.sum(
        case(
            (Dictionary.name == "видача", Credit.body),
            else_=0
        )
    )

    stmt = (
        select(
            Plan.period,
            Dictionary.name.label("category"),
            Plan.sum.label("plan_sum"),
            payment_sum_case.label("actual_sum_payment"),
            credit_sum_case.label("actual_sum_credit"),
        )
        .join(Dictionary, Plan.category_id == Dictionary.id)
        .outerjoin(
            Payment,
            and_(
                Dictionary.name == "збір",
                Payment.payment_date >= start_of_month,
                Payment.payment_date <= target_date,
            ),
        )
        .outerjoin(
            Credit,
            and_(
                Dictionary.name == "видача",
                Credit.issuance_date >= start_of_month,
                Credit.issuance_date <= target_date,
            ),
        )
        .where(
            Plan.period >= start_of_month,
            Plan.period <= target_date,
        )
        .group_by(Plan.period, Dictionary.name, Plan.sum)
        .order_by(Plan.period)
    )

    result = await db.execute(stmt)
    rows = result.fetchall()

    summary = []
    for row in rows:
        if row.category == "збір":
            actual_sum = float(row.actual_sum_payment or 0)
        elif row.category == "видача":
            actual_sum = float(row.actual_sum_credit or 0)
        else:
            actual_sum = 0.0

        percent = (actual_sum / float(row.plan_sum) * 100) if row.plan_sum else 0

        summary.append({
            "month": row.period,
            "category": row.category,
            "plan_sum": float(row.plan_sum),
            "actual_sum": actual_sum,
            "performance_percent": round(percent, 2),
        })

    return summary


@router.get("/year_performance", response_model=List[YearPerformanceOut])
async def get_year_summary(
    year: int = Query(...),
    db: AsyncSession = Depends(get_db)
) -> List[YearPerformanceOut]:
    plan_subquery = (
        select(
            extract("month", Plan.period).label("month"),
            func.sum(
                case((Dictionary.name == "видача", Plan.sum), else_=0)
            ).label("plan_credit_sum"),
            func.sum(
                case((Dictionary.name == "збір", Plan.sum), else_=0)
            ).label("plan_payment_sum")
        )
        .join(Dictionary, Plan.category_id == Dictionary.id)
        .where(extract("year", Plan.period) == year)
        .group_by(extract("month", Plan.period))
        .subquery()
    )

    stmt = (
        select(
            plan_subquery.c.month,
            func.count(func.distinct(Credit.id)).label("credit_count"),
            plan_subquery.c.plan_credit_sum,
            func.sum(
                case((Dictionary.name == "видача", Credit.body), else_=0)
            ).label("actual_credit_sum"),
            func.count(func.distinct(Payment.id)).label("payment_count"),
            plan_subquery.c.plan_payment_sum,
            func.sum(
                case((Dictionary.name == "збір", Payment.sum), else_=0)
            ).label("actual_payment_sum"),
        )
        .select_from(Plan)
        .join(Dictionary, Plan.category_id == Dictionary.id)
        .outerjoin(
            Credit,
            and_(
                Dictionary.name == "видача",
                extract("year", Credit.issuance_date) == year,
                extract("month", Credit.issuance_date) == extract("month", Plan.period),
            )
        )
        .outerjoin(
            Payment,
            and_(
                Dictionary.name == "збір",
                extract("year", Payment.payment_date) == year,
                extract("month", Payment.payment_date) == extract("month", Plan.period),
            )
        )
        .join(plan_subquery, extract("month", Plan.period) == plan_subquery.c.month)
        .where(extract("year", Plan.period) == year)
        .group_by(plan_subquery.c.month, plan_subquery.c.plan_credit_sum, plan_subquery.c.plan_payment_sum)
        .order_by(plan_subquery.c.month)
    )

    result = await db.execute(stmt)
    rows = result.fetchall()

    summary = []
    for row in rows:
        credit_plan = float(row.plan_credit_sum or 0)
        credit_actual = float(row.actual_credit_sum or 0)
        credit_percent = (credit_actual / credit_plan * 100) if credit_plan else 0

        payment_plan = float(row.plan_payment_sum or 0)
        payment_actual = float(row.actual_payment_sum or 0)
        payment_percent = (payment_actual / payment_plan * 100) if payment_plan else 0

        summary.append({
            "month": f"{year}-{int(row.month):02d}",
            "credit_count": row.credit_count,
            "plan_credit_sum": credit_plan,
            "actual_credit_sum": credit_actual,
            "credit_performance_percent": round(credit_percent, 2),
            "payment_count": row.payment_count,
            "plan_payment_sum": payment_plan,
            "actual_payment_sum": payment_actual,
            "payment_performance_percent": round(payment_percent, 2),
            "credit_share_percent_of_year": 0,
            "payment_share_percent_of_year": 0,
        })

    total_credit = sum(m["actual_credit_sum"] for m in summary)
    total_payment = sum(m["actual_payment_sum"] for m in summary)

    for month in summary:
        month["credit_share_percent_of_year"] = round(
            (month["actual_credit_sum"] / total_credit * 100) if total_credit else 0, 2
        )
        month["payment_share_percent_of_year"] = round(
            (month["actual_payment_sum"] / total_payment * 100) if total_payment else 0, 2
        )

    return summary


