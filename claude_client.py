"""
Claude Client for fundamental analysis.
"""
import os
import json
import anthropic
from typing import List
from models import CompanyPick, FundamentalData, ClaudeResponse


def get_claude_client() -> anthropic.Anthropic:
    """Initialize Anthropic client with API key from environment."""
    api_key = os.environ.get("claude_main")
    if not api_key:
        raise ValueError("claude_main environment variable not set")
    return anthropic.Anthropic(api_key=api_key)


def analyze_fundamentals(picks: List[CompanyPick]) -> ClaudeResponse:
    """
    Use Claude to analyze fundamental data for the given companies.
    Returns fundamental metrics and analysis for each company.
    """
    client = get_claude_client()
    
    # Build input JSON for Claude
    input_data = {
        "companies": [
            {
                "company": p.company,
                "ticker": p.ticker,
                "rationale": p.rationale,
                "news_summary": p.news_summary
            }
            for p in picks
        ]
    }
    
    prompt = f"""You are a financial analyst specializing in fundamental analysis.

You have received the following companies selected for potential investment:

{json.dumps(input_data, indent=2)}

For each company, provide fundamental analysis including:
1. P/E Ratio (price-to-earnings)
2. Cash Flow (operating cash flow in millions)
3. Revenue (annual revenue in millions)
4. Market Cap (in billions)
5. Debt-to-Equity ratio
6. Earnings Growth (YoY percentage)
7. Dividend Yield (if applicable)
8. Any additional relevant metrics based on the news provided
9. Analysis notes connecting the fundamentals to the news/rationale

Return your response as a JSON object with the following structure:
{{
    "fundamentals": [
        {{
            "company": "Company Name",
            "ticker": "TICK",
            "pe_ratio": 25.5,
            "cash_flow": 5000,
            "revenue": 50000,
            "market_cap": 200,
            "debt_to_equity": 0.5,
            "earnings_growth": 15.5,
            "dividend_yield": 1.2,
            "additional_metrics": {{"metric_name": "value"}},
            "analysis_notes": "How fundamentals relate to the news and investment thesis"
        }}
    ]
}}

Use realistic market data. If you don't have exact figures, provide reasonable estimates based on the company's profile.
Return ONLY the JSON object, no additional text."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    content = response.content[0].text
    
    # Parse JSON from response (handle potential markdown code blocks)
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]
    
    data = json.loads(content.strip())
    
    fundamentals = [
        FundamentalData(
            company=f["company"],
            ticker=f["ticker"],
            pe_ratio=f.get("pe_ratio"),
            cash_flow=f.get("cash_flow"),
            revenue=f.get("revenue"),
            market_cap=f.get("market_cap"),
            debt_to_equity=f.get("debt_to_equity"),
            earnings_growth=f.get("earnings_growth"),
            dividend_yield=f.get("dividend_yield"),
            additional_metrics=f.get("additional_metrics", {}),
            analysis_notes=f.get("analysis_notes", "")
        )
        for f in data["fundamentals"]
    ]
    
    return ClaudeResponse(fundamentals=fundamentals)


if __name__ == "__main__":
    # Test with sample data
    test_picks = [
        CompanyPick(
            company="NVIDIA",
            ticker="NVDA",
            rationale="AI chip demand surge",
            news_summary="Record data center revenue"
        )
    ]
    result = analyze_fundamentals(test_picks)
    print(result.to_json())
