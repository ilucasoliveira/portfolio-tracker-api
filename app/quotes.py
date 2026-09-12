import os
import httpx
import logging

from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

QUOTE_API = os.getenv("QUOTES_API_KEY")
BRAPI_URL = "https://brapi.dev/api/v2/stocks/quote"

logger = logging.getLogger(__name__)

async def fetch_quotes(tickers: list[str]) -> dict[str, Decimal]:
    
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