from fastapi import APIRouter
from app.kpi.kpi_memory import (
    repeat_customers_memory,
    monthly_order_trends_memory,
    regional_revenue_memory,
    top_customers_last_30_days_memory
)

router = APIRouter(prefix="/kpi/memory", tags=["KPI In-Memory"])


@router.get("/repeat-customers")
def get_repeat_customers():
    return repeat_customers_memory()


@router.get("/monthly-order-trends")
def get_monthly_trends():
    return monthly_order_trends_memory()


@router.get("/regional-revenue")
def get_regional_revenue():
    return regional_revenue_memory()


@router.get("/top-customers")
def get_top_customers(limit: int = 10):
    return top_customers_last_30_days_memory(limit=limit)
