# API Keys Configuration
# Replace placeholder values with your actual API keys

API_KEYS = {
    "ALPACA": {
        "API_KEY": "your_alpaca_api_key",
        "API_SECRET": "your_alpaca_secret_key",
        "BASE_URL": "https://paper-api.alpaca.markets"  # Use paper trading URL for testing
    },
    "POLYGON": {
        "API_KEY": "your_polygon_api_key"
    },
    "OPENAI": {
        "API_KEY": "your_openai_api_key"
    },
    "TRADIER": {
        "API_KEY": "your_tradier_api_key",
        "ACCOUNT_ID": "your_tradier_account_id"
    }
}


def get_key(service: str, key_name: str = "API_KEY") -> str:
    """
    Retrieve an API key for a given service.
    
    Args:
        service: The service name (e.g., "ALPACA", "POLYGON")
        key_name: The specific key to retrieve (default: "API_KEY")
    
    Returns:
        The API key string
    """
    if service not in API_KEYS:
        raise KeyError(f"Service '{service}' not found in API_KEYS")
    if key_name not in API_KEYS[service]:
        raise KeyError(f"Key '{key_name}' not found for service '{service}'")
    return API_KEYS[service][key_name]
