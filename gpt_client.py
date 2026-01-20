"""
GPT Client for news research and company selection.
"""
import os
import json
from openai import OpenAI
from models import CompanyPick, GPTResponse


def get_gpt_client() -> OpenAI:
    """Initialize OpenAI client with API key from environment."""
    api_key = os.environ.get("gpt_main")
    if not api_key:
        raise ValueError("gpt_main environment variable not set")
    return OpenAI(api_key=api_key)


def research_companies() -> GPTResponse:
    """
    Use GPT to search news and current happenings.
    Returns 5 companies to invest in with rationale.
    """
    client = get_gpt_client()
    
    prompt = """You are a financial research analyst. Search through recent news and current market happenings.

Your task:
1. Identify 5 promising companies for potential investment based on recent positive news, market trends, or catalysts.
2. For each company, provide:
   - Company name
   - Stock ticker symbol
   - A brief rationale for why this company is a good investment opportunity
   - Summary of the relevant news driving your recommendation

Focus on:
- Companies with positive momentum
- Recent earnings beats or upgrades
- Industry tailwinds
- Product launches or strategic moves
- Undervalued opportunities

Return your response as a JSON object with the following structure:
{
    "picks": [
        {
            "company": "Company Name",
            "ticker": "TICK",
            "rationale": "Why this is a good investment",
            "news_summary": "Recent news driving this recommendation"
        }
    ]
}

Return ONLY the JSON object, no additional text."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a financial research analyst providing investment recommendations based on current news and market analysis. Always respond with valid JSON."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content
    data = json.loads(content)
    
    picks = [
        CompanyPick(
            company=p["company"],
            ticker=p["ticker"],
            rationale=p["rationale"],
            news_summary=p["news_summary"]
        )
        for p in data["picks"]
    ]
    
    return GPTResponse(picks=picks)


if __name__ == "__main__":
    # Test the client
    result = research_companies()
    print(result.to_json())
