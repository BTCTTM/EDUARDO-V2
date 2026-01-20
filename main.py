"""
EDUARDO-V2: Automated Trading Pipeline

Scheduler runs every Monday at 8:30 AM CDT:
1. GPT researches news and picks 5 companies
2. Claude analyzes fundamental data for each company
3. Grok makes quantitative investment decisions
4. Alpaca executes trades

If trades fail, retry next day. Otherwise, resume next Monday.
"""
import logging
import argparse
from datetime import datetime

from scheduler import EduardoScheduler, CDT
from gpt_client import research_companies
from claude_client import analyze_fundamentals
from grok_client import make_investment_decision
from alpaca_client import get_account_info, execute_trades, check_market_open
from models import TradeResult
from openai import RateLimitError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('eduardo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_trading_pipeline() -> bool:
    """
    Execute the full EDUARDO-V2 trading pipeline.
    
    Returns:
        True if all trades succeeded, False otherwise
    """
    try:
        # Step 0: Check if market is open
        logger.info("Checking market status...")
        if not check_market_open():
            logger.warning("Market is closed. Will retry when market opens.")
            return False
        
        # Step 1: Get account info from Alpaca
        logger.info("Step 1: Fetching account info from Alpaca...")
        account_info = get_account_info()
        available_capital = account_info["cash"]
        current_positions = account_info["positions"]
        
        logger.info(f"  Available capital: ${available_capital:,.2f}")
        logger.info(f"  Portfolio value: ${account_info['portfolio_value']:,.2f}")
        logger.info(f"  Current positions: {len(current_positions)}")
        
        # Step 2: GPT researches and picks 5 companies
        logger.info("Step 2: GPT researching news and selecting companies...")
        try:
            gpt_response = research_companies()
        except RateLimitError as e:
            # Common case: insufficient_quota. Retrying won't help until billing/quota is fixed.
            logger.error("OpenAI request failed (RateLimitError). This usually means your API key has no remaining quota/billing.")
            logger.error("Fix: check your OpenAI billing/usage, then re-run.")
            logger.error(f"Details: {e}")
            return False
        
        logger.info(f"  GPT selected {len(gpt_response.picks)} companies:")
        for pick in gpt_response.picks:
            logger.info(f"    - {pick.ticker}: {pick.company}")
        
        # Step 3: Claude analyzes fundamentals
        logger.info("Step 3: Claude analyzing fundamental data...")
        claude_response = analyze_fundamentals(gpt_response.picks)
        
        logger.info(f"  Claude analyzed {len(claude_response.fundamentals)} companies:")
        for fund in claude_response.fundamentals:
            logger.info(f"    - {fund.ticker}: P/E={fund.pe_ratio}, Growth={fund.earnings_growth}%")
        
        # Step 4: Grok makes investment decisions
        logger.info("Step 4: Grok making investment decisions...")
        grok_response = make_investment_decision(
            picks=gpt_response.picks,
            fundamentals=claude_response.fundamentals,
            available_capital=available_capital,
            current_positions=current_positions
        )
        
        logger.info(f"  Grok made {len(grok_response.decisions)} decisions:")
        for decision in grok_response.decisions:
            logger.info(f"    - {decision.action} {decision.shares} shares of {decision.ticker} (confidence: {decision.confidence:.0%})")
        
        logger.info(f"  Portfolio risk analysis: {grok_response.portfolio_risk_analysis}")
        
        # Step 5: Execute trades via Alpaca
        logger.info("Step 5: Executing trades via Alpaca...")
        trade_results = execute_trades(grok_response.decisions)
        
        # Check results
        all_successful = True
        for result in trade_results:
            if result.success:
                logger.info(f"  OK: {result.action} {result.shares} {result.ticker} @ ${result.price:.2f} = ${result.total_value:,.2f}")
            else:
                logger.error(f"  FAIL: Failed to {result.action} {result.ticker}: {result.error_message}")
                all_successful = False
        
        if not trade_results:
            logger.info("  No trades to execute (Grok may have decided to hold)")
            all_successful = True
        
        # Summary
        logger.info("=" * 50)
        if all_successful:
            logger.info("Pipeline completed successfully!")
        else:
            logger.warning("Some trades failed. Will retry tomorrow.")
        logger.info("=" * 50)
        
        return all_successful
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        logger.exception("Full traceback:")
        return False


def main():
    """Main entry point for EDUARDO-V2."""
    parser = argparse.ArgumentParser(description="EDUARDO-V2 Automated Trading System")
    parser.add_argument(
        "--run-now", 
        action="store_true", 
        help="Run the trading pipeline immediately instead of waiting for scheduled time"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline without executing actual trades (for testing)"
    )
    args = parser.parse_args()
    
    logger.info("=" * 50)
    logger.info("EDUARDO-V2 Starting")
    logger.info(f"Time: {datetime.now(CDT).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info("=" * 50)
    
    scheduler = EduardoScheduler(run_trading_pipeline)
    
    if args.run_now:
        logger.info("Running pipeline immediately (--run-now flag)")
        scheduler.run_now()
    else:
        logger.info("Starting scheduler (Monday 8:30 AM CDT)")
        scheduler.start()


if __name__ == "__main__":
    main()
