from pydantic import Field, field_validator, BaseModel, EmailStr, ConfigDict

from datetime import date, datetime
from decimal import Decimal

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

class SchemaTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    asset_id: int 
    operation: BuyOrSell
    quantity: int
    unitary_price: Decimal
    operation_date: date