import os
import pandas as pd
from loguru import logger
from sqlalchemy.dialects.mysql import insert as mysql_insert

from app.db.connection import SessionLocal, engine
from app.db.models import Customer, Order
from sqlalchemy import inspect

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLEANED_DIR = os.path.join(BASE_DIR, "data", "cleaned")


def load_cleaned_customers(session, filepath):
    logger.info(f"Loading customers from: {filepath}")
    df = pd.read_csv(filepath)

    for _, row in df.iterrows():
        stmt = mysql_insert(Customer).values(
            customer_id=row["customer_id"],
            customer_name=row["customer_name"],
            mobile_number=str(row["mobile_number"]),
            region=row["region"],
        )

        stmt = stmt.on_duplicate_key_update(
            customer_name=stmt.inserted.customer_name,
            mobile_number=stmt.inserted.mobile_number,
            region=stmt.inserted.region,
        )

        session.execute(stmt)

    logger.success("Customers loaded successfully (UPSERT).")


def load_cleaned_orders(session, filepath):
    logger.info(f"Loading orders from: {filepath}")
    df = pd.read_csv(filepath)

    customers = session.query(Customer).all()
    mobile_to_customer = {str(c.mobile_number): c.customer_id for c in customers}

    for _, row in df.iterrows():
        cust_id = mobile_to_customer.get(str(row["mobile_number"]))

        stmt = mysql_insert(Order).values(
            order_id=row["order_id"],
            mobile_number=str(row["mobile_number"]),
            order_date_time=row["order_date_time"],
            sku_id=row["sku_id"],
            sku_count=row["sku_count"],
            total_amount=row["total_amount"],
            customer_id=cust_id
        )

        stmt = stmt.on_duplicate_key_update(
            mobile_number=stmt.inserted.mobile_number,
            order_date_time=stmt.inserted.order_date_time,
            sku_id=stmt.inserted.sku_id,
            sku_count=stmt.inserted.sku_count,
            total_amount=stmt.inserted.total_amount,
            customer_id=stmt.inserted.customer_id,
        )

        session.execute(stmt)

    logger.success("Orders loaded successfully (UPSERT).")


def run_db_loader():
    logger.info("Running DB Loader...")
    
    # Check if cleaned directory exists
    if not os.path.exists(CLEANED_DIR):
        error_msg = f"Cleaned directory not found: {CLEANED_DIR}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Test database connection
    try:
        with engine.connect() as conn:
            logger.info("Database connection successful")
    except Exception as e:
        error_msg = f"Cannot connect to database: {e}. Check your database configuration and ensure MySQL is running."
        logger.error(error_msg)
        raise ConnectionError(error_msg)
    
    # Check if database tables exist
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        required_tables = ["customers", "orders"]
        
        missing_tables = [t for t in required_tables if t not in existing_tables]
        if missing_tables:
            error_msg = f"Database tables not found: {missing_tables}. Please run 'python scripts/init_db.py' to create tables."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Database tables verified: {existing_tables}")
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        error_msg = f"Error checking database tables: {e}"
        logger.error(error_msg)
        raise

    session = SessionLocal()

    try:
        cleaned_files = sorted(os.listdir(CLEANED_DIR))
        logger.info(f"Found {len(cleaned_files)} files in {CLEANED_DIR}")

        customer_files = [f for f in cleaned_files if "customers_cleaned" in f]
        order_files = [f for f in cleaned_files if "orders_cleaned" in f]

        if not customer_files or not order_files:
            error_msg = "No cleaned files found. Run cleaning pipeline first."
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        latest_customer_file = os.path.join(CLEANED_DIR, customer_files[-1])
        latest_order_file = os.path.join(CLEANED_DIR, order_files[-1])
        
        logger.info(f"Loading customers from: {latest_customer_file}")
        logger.info(f"Loading orders from: {latest_order_file}")

        load_cleaned_customers(session, latest_customer_file)
        load_cleaned_orders(session, latest_order_file)

        session.commit()
        logger.success("DB loading completed successfully!")
        return True

    except Exception as e:
        session.rollback()
        logger.error(f"DB Loader Error: {e}")
        logger.exception(e)  # Log full traceback
        raise  # Re-raise the exception so API can handle it

    finally:
        session.close()
