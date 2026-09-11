from contextlib import asynccontextmanager
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import init_db, get_db
from app.models import User, Asset, Transaction
from app.schemas import( 
    SchemaUser,
    SchemaUserResponse,
    SchemaToken,
    SchemaAsset,
    SchemaAssetResponse,
    SchemaTransaction,
    SchemaTransactionResponse,
    SchemaPortfolioResponse,)
from app.security import(
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,)
from app.services import calculate_position

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    lifespan=lifespan,
    title="Investment Portfolio API",
    description=(
        "REST API for tracking personal investment portfolios. "
        "Users register their buy and sell transactions, and the API "
        "derives current positions, average cost and profit or loss "
        "using live quotes from an external market data provider. "
        "Authentication is handled with JWT bearer tokens, and each "
        "user only ever sees their own transactions."
    ),
    version="0.1.0",
    contact={
        "name":"Lucas de Oliveira",
        "email":"lucasoliveirapimentel.dev@gmail.com"
    }
)

@app.get("/")
async def health_check():
    return {"status": "OK"}

@app.post("/users", status_code=201, response_model=SchemaUserResponse)
async def create_user(user: SchemaUser, db: AsyncSession = Depends(get_db)):
    
    verify_email = await db.execute(select(User).where(User.email == user.email))
    verify_email_result = verify_email.scalars().first()
    
    if verify_email_result is not None:
        raise HTTPException(status_code=409, detail="Email already registered. Please, try another one again!")
    
    new_user = User(
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered. Please, try another one again!")
    
    return new_user

@app.post("/login", status_code=200, response_model=SchemaToken)
async def create_login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    
    seek_user = form_data.username
    user = await db.execute(select(User).where(User.email == seek_user))
    user_result = user.scalars().first()
    
    if not user_result or not verify_password(form_data.password, user_result.hashed_password):
        raise HTTPException(status_code=401, detail="Unauthorized Credentials")
    
    token = create_access_token({"sub": str(user_result.id)})
    
    return SchemaToken(access_token=token)

@app.post("/assets", status_code=201, response_model=SchemaAssetResponse)
async def create_asset(asset: SchemaAsset, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    
    consult_ticker = await db.execute(select(Asset).where(Asset.ticker == asset.ticker))
    consult_ticker_result = consult_ticker.scalars().first()
    
    if consult_ticker_result:
        raise HTTPException(status_code=409, detail="Ticker already registered. Please, try again")
    
    new_asset = Asset(**asset.model_dump())
    
    try:
        db.add(new_asset)
        await db.commit()
        await db.refresh(new_asset)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Ticker already registered. Please, try again")
    
    return new_asset

@app.get("/assets", response_model=list[SchemaAssetResponse])
async def read_assets(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    
    assets = await db.execute(select(Asset))
    assets_result = assets.scalars().all()
    
    return assets_result

@app.post("/transactions", status_code=201, response_model=SchemaTransactionResponse)
async def create_transaction(transaction: SchemaTransaction, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    
    verify_asset_id = await db.execute(select(Asset).where(Asset.id == transaction.asset_id))
    verify_asset_id_result = verify_asset_id.scalars().first()
    
    if not verify_asset_id_result:
        raise HTTPException(status_code=404, detail="ID not found!")
    
    new_transaction = Transaction(**transaction.model_dump(), user_id=current_user.id)
    
    try:
        db.add(new_transaction)
        await db.commit()
        await db.refresh(new_transaction)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=404, detail="ID not found!")
    
    return new_transaction

@app.get("/transactions", response_model=list[SchemaTransactionResponse])
async def read_transactions(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    
    transactions = await db.execute(select(Transaction).where(Transaction.user_id == current_user.id))
    transactions_result = transactions.scalars().all()
    
    return transactions_result

@app.get("/portfolio", response_model=list[SchemaPortfolioResponse])
async def read_portfolio(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    
    transactions = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .options(selectinload(Transaction.asset))
        .order_by(Transaction.asset_id, Transaction.operation_date, Transaction.id)
    )
    
    transactions_result = transactions.scalars().all()
    
    grouped = {}
    
    for transaction in transactions_result:
        result_asset = transaction.asset_id
        if result_asset not in grouped:
            grouped[result_asset] = []
        grouped[result_asset].append(transaction)
    
    positions = []
    
    for asset_id, asset_transactions in grouped.items():
        position = calculate_position(asset_transactions)
        
        if position["quantity"] == 0:
            continue
        
        asset = asset_transactions[0].asset
        
        positions.append(
            SchemaPortfolioResponse(
                ticker=asset.ticker,
                company_name=asset.company_name,
                quantity=position["quantity"],
                average_price=position["average_price"],
            )
        )
    
    return positions