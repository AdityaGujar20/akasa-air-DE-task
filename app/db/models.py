from sqlalchemy import (
    Column, String, Integer, Float, DateTime,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.db.connection import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(50), primary_key=True)
    customer_name = Column(String(255))
    mobile_number = Column(String(20), index=True)
    region = Column(String(100))

    orders = relationship("Order", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String(50), primary_key=True)
    mobile_number = Column(String(20), index=True)
    order_date_time = Column(DateTime)
    sku_id = Column(String(50))
    sku_count = Column(Integer)
    total_amount = Column(Float)
    customer_id = Column(String(50), ForeignKey("customers.customer_id"))

    customer = relationship("Customer", back_populates="orders")

    __table_args__ = (
        UniqueConstraint("order_id", "sku_id", name="uix_order_sku"),
    )
