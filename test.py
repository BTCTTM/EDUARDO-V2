import os
from alpaca.trading.client import TradingClient
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.data.historical import StockHistoricalDataClient

def get_alpaca_client() -> TradingClient:
    """Initialize Alpaca client with API keys from environment."""
    api_key = os.environ.get("eduardo_v2_key")
    api_secret = os.environ.get("eduardo_v2_secret")
    #potential to do: specify paper trading
    return TradingClient(api_key, api_secret)


def get_account_info() -> dict:
    """
    Get account information including available capital and positions.
    
    Returns:
        dict with account details:
        - cash: Available cash
        - portfolio_value: Total portfolio value
        - buying_power: Available buying power
        - positions: Current positions
    """
    client = get_alpaca_client()
    
    account = client.get_account()
    positions = client.get_all_positions()

    positions_dict = {}
    for pos in positions:
        positions_dict[pos.symbol] = {
            "qty": float(pos.qty),
            "market_value": float(pos.market_value),
            "avg_entry_price": float(pos.avg_entry_price),
            "current_price": float(pos.current_price),
            "unrealized_pl": float(pos.unrealized_pl),
            "unrealized_plpc": float(pos.unrealized_plpc)
        }
    
    return {
        "cash": float(account.cash),
        "portfolio_value": float(account.portfolio_value),
        "buying_power": float(account.buying_power),
        "positions": positions_dict
    }

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
import os

def get_current_stock_price(symbol: str) -> float:
    data_client = StockHistoricalDataClient(
        os.environ["eduardo_v2_key"],
        os.environ["eduardo_v2_secret"],
    )

    req = StockLatestQuoteRequest(symbol_or_symbols=symbol)  # <-- FIX
    quotes = data_client.get_stock_latest_quote(req)
    q = quotes[symbol]

    return float(q.ask_price)  # or q.bid_price, or (q.bid_price + q.ask_price)/2


print(get_current_stock_price("AAPL"))