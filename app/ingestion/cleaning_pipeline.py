import os
import pandas as pd
from datetime import datetime
from loguru import logger


BASE_DATA_DIR = "data"
UPLOAD_DIR = os.path.join(BASE_DATA_DIR, "upload")
CLEANED_DIR = os.path.join(BASE_DATA_DIR, "cleaned")

CLEANED_CUSTOMER_PATH = os.path.join(CLEANED_DIR, "customers_cleaned.csv")
CLEANED_ORDER_PATH = os.path.join(CLEANED_DIR, "orders_cleaned.csv")

RAW_CUSTOMER_PATH = os.path.join(UPLOAD_DIR, "customers.csv")
RAW_ORDER_PATH    = os.path.join(UPLOAD_DIR, "orders.xml")


def _standardize_mobile(series: pd.Series) -> pd.Series:
    """Strip non-digits from phone numbers."""
    return series.astype(str).str.replace(r"\D", "", regex=True)


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    """Clean customers but KEEP ALL columns."""
    logger.info("Cleaning customers...")

    required = {"customer_id", "mobile_number"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"customers.csv missing columns: {missing}")

    df = df.dropna(subset=["customer_id", "mobile_number"]).copy()

    df["mobile_number"] = _standardize_mobile(df["mobile_number"])

    if "customer_name" in df.columns:
        df["customer_name"] = df["customer_name"].astype(str).str.strip().str.title()

    if "region" in df.columns:
        df["region"] = df["region"].astype(str).str.strip().str.title()

    df = df.drop_duplicates(ignore_index=True)

    return df


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Cleaning orders...")

    required = {"order_id", "mobile_number", "order_date_time"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"orders.xml missing columns: {missing}")

    df = df.dropna(subset=["order_id", "mobile_number", "order_date_time"]).copy()

    df["mobile_number"] = _standardize_mobile(df["mobile_number"])

    # Convert date
    df["order_date_time"] = pd.to_datetime(df["order_date_time"], errors="coerce")
    df = df.dropna(subset=["order_date_time"])

    # Numeric fix
    for col in ("sku_count", "total_amount"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.drop_duplicates(ignore_index=True)

    return df


def _append_and_dedupe(new_df: pd.DataFrame, final_path: str, keys: list):

    if os.path.exists(final_path):
        old_df = pd.read_csv(final_path)
        combined = pd.concat([old_df, new_df], ignore_index=True)

        combined.drop_duplicates(subset=keys, keep="last", inplace=True)
        combined.to_csv(final_path, index=False)

        logger.success(f"Appended + deduped: {final_path} → {len(combined)} rows")
        return combined

    # No existing file → save fresh
    new_df.to_csv(final_path, index=False)
    logger.success(f"📦 Created new cleaned file: {final_path} → {len(new_df)} rows")
    return new_df



def run_cleaning_pipeline():
    logger.info("Starting cleaning pipeline (APPEND MODE)...")

    if not os.path.exists(RAW_CUSTOMER_PATH):
        logger.error("customers.csv missing in data/upload/")
        return

    if not os.path.exists(RAW_ORDER_PATH):
        logger.error("orders.xml missing in data/upload/")
        return

    try:
        raw_customers = pd.read_csv(RAW_CUSTOMER_PATH)
        raw_orders    = pd.read_xml(RAW_ORDER_PATH)
        logger.info(f"Loaded raw customers: {len(raw_customers)} rows")
        logger.info(f"Loaded raw orders: {len(raw_orders)} rows")
    except Exception as e:
        logger.error(f"Failed to load raw files: {e}")
        return

    try:
        cleaned_customers = clean_customers(raw_customers)
        cleaned_orders    = clean_orders(raw_orders)
    except Exception as e:
        logger.error(f"Cleaning failed: {e}")
        return

    os.makedirs(CLEANED_DIR, exist_ok=True)

    _append_and_dedupe(
        cleaned_customers,
        CLEANED_CUSTOMER_PATH,
        keys=["customer_id"]
    )

    key_cols = ["order_id", "sku_id"] if "sku_id" in cleaned_orders.columns else ["order_id"]

    _append_and_dedupe(
        cleaned_orders,
        CLEANED_ORDER_PATH,
        keys=key_cols
    )

    logger.success("Cleaning pipeline completed successfully (APPEND MODE).")

if __name__ == "__main__":
    run_cleaning_pipeline()
