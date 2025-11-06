# file: app/kpi/kpi_db.py
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict, Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.connection import SessionLocal


def _run(session: Session, sql: str, params: dict | None = None) -> List[Dict[str, Any]]:
    rows = session.execute(text(sql), params or {}).mappings().all()
    return [dict(r) for r in rows]


def repeat_customers() -> List[Dict[str, Any]]:
    """
    Customers with more than one order (counting DISTINCT orders).
    """
    sql = """
    SELECT
      c.customer_id,
      c.customer_name,
      c.mobile_number,
      c.region,
      COUNT(DISTINCT o.order_id) AS order_count
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    GROUP BY c.customer_id, c.customer_name, c.mobile_number, c.region
    HAVING COUNT(DISTINCT o.order_id) > 1
    ORDER BY order_count DESC, c.customer_id;
    """
    with SessionLocal() as session:
        return _run(session, sql)


def monthly_order_trends() -> List[Dict[str, Any]]:
    """
    Aggregate orders by calendar month.
    Counts DISTINCT orders (since orders table is SKU-level).
    """
    sql = """
    SELECT
      DATE_FORMAT(o.order_date_time, '%Y-%m') AS month,
      COUNT(DISTINCT o.order_id) AS orders_count
    FROM orders o
    GROUP BY DATE_FORMAT(o.order_date_time, '%Y-%m')
    ORDER BY month;
    """
    with SessionLocal() as session:
        return _run(session, sql)


def regional_revenue() -> List[Dict[str, Any]]:
    """
    Sum total revenue by region.
    IMPORTANT: total_amount repeats per SKU in many datasets.
    To avoid double counting, we compute one row per order_id,customer_id
    taking MAX(total_amount) and then sum by region.
    """
    sql = """
    SELECT
      c.region,
      SUM(u.order_total) AS revenue
    FROM (
      SELECT
        o.order_id,
        o.customer_id,
        MAX(o.total_amount) AS order_total
      FROM orders o
      GROUP BY o.order_id, o.customer_id
    ) u
    JOIN customers c ON c.customer_id = u.customer_id
    GROUP BY c.region
    ORDER BY revenue DESC, c.region;
    """
    with SessionLocal() as session:
        return _run(session, sql)


def top_customers_last_30_days(limit: int = 10, tz: str = "Asia/Kolkata") -> List[Dict[str, Any]]:
    """
    Rank customers by spend in the last 30 days (tz-aware).
    Uses the same unique-order logic (MAX(total_amount) per order).
    """
    now_tz = datetime.now(ZoneInfo(tz))
    cutoff = now_tz - timedelta(days=30)

    sql = """
    SELECT
      c.customer_id,
      c.customer_name,
      c.mobile_number,
      c.region,
      SUM(u.order_total) AS total_spend
    FROM (
      SELECT
        o.order_id,
        o.customer_id,
        MAX(o.total_amount) AS order_total
      FROM orders o
      WHERE o.order_date_time >= :cutoff
      GROUP BY o.order_id, o.customer_id
    ) u
    JOIN customers c ON c.customer_id = u.customer_id
    GROUP BY c.customer_id, c.customer_name, c.mobile_number, c.region
    ORDER BY total_spend DESC, c.customer_id
    LIMIT :limit;
    """
    with SessionLocal() as session:
        return _run(session, sql, {"cutoff": cutoff, "limit": limit})
