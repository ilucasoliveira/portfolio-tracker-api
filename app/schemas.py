from pydantic import Field, field_validator, BaseModel, EmailStr, ConfigDict

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from app.models import BuyOrSell

# USER
class SchemaUser(BaseModel):
    email: EmailStr = Field(max_length=200, description="User's email")
    password: str = Field(min_length=8, max_length=128, description="User's password")

class SchemaUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: EmailStr
    created_at: datetime

# TOKEN
class SchemaToken(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ASSET
class SchemaAsset(BaseModel):
    ticker: str = Field(min_length=2, max_length=10, description="Asset's ticker")
    company_name: str = Field(min_length=2, max_length=200, description="Company's name")
    
    @field_validator("ticker")
    @classmethod
    def upper_ticker(cls, value):
        result = value.upper().strip()
        return result

class SchemaAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    ticker: str
    company_name: str

# TRANSACTION
class SchemaTransaction(BaseModel):
    asset_id: int = Field(description="Asset's ID")
    operation: BuyOrSell = Field(description="Buy or Sell operation")
    quantity: int = Field(gt=0, description="Quantity of transactions")
    unitary_price: Decimal = Field(gt=0, description="Unitary's price")
    operation_date: date = Field(default_factory=date.today, description="Date's operation")

class SchemaTransactionUpdate(BaseModel):
    asset_id: int | None = Field(default=None)
    operation: BuyOrSell | None = Field(default=None)
    quantity: int | None = Field(default=None, gt=0)
    unitary_price: Decimal | None = Field(default=None, gt=0)
    operation_date: date | None = Field(default=None)

class SchemaTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    asset_id: int 
    operation: BuyOrSell
    quantity: int
    unitary_price: Decimal
    operation_date: date

# PORTFOLIO
class SchemaPortfolioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    ticker: str
    company_name: str
    quantity: int
    average_price: Decimal
    
    current_price: Decimal | None = None
    current_value: Decimal | None = None
    profit_loss: Decimal | None = None
    
    @field_validator("average_price", "current_price", "current_value", "profit_loss")
    @classmethod
    def round_price(cls, value):
        if value is None:
            return None
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)