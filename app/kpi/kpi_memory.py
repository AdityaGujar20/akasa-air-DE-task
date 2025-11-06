import os
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger

CLEANED_DIR = "data/cleaned"


def _latest_cleaned_files():
    files = sorted(os.listdir(CLEANED_DIR))

    cust_files = [f for f in files if "customers_cleaned" in f]
    order_files = [f for f in files if "orders_cleaned" in f]

    if not cust_files or not order_files:
        raise FileNotFoundError("No cleaned files found.")

    customers = os.path.join(CLEANED_DIR, cust_files[-1])
    orders = os.path.join(CLEANED_DIR, order_files[-1])
    return customers, orders


def _load_order_level():
    """
    Load customers + orders and convert orders from SKU-level rows
    to ORDER-LEVEL rows exactly like the DB logic does.
    """
    cust_path, order_path = _latest_cleaned_files()

    logger.info(f"Loading customers → {cust_path}")
    customers = pd.read_csv(cust_path)

    logger.info(f"Loading orders → {order_path}")
    orders = pd.read_csv(order_path)

    # Convert types
    orders["order_date_time"] = pd.to_datetime(orders["order_date_time"])
    orders["total_amount"] = pd.to_numeric(orders["total_amount"], errors="coerce").fillna(0)

    # Join with customers
    merged = orders.merge(
        customers[["customer_id", "mobile_number", "region"]],
        on="mobile_number",
        how="left"
    )

    # ✅ Convert SKU-level → ORDER-LEVEL like SQL
    order_level = (
        merged.groupby(["order_id", "customer_id"], dropna=False)
        .agg(
            order_date_time=("order_date_time", "max"),
            order_total=("total_amount", "max"),   # EXACT SQL LOGIC
            region=("region", "first")
        )
        .reset_index()
    )

    return order_level


def repeat_customers_memory():
    orders = _load_order_level()

    counts = (
        orders.groupby("customer_id")["order_id"]
        .nunique()
        .reset_index(name="order_count")
    )

    repeats = counts[counts["order_count"] > 1]
    return repeats.to_dict(orient="records")


def monthly_order_trends_memory():
    orders = _load_order_level()

    orders["month"] = orders["order_date_time"].dt.to_period("M").astype(str)

    trends = (
        orders.groupby("month")["order_id"]
        .nunique()
        .reset_index(name="orders_count")
    )

    return trends.to_dict(orient="records")


def regional_revenue_memory():
    orders = _load_order_level()

    revenue = (
        orders.groupby("region")["order_total"]
        .sum()
        .reset_index(name="revenue")
    )

    return revenue.to_dict(orient="records")


def top_customers_last_30_days_memory(limit=10):
    orders = _load_order_level()

    cutoff = datetime.now() - timedelta(days=30)
    last30 = orders[orders["order_date_time"] >= cutoff]

    ranked = (
        last30.groupby(["customer_id"])
        ["order_total"].sum()
        .reset_index(name="total_spend")
        .sort_values("total_spend", ascending=False)
        .head(limit)
    )

    return ranked.to_dict(orient="records")
