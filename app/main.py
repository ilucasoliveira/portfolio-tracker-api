from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


from app.database import init_db, get_db
from app.models import User
from app.schemas import SchemaUser, SchemaUserResponse, SchemaToken
from app.security import(
    hash_password,
    verify_password,
    create_access_token,
    get_current_user)

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