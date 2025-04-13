from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, case, extract
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta
from typing import List

from app.core.database import get_db
from app.models import Plan, Dictionary, Credit, Payment
from app.schemas.analytics_schemas import PlansPerformanceOut, YearPerformanceOut

router = APIRouter()


@router.get("/month_performance", response_model=List[PlansPerformanceOut])
async def get_plans_performance(
        year: int = Query(...),
        month: int = Query(...),
        db: AsyncSession = Depends(get_db)
) -> List[PlansPerformanceOut]:
    start_of_month = date(year, month, 1)
    if month == 12:
        end_of_month = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_of_month = date(year, month + 1, 1) - timedelta(days=1)
    print(start_of_month, " - ", end_of_month)

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
                Payment.payment_date >= start_of_month,
                Payment.payment_date <= end_of_month,
            ),
        )
        .outerjoin(
            Credit,
            and_(
                Credit.issuance_date >= start_of_month,
                Credit.issuance_date <= end_of_month,
            ),
        )
        .where(
            Plan.period >= start_of_month,
            Plan.period <= end_of_month
        )
        .group_by(Plan.period, Dictionary.name, Plan.sum)
    )

    result = await db.execute(stmt)
    rows = result.fetchall()

    response = []
    for row in rows:
        print("Row period is ", row.period)
        if row.category == "збір":
            actual_sum = float(row.actual_sum_payment or 0)
        elif row.category == "видача":
            actual_sum = float(row.actual_sum_credit or 0)
        else:
            actual_sum = 0.0

        percent = (actual_sum / float(row.plan_sum) * 100) if row.plan_sum else 0

        response.append({
            "month": row.period,
            "category": row.category,
            "plan_sum": float(row.plan_sum),
            "actual_sum": actual_sum,
            "performance_percent": round(percent, 2),
        })

    return response


@router.get("/year_performance", response_model=List[YearPerformanceOut])
async def get_year_performance(
        year: int = Query(...),
        db: AsyncSession = Depends(get_db)
) -> List[YearPerformanceOut]:
    # Загальна сума за рік (для відсотків)
    credit_total_stmt = select(func.sum(Credit.body)).where(extract("year", Credit.issuance_date) == year)
    payment_total_stmt = (
        select(func.sum(Payment.sum))
        .join(Dictionary, Payment.type_id == Dictionary.id)
        .where(
            extract("year", Payment.payment_date) == year,
            Dictionary.name == "збір"
        )
    )

    total_issue_sum = (await db.execute(credit_total_stmt)).scalar() or 0
    total_payment_sum = (await db.execute(payment_total_stmt)).scalar() or 0

    # Створюємо запит для отримання статистики по місяцях
    stmt = (
        select(
            func.date_trunc('month', Credit.issuance_date).label("month"),
            extract('year', Credit.issuance_date).label("year"),
            func.count(Credit.id).label("issue_count"),
            func.sum(Credit.body).label("actual_issue_sum"),
            func.count(Payment.id).label("payment_count"),
            func.sum(
                case((Dictionary.name == "збір", Payment.sum), else_=0)
            ).label("actual_payment_sum"),
            func.sum(
                case((Dictionary.name == "видача", Plan.sum), else_=0)
            ).label("plan_issue_sum"),
            func.sum(
                case((Dictionary.name == "збір", Plan.sum), else_=0)
            ).label("plan_payment_sum"),
        )
        .outerjoin(Payment, Payment.credit_id == Credit.id)
        .outerjoin(Dictionary, Payment.type_id == Dictionary.id)
        .outerjoin(
            Plan,
            and_(
                extract("month", Plan.period) == extract("month", Credit.issuance_date),
                extract("year", Plan.period) == extract("year", Credit.issuance_date),
            )
        )
        .where(extract("year", Credit.issuance_date) == year)
        .group_by("month", "year")
        .order_by("month")
    )

    result = await db.execute(stmt)
    rows = result.fetchall()

    response = []
    for row in rows:
        actual_issue_sum = float(row.actual_issue_sum or 0)
        actual_payment_sum = float(row.actual_payment_sum or 0)
        plan_issue_sum = float(row.plan_issue_sum or 0)
        plan_payment_sum = float(row.plan_payment_sum or 0)

        # Відсоток виконання плану по видачах
        issue_performance_percent = round((actual_issue_sum / plan_issue_sum * 100) if plan_issue_sum else 0, 2)

        # Відсоток виконання плану по платежам
        payment_performance_percent = round((actual_payment_sum / plan_payment_sum * 100) if plan_payment_sum else 0, 2)

        # Частка видач по місяцю від суми видач за рік
        issue_share = round((actual_issue_sum / total_issue_sum * 100) if total_issue_sum else 0, 2)

        # Частка платежів по місяцю від суми платежів за рік
        payment_share = round((actual_payment_sum / total_payment_sum * 100) if total_payment_sum else 0, 2)

        response.append({
            "month": row.month.strftime("%Y-%m"),  # Форматуємо місяць як "YYYY-MM"
            "year": row.year,
            "issue_count": row.issue_count,
            "plan_issue_sum": plan_issue_sum,
            "actual_issue_sum": actual_issue_sum,
            "issue_performance_percent": issue_performance_percent,
            "payment_count": row.payment_count,
            "plan_payment_sum": plan_payment_sum,
            "actual_payment_sum": actual_payment_sum,
            "payment_performance_percent": payment_performance_percent,
            "issue_share": issue_share,
            "payment_share": payment_share,
        })

    return response
