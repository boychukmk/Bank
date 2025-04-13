from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import init_db
from app.routers import upload, user_credits, plans_insert, plan_perfomance

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app.include_router(upload.router, prefix="/upload", tags=["Upload CSV"])
app.include_router(user_credits.router, prefix="/credits", tags=["User Credits"])
app.include_router(plan_perfomance.router, prefix="/plan", tags=["Plan Performance"])
app.include_router(plans_insert.router, prefix="/plan", tags=["Insert Plan"])
