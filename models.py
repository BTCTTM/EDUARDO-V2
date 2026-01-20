"""
Data models for EDUARDO-V2 trading pipeline.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime
import json


@dataclass
class CompanyPick:
    """Company picked by GPT with rationale."""
    company: str
    ticker: str
    rationale: str
    news_summary: str


@dataclass
class GPTResponse:
    """Response from GPT containing 5 company picks."""
    picks: List[CompanyPick]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


@dataclass
class FundamentalData:
    """Fundamental data for a company from Claude."""
    company: str
    ticker: str
    pe_ratio: Optional[float]
    cash_flow: Optional[float]
    revenue: Optional[float]
    market_cap: Optional[float]
    debt_to_equity: Optional[float]
    earnings_growth: Optional[float]
    dividend_yield: Optional[float]
    additional_metrics: dict = field(default_factory=dict)
    analysis_notes: str = ""


@dataclass
class ClaudeResponse:
    """Response from Claude with fundamental analysis."""
    fundamentals: List[FundamentalData]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


@dataclass
class InvestmentDecision:
    """Investment decision from Grok."""
    company: str
    ticker: str
    action: str  # "BUY", "SELL", "HOLD"
    shares: int
    rationale: str
    confidence: float  # 0-1 scale
    risk_assessment: str


@dataclass
class GrokResponse:
    """Response from Grok with investment decisions."""
    decisions: List[InvestmentDecision]
    portfolio_risk_analysis: str
    available_capital: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


@dataclass
class TradeResult:
    """Result of a trade execution."""
    ticker: str
    shares: int
    action: str
    price: float
    total_value: float
    success: bool
    order_id: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
