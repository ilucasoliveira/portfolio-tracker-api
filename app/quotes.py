import os
import httpx
import logging

from decimal import Decimal
from dotenv import load_dotenv

from app.cache import cache_set, cache_get

load_dotenv()

QUOTE_API = os.getenv("QUOTES_API_KEY")
BRAPI_URL = "https://brapi.dev/api/v2/stocks/quote"
QUOTE_TTL = 60

logger = logging.getLogger(__name__)

async def _fetch_from_api(tickers: list[str]) -> dict[str, Decimal]:
    
    tickers_str = ",".join(tickers)
    params = {
        "symbols": tickers_str,
        "token": QUOTE_API
    }
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(BRAPI_URL, params=params)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Quote fetch failed: %s", exc)
            return {}
        
        data = response.json()
        quotes = {}
        
        for item in data["results"]:
            data_field = item.get("data")
            if not data_field:
                continue
            symbol = item["symbol"]
            price = data_field["regularMarketPrice"]
            quotes[symbol] = Decimal(str(price))
        
        return quotes

async def fetch_quotes(tickers: list[str]) -> dict[str, Decimal]:
    
    quotes = {}
    missing = []
    
    for ticker in tickers:
        cached = await cache_get(f"quote:{ticker}")
        if cached is not None:
            quotes[ticker] = Decimal(cached)
        else:
            missing.append(ticker)
    
    if not missing:
        return quotes
    
    fetched = await _fetch_from_api(missing)
    
    for ticker, price in fetched.items():
        quotes[ticker] = price
        await cache_set(f"quote:{ticker}", str(price), ttl=QUOTE_TTL)
    
    return quotes