"""
Alpaca Client for account management and trade execution.
"""
import os
from typing import List, Optional
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from models import InvestmentDecision, TradeResult


def get_alpaca_client() -> TradingClient:
    """Initialize Alpaca client with API keys from environment."""
    api_key = os.environ.get("ALPACA_API_KEY")
    api_secret = os.environ.get("ALPACA_API_SECRET")
    
    if not api_key or not api_secret:
        raise ValueError("ALPACA_API_KEY and ALPACA_API_SECRET environment variables must be set")
    
    # Use paper trading by default (set ALPACA_LIVE=true for live trading)
    paper = os.environ.get("ALPACA_LIVE", "false").lower() != "true"
    
    return TradingClient(api_key, api_secret, paper=paper)


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


def execute_trades(decisions: List[InvestmentDecision]) -> List[TradeResult]:
    """
    Execute trades based on Grok's investment decisions.
    
    Args:
        decisions: List of investment decisions from Grok
    
    Returns:
        List of TradeResult objects with execution details
    """
    client = get_alpaca_client()
    results = []
    
    for decision in decisions:
        if decision.action != "BUY" or decision.shares <= 0:
            continue
            
        try:
            # Create market order
            order_data = MarketOrderRequest(
                symbol=decision.ticker,
                qty=decision.shares,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            
            order = client.submit_order(order_data)
            
            # Get filled price (may need to wait for fill in real scenario)
            filled_price = float(order.filled_avg_price) if order.filled_avg_price else 0.0
            
            results.append(TradeResult(
                ticker=decision.ticker,
                shares=decision.shares,
                action="BUY",
                price=filled_price,
                total_value=filled_price * decision.shares,
                success=True,
                order_id=str(order.id)
            ))
            
        except Exception as e:
            results.append(TradeResult(
                ticker=decision.ticker,
                shares=decision.shares,
                action="BUY",
                price=0.0,
                total_value=0.0,
                success=False,
                error_message=str(e)
            ))
    
    return results


def check_market_open() -> bool:
    """Check if the market is currently open for trading."""
    client = get_alpaca_client()
    clock = client.get_clock()
    return clock.is_open


if __name__ == "__main__":
    # Test account info
    try:
        info = get_account_info()
        print(f"Cash: ${info['cash']:,.2f}")
        print(f"Portfolio Value: ${info['portfolio_value']:,.2f}")
        print(f"Positions: {info['positions']}")
    except Exception as e:
        print(f"Error: {e}")
