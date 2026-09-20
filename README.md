# Investment Portfolio API

REST API for tracking a personal investment portfolio. Users record their buy and sell
transactions and the API derives current positions, average cost and profit or loss using
live quotes from an external market data provider.

## Stack

- Python 3.14
- FastAPI
- SQLAlchemy 2.0 (async) + asyncpg
- PostgreSQL 18
- Redis 8
- JWT authentication (PyJWT + pwdlib/argon2)
- Docker and Docker Compose
- Poetry

## Status

The core is complete and tested. Remaining:

- [x] User registration with argon2 password hashing
- [x] Login returning a signed JWT access token
- [x] Token validation dependency (`get_current_user`)
- [x] Assets endpoints
- [x] Transactions CRUD, scoped to the authenticated user
- [x] Position calculation from transaction history
- [x] External quotes integration (brapi)
- [x] Redis caching for quotes
- [x] Unit tests for position calculation
- [x] API integration tests against an isolated Postgres
- [ ] Database migrations (Alembic)
- [ ] Reject sells larger than the current position

## Running locally

Requires Docker and Docker Compose.

```bash
git clone https://github.com/ilucasoliveira/portfolio-tracker-api
cd investment-portfolio
cp .env.example .env
```

Generate a signing key and paste it into `SECRET_KEY` in your `.env`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Then start the stack:

```bash
docker compose up --build
```

The API is available at `http://localhost:8000` and the interactive docs at
`http://localhost:8000/docs`.

Postgres is exposed on host port `5433` to avoid clashing with a local installation
on the default `5432`.

## Tests

The suite runs against a dedicated Postgres instance, separate from the
development database. Start it and run pytest:

```bash
docker compose up -d db_test
poetry install --with dev
pytest
```

The schema is created and dropped around every test, so each one starts
from an empty database.

## Authentication

1. `POST /users` to register with an email and a password.
2. `POST /login` with the same credentials to receive an access token.
3. Send the token on every protected request:

```
Authorization: Bearer <token>
```

In the interactive docs, use the **Authorize** button and paste the token without
the `Bearer` prefix.

Tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (30 by default).

## Design decisions

### Transactions, not positions

The database stores one row per operation (buy or sell), never a running position.
The current holding of an asset is derived by aggregating its transactions.

Storing the position directly would be cheaper to read, but it destroys the history
that produced it. Correcting a mistyped order would mean recomputing the position by
hand, and questions like "what was I holding last March" become unanswerable. Keeping
the event log as the single source of truth makes both trivial, at the cost of an
aggregation on read. That read cost is what the Redis cache is there to absorb.

### `NUMERIC` for money, never `FLOAT`

Floating point stores decimal values in base 2, so `10.10 * 3` yields `30.299999999999997`.
Rounding errors accumulate across a portfolio and the reported balance stops matching
reality. Prices use `NUMERIC(12, 2)`, which maps to Python's `Decimal` and is exact.

### Assets are shared, transactions are personal

`assets` has no `user_id`. A ticker such as PETR4 is a fact about the market, identical
for every user, so it is stored once. Duplicating it per user would mean redundant rows
and one external quote request per user for the same price.

`transactions` carries `user_id` and every query filters on the authenticated user, so
one user can never read another user's operations.

### Quotes are cached per ticker, not per portfolio

Each quote is cached under `quote:<TICKER>` rather than caching a whole
portfolio response. A ticker held by several users is then fetched once
for all of them, and buying a new asset does not invalidate the quotes
already cached for the rest of the portfolio. Only the tickers missing
from the cache are requested from the provider.

### The portfolio degrades rather than failing

Cost basis lives in our own database and does not depend on the quote
provider. When the provider is unavailable, `current_price`,
`current_value` and `profit_loss` come back null and the rest of the
portfolio still responds, instead of the whole endpoint returning an
error. Failed fetches are never cached, so tickers already in cache keep
serving their last known price.

## Project structure

```
app/
  main.py       FastAPI app, lifespan and endpoints
  models.py     SQLAlchemy models
  schemas.py    Pydantic schemas
  database.py   Async engine, session factory and init
  security.py   Password hashing, JWT creation and validation
  services.py   Domain logic (position calculation)
  quotes.py     External quote provider client, with caching
  cache.py      Redis client and generic cache helpers
tests/
  conftest.py       Fixtures: test database, session and HTTP client
  test_services.py  Unit tests for position calculation
  test_api.py       Endpoint tests, including ownership
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
