from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import date
from typing import List

from app.core.database import get_db
from app.models import Credit, Payment
from app.schemas.analytics_schemas import UserCreditInfo, OpenCreditInfo, ClosedCreditInfo

router = APIRouter()


@router.get("/user_credits/{user_id}", response_model=List[UserCreditInfo])
async def get_user_credits(user_id: int, db: AsyncSession = Depends(get_db)) -> List[UserCreditInfo]:
    result = await db.execute(select(Credit).where(Credit.user_id == user_id))
    credits = result.scalars().all()

    if not credits:
        raise HTTPException(
            status_code=404,
            detail="User not found or no credits available."
        )

    response = []
    today = date.today()
    for credit in credits:
        result = await db.execute(select(Payment).where(Payment.credit_id == credit.id))
        payments = result.scalars().all()

        if credit.actual_return_date:
            total_payments = sum(payment.sum for payment in payments)
            credit_info = ClosedCreditInfo(
                issuance_date=credit.issuance_date,
                is_closed=True,
                return_date=credit.actual_return_date,
                body=credit.body,
                percent=credit.percent,
                total_payments=total_payments
            )
        else:
            overdue_days = (today - credit.return_date).days if today > credit.return_date else 0
            body_payments = sum(p.sum for p in payments if p.type_id == 1)
            percent_payments = sum(p.sum for p in payments if p.type_id == 2)

            credit_info = OpenCreditInfo(
                issuance_date=credit.issuance_date,
                is_closed=False,
                return_date=credit.return_date,
                overdue_days=overdue_days,
                body=credit.body,
                percent=credit.percent,
                body_payments=body_payments,
                percent_payments=percent_payments
            )

        response.append(credit_info)

    return response

