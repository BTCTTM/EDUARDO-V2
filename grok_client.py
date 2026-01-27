"""
Grok Client for investment decision making.
Uses xAI API with OpenAI-compatible interface.
"""
import os
import json
from openai import OpenAI
from typing import List
from xai_sdk import Client
from xai_sdk.chat import user, system
from models import (
    CompanyPick, 
    FundamentalData, 
    InvestmentDecision, 
    GrokResponse
)


def get_grok_client() -> OpenAI:
    """Initialize Grok client with API key from environment."""
    api_key = os.environ.get("grok_main")
    if not api_key:
        raise ValueError("grok_main environment variable not set")
    return OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1"
    )


def make_investment_decision(
    picks: List[CompanyPick],
    fundamentals: List[FundamentalData],
    available_capital: float,
    current_positions: dict
) -> GrokResponse:
    """
    Use Grok to make quantitative investment decisions.
    
    Args:
        picks: Company picks from GPT with news/rationale
        fundamentals: Fundamental data from Claude
        available_capital: Available cash in Alpaca account
        current_positions: Current portfolio positions for risk analysis
    
    Returns:
        GrokResponse with investment decisions
    """
    client = get_grok_client()
    
    # Build comprehensive input data
    input_data = {
        "companies": [],
        "available_capital": available_capital,
        "current_positions": current_positions
    }
    
    # Merge picks and fundamentals
    fund_map = {f.ticker: f for f in fundamentals}
    for pick in picks:
        company_data = {
            "company": pick.company,
            "ticker": pick.ticker,
            "news_rationale": pick.rationale,
            "news_summary": pick.news_summary
        }
        if pick.ticker in fund_map:
            f = fund_map[pick.ticker]
            company_data["fundamentals"] = {
                "pe_ratio": f.pe_ratio,
                "cash_flow": f.cash_flow,
                "revenue": f.revenue,
                "market_cap": f.market_cap,
                "debt_to_equity": f.debt_to_equity,
                "earnings_growth": f.earnings_growth,
                "dividend_yield": f.dividend_yield,
                "additional_metrics": f.additional_metrics,
                "analysis_notes": f.analysis_notes
            }
        input_data["companies"].append(company_data)
    
    prompt = f"""You are a quantitative investment analyst making executive investment decisions.

CRITICAL: You must be QUANTITATIVE and DATA-DRIVEN in your decision making. Use specific numbers and metrics.

INPUT DATA:
{json.dumps(input_data, indent=2)}

YOUR TASK:
1. Analyze the portfolio risk based on current positions
2. Evaluate each company using quantitative criteria:
   - P/E ratio vs industry average
   - Earnings growth rate
   - Debt levels and financial health
   - News catalyst strength
   - Risk/reward ratio
3. Decide which company/companies to invest in OR divest from
4. Determine exact number of shares to BUY or SELL based on:
   - Available capital: ${available_capital:,.2f}
   - Position sizing (max 25% of capital per position)
   - Risk tolerance (conservative approach)
   - Current holdings that may need to be sold

Return your response as a JSON object:
{{
    "decisions": [
        {{
            "company": "Company Name",
            "ticker": "TICK",
            "action": "BUY",
            "shares": 100,
            "rationale": "Quantitative reasoning for this decision",
            "confidence": 0.85,
            "risk_assessment": "Low/Medium/High with explanation"
        }},
        {{
            "company": "Another Company",
            "ticker": "ANTH",
            "action": "SELL",
            "shares": 50,
            "rationale": "Reason for selling (e.g. overvalued, taking profits, rebalancing)",
            "confidence": 0.75,
            "risk_assessment": "Medium - locking in gains"
        }}
    ],
    "portfolio_risk_analysis": "Overall assessment of portfolio risk after these trades",
    "available_capital": {available_capital}
}}

RULES:
- Use "BUY" for new purchases
- Use "SELL" to reduce or exit positions you currently hold
- Be conservative with position sizing
- Never invest more than available capital
- Never sell more shares than currently held
- Provide specific share counts based on approximate current prices
- Confidence should be 0-1 scale based on data quality

Return ONLY the JSON object, no additional text."""

    response = client.chat.completions.create(
        model='grok-4',
        messages=[
            {
                "role": "system",
                "content": "You are a quantitative investment analyst. Make data-driven decisions using specific metrics and numbers. Always respond with valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3  # Lower temperature for more consistent, analytical responses
    )
    
    content = response.choices[0].message.content
    
    # Parse JSON from response
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]
    
    data = json.loads(content.strip())
    
    decisions = [
        InvestmentDecision(
            company=d["company"],
            ticker=d["ticker"],
            action=d["action"],
            shares=d["shares"],
            rationale=d["rationale"],
            confidence=d["confidence"],
            risk_assessment=d["risk_assessment"]
        )
        for d in data["decisions"]
    ]
    
    return GrokResponse(
        decisions=decisions,
        portfolio_risk_analysis=data.get("portfolio_risk_analysis", ""),
        available_capital=available_capital
    )


if __name__ == "__main__":
    # Test with sample data
    from models import CompanyPick, FundamentalData
    
    test_picks = [
        CompanyPick("NVIDIA", "NVDA", "AI leader", "Record earnings")
    ]
    test_fundamentals = [
        FundamentalData(
            company="NVIDIA", ticker="NVDA", pe_ratio=65.0,
            cash_flow=15000, revenue=60000, market_cap=1200,
            debt_to_equity=0.4, earnings_growth=125.0, dividend_yield=0.03
        )
    ]
    
    result = make_investment_decision(
        test_picks, test_fundamentals, 10000.0, {}
    )
    print(result.to_json())
