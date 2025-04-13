import io
import pandas as pd
from typing import Literal
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User, Credit, Dictionary, Plan, Payment
from app.schemas.model_schemas import UserCSV, CreditCSV, DictionaryCSV, PlanCSV, PaymentCSV

router = APIRouter()

VALID_TABLES = ["users", "credits", "dictionary", "plans", "payments"]


@router.post("/upload_csv/{table_name}")
async def upload_csv(
    table_name: Literal["users", "credits", "dictionary", "plans", "payments"],
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    content = await file.read()
    try:
        df = pd.read_csv(io.StringIO(content.decode('utf-8')), sep='\t')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {e}")

    model_mapping = {
        "users": User,
        "credits": Credit,
        "dictionary": Dictionary,
        "plans": Plan,
        "payments": Payment
    }

    schema_mapping = {
        "users": UserCSV,
        "credits": CreditCSV,
        "dictionary": DictionaryCSV,
        "plans": PlanCSV,
        "payments": PaymentCSV
    }

    model = model_mapping.get(table_name.lower())
    schema = schema_mapping.get(table_name.lower())

    if not model or not schema:
        raise HTTPException(status_code=400, detail="Invalid table name.")

    records = df.to_dict(orient='records')
    instances = []
    validation_errors = []

    for idx, record in enumerate(records, start=2):
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, str) and ("date" in key.lower() or "period" in key.lower()):
                try:
                    record[key] = datetime.strptime(value, "%d.%m.%Y").date()
                except Exception:
                    pass

        try:
            validated_data = schema(**record)
            instance = model(**validated_data.dict())
            instances.append(instance)
        except Exception as e:
            validation_errors.append(f"Row {idx}: {str(e)}")

    if validation_errors:
        raise HTTPException(status_code=400, detail=validation_errors)

    if not instances:
        raise HTTPException(status_code=400, detail="No valid records to upload.")

    db.add_all(instances)
    await db.commit()

    return {
        "message": f"Successfully uploaded {len(instances)} records to {table_name}.",
        "note": "Available tables: users, credits, dictionary, plans, payments"
    }
