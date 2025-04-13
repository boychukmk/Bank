import io
import pandas as pd
from typing import Literal
from pydantic import constr
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User, Credit, Dictionary, Plan, Payment


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

    model = model_mapping.get(table_name.lower())
    if not model:
        raise HTTPException(status_code=400, detail="Invalid table name.")

    required_fields = set(model.__table__.columns.keys())
    records = df.to_dict(orient='records')

    instances = []
    for record in records:
        if not required_fields.issubset(record.keys()):
            continue

        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif "date" in key.lower() or "period" in key.lower() and isinstance(value, str):
                try:
                    record[key] = datetime.strptime(value, "%d.%m.%Y").date()
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid date format in field '{key}': '{value}' (expected dd.mm.yyyy)")

        try:
            instance = model(**record)
            instances.append(instance)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error creating model instance: {e}")

    if not instances:
        raise HTTPException(status_code=400, detail="No valid records to upload.")

    db.add_all(instances)
    await db.commit()
    return {"message": f"Successfully uploaded data to {table_name}. Available tables are: {', '.join(VALID_TABLES)}."}
