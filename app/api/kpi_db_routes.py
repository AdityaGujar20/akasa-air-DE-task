from fastapi import APIRouter, Query

from app.kpi.kpi_db import (
    repeat_customers,
    monthly_order_trends,
    regional_revenue,
    top_customers_last_30_days,
)

router = APIRouter(prefix="/kpi/db", tags=["KPIs - Database"])


@router.get("/repeat-customers")
def get_repeat_customers():
    return repeat_customers()


@router.get("/monthly-order-trends")
def get_monthly_order_trends():
    return monthly_order_trends()


@router.get("/regional-revenue")
def get_regional_revenue():
    return regional_revenue()


@router.get("/top-customers")
def get_top_customers(limit: int = Query(10, ge=1)):
    return top_customers_last_30_days(limit=limit)
