import os
import pytest
import pytest_asyncio

from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import(
    create_async_engine,
    async_sessionmaker,
    )

from app.database import get_db
from app.main import app
from app.models import Base

load_dotenv()
DATABASE_TEST = os.getenv("DATABASE_URL_TEST")

@pytest.fixture
def engine():
    return create_async_engine(DATABASE_TEST)

@pytest.fixture
def session_factory(engine):
    return async_sessionmaker(bind=engine, expire_on_commit=False)

@pytest_asyncio.fixture
async def override_get_db(session_factory):
    db = session_factory()
    try:
        yield db
    finally:
        await db.close()

@pytest_asyncio.fixture
async def setup_database(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client(setup_database, override_get_db):
    app.dependency_overrides[get_db] = lambda: override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def authenticated_client(client):
    
    email = "user1@test.com"
    password = "senha1234"
    
    await client.post("/users", json={"email": email, "password": password})
    
    response = await client.post(
        "/login",
        data={"username": email, "password": password},
    )
    token = response.json()["access_token"]
    
    client.headers["Authorization"] = f"Bearer {token}"
    
    yield client