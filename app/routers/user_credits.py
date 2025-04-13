from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import date

from app.core.database import get_db
from app.models import Credit, Payment
from app.schemas.analytics_schemas import UserCreditInfo

router = APIRouter()


@router.get("/user_credits/{user_id}", response_model=UserCreditInfo)
async def get_user_credits(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Credit).where(Credit.user_id == user_id))
    credits = result.scalars().all()

    if not credits:
        raise HTTPException(status_code=404, detail="User not found or no credits available.")

    response = []
    for credit in credits:
        credit_info = {
            "issuance_date": credit.issuance_date,
            "is_closed": bool(credit.actual_return_date)
        }

        if credit.actual_return_date:
            result = await db.execute(select(Payment).where(Payment.credit_id == credit.id))
            payments = result.scalars().all()
            total_payments = sum(payment.sum for payment in payments)

            credit_info.update({
                "return_date": credit.actual_return_date,
                "body": credit.body,
                "percent": credit.percent,
                "total_payments": total_payments
            })
        else:
            today = date.today()
            overdue_days = (today - credit.return_date).days if today > credit.return_date else 0

            result = await db.execute(select(Payment).where(Payment.credit_id == credit.id))
            payments = result.scalars().all()
            body_payments = sum(payment.sum for payment in payments if payment.type_id == 1)
            percent_payments = sum(payment.sum for payment in payments if payment.type_id == 2)

            credit_info.update({
                "return_date": credit.return_date,
                "overdue_days": overdue_days,
                "body": credit.body,
                "percent": credit.percent,
                "body_payments": body_payments,
                "percent_payments": percent_payments
            })

        response.append(credit_info)

    return response
