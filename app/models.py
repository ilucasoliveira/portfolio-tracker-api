import enum

from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Integer, String, Date, Enum, ForeignKey, Numeric, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class BuyOrSell(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"

class Transaction(Base):
    __tablename__="transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))
    operation: Mapped[BuyOrSell] = mapped_column(Enum(BuyOrSell))
    quantity: Mapped[int] = mapped_column(Integer)
    unitary_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    operation_date: Mapped[date] = mapped_column(Date, default=date.today)
    
    user: Mapped["User"] = relationship(back_populates="transactions")
    asset: Mapped["Asset"] = relationship(back_populates="transactions")

class User(Base):
    __tablename__="users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(200), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user")

class Asset(Base):
    __tablename__="assets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), unique=True)
    company_name: Mapped[str] = mapped_column(String(200))
    
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="asset")