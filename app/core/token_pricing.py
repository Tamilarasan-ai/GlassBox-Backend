"""
Token Usage Calculator - Gemini API Pricing
"""
from typing import Dict, Any


class TokenPricing:
    """
    Gemini API Pricing (as of Jan 2026)
    Source: https://ai.google.dev/pricing
    """
    
    # Pricing per 1 million tokens (USD)
    MODELS = {
        "gemini-2.0-flash-exp": {
            "input": 0.0,  # Free tier
            "output": 0.0,  # Free tier
            "cached_input": 0.0
        },
        "gemini-2.0-flash": {
            "input": 0.075,
            "output": 0.30,
            "cached_input": 0.01875  # 75% discount
        },
        "gemini-1.5-flash": {
            "input": 0.075,
            "output": 0.30,
            "cached_input": 0.01875
        },
        "gemini-1.5-pro": {
            "input": 1.25,
            "output": 5.00,
            "cached_input": 0.3125
        },
        "gemini-2.5-flash": {
            "input": 0.075,
            "output": 0.30,
            "cached_input": 0.01875
        },
    }
    
    @classmethod
    def calculate_cost(
        cls,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0
    ) -> Dict[str, float]:
        """
        Calculate cost for token usage
        
        Args:
            model_name: Gemini model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cached_tokens: Number of cached input tokens
            
        Returns:
            Dict with input_cost, output_cost, total_cost in USD
        """
        
        # Get pricing for model (default to gemini-1.5-flash if unknown)
        pricing = cls.MODELS.get(model_name, cls.MODELS["gemini-1.5-flash"])
        
        # Calculate costs (pricing is per 1M tokens)
        regular_input_tokens = input_tokens - cached_tokens
        
        input_cost = (regular_input_tokens / 1_000_000) * pricing["input"]
        cached_cost = (cached_tokens / 1_000_000) * pricing["cached_input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        total_input_cost = input_cost + cached_cost
        total_cost = total_input_cost + output_cost
        
        return {
            "input_cost_usd": round(total_input_cost, 6),
            "output_cost_usd": round(output_cost, 6),
            "total_cost_usd": round(total_cost, 6),
        }
    
    @classmethod
    def estimate_monthly_cost(
        cls,
        model_name: str,
        avg_input_tokens: int,
        avg_output_tokens: int,
        requests_per_day: int
    ) -> Dict[str, Any]:
        """
        Estimate monthly costs based on usage patterns
        
        Returns:
            Dict with daily, monthly costs and request counts
        """
        
        daily_cost = cls.calculate_cost(
            model_name,
            avg_input_tokens * requests_per_day,
            avg_output_tokens * requests_per_day
        )
        
        return {
            "daily_requests": requests_per_day,
            "monthly_requests": requests_per_day * 30,
            "daily_cost_usd": daily_cost["total_cost_usd"],
            "monthly_cost_usd": round(daily_cost["total_cost_usd"] * 30, 2),
            "per_request_cost_usd": round(
                daily_cost["total_cost_usd"] / requests_per_day, 6
            )
        }
