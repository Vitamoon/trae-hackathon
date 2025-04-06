import os
import re
import json
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class RecommendationEngine:
    """Generates personalized investment recommendations based on user and friend data."""
    
    def __init__(self, confidence_threshold: float = 0.6):
        """Initialize the RecommendationEngine.
        
        Args:
            confidence_threshold: Minimum confidence score for recommendations
        """
        self.confidence_threshold = confidence_threshold
    
    def generate_recommendations(self, 
                                user_data: Dict[str, Any], 
                                friend_data: List[Dict[str, Any]],
                                user_performances: List[Dict[str, Any]],
                                max_recommendations: int = 5) -> List[Dict[str, Any]]:
        """Generate personalized investment recommendations.
        
        Args:
            user_data: The main user's data
            friend_data: Data for the user's friends/connections
            user_performances: Performance metrics for all users
            max_recommendations: Maximum number of recommendations to generate
            
        Returns:
            List of investment recommendations
        """
        # Extract user's current holdings and recent trades
        user_holdings = user_data["web3_data"]["holdings"]
        user_recent_trades = user_data["web3_data"]["recent_trades"]
        
        # Identify top performing friends
        top_performers = [p for p in user_performances if p["user_id"] != user_data["user_id"]][:5]
        
        # Analyze trending assets among top performers
        trending_assets = self._analyze_trending_assets(top_performers)
        
        # Generate recommendations based on trending assets and user's portfolio
        recommendations = []
        
        for asset, data in trending_assets.items():
            # Skip if confidence score is below threshold
            if data["confidence_score"] < self.confidence_threshold:
                continue
            
            # Determine if user already holds this asset
            user_holds_asset = asset in user_holdings
            user_holding_amount = user_holdings.get(asset, {}).get("amount", 0) if user_holds_asset else 0
            
            # Check if user has recently traded this asset
            user_recent_asset_trades = [t for t in user_recent_trades if t["asset"] == asset]
            
            # Determine recommendation action based on trend and user's portfolio
            action = self._determine_action(asset, data, user_holds_asset, user_recent_asset_trades)
            
            # Generate reasoning for the recommendation
            reasoning = self._generate_reasoning(asset, data, action, user_holds_asset)
            
            # Create recommendation object
            recommendation = {
                "asset": asset,
                "action": action,
                "confidence_score": data["confidence_score"],
                "reasoning": reasoning,
                "supporting_users": data["supporting_users"]
            }
            
            recommendations.append(recommendation)
            
            # Limit to max_recommendations
            if len(recommendations) >= max_recommendations:
                break
        
        return recommendations
    
    def _analyze_trending_assets(self, top_performers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trending assets among top performing users.
        
        Args:
            top_performers: List of top performing users with their metrics
            
        Returns:
            Dictionary of trending assets with analysis data
        """
        asset_data = {}
        
        # Collect recent trades from top performers
        for performer in top_performers:
            for trade in performer["recent_trades"]:
                asset = trade["asset"]
                
                if asset not in asset_data:
                    asset_data[asset] = {
                        "buy_count": 0,
                        "sell_count": 0,
                        "total_volume": 0,
                        "supporting_users": [],
                        "recent_price_trend": 0,
                        "social_mentions": 0
                    }
                
                # Update trade counts and volume
                asset_data[asset][f"{trade['action']}_count"] += 1
                asset_data[asset]["total_volume"] += trade["value_usd"]
                
                # Add supporting user if not already in the list
                if performer["username"] not in asset_data[asset]["supporting_users"]:
                    asset_data[asset]["supporting_users"].append(performer["username"])
        
        # Calculate additional metrics for each asset
        for asset, data in asset_data.items():
            # Calculate buy/sell ratio (>1 means more buys than sells)
            buy_sell_ratio = data["buy_count"] / max(1, data["sell_count"])
            
            # Calculate confidence score based on multiple factors
            confidence_factors = [
                min(1.0, data["total_volume"] / 10000),  # Volume factor (max 1.0)
                min(1.0, len(data["supporting_users"]) / 3),  # User diversity factor
                min(1.0, (buy_sell_ratio if buy_sell_ratio <= 3 else 3) / 3)  # Buy/sell ratio factor (capped at 3)
            ]
            
            data["buy_sell_ratio"] = buy_sell_ratio
            data["confidence_score"] = sum(confidence_factors) / len(confidence_factors)
        
        # Sort assets by confidence score
        sorted_assets = sorted(asset_data.items(), key=lambda x: x[1]["confidence_score"], reverse=True)
        
        return dict(sorted_assets)
    
    def _determine_action(self, 
                         asset: str, 
                         asset_data: Dict[str, Any], 
                         user_holds_asset: bool,
                         user_recent_asset_trades: List[Dict[str, Any]]) -> str:
        """Determine the recommended action for an asset.
        
        Args:
            asset: The asset symbol
            asset_data: Analysis data for the asset
            user_holds_asset: Whether the user already holds this asset
            user_recent_asset_trades: User's recent trades for this asset
            
        Returns:
            Recommended action ("buy", "sell", or "hold")
        """
        # Check if there's a strong buy trend among top performers
        strong_buy_trend = asset_data["buy_sell_ratio"] > 1.5
        
        # Check if there's a strong sell trend among top performers
        strong_sell_trend = asset_data["buy_sell_ratio"] < 0.7
        
        # Check if user has recently bought this asset
        recent_buy = any(t["action"] == "buy" for t in user_recent_asset_trades)
        
        # Check if user has recently sold this asset
        recent_sell = any(t["action"] == "sell" for t in user_recent_asset_trades)
        
        # Determine action based on trends and user's portfolio
        if strong_buy_trend and not recent_buy:
            return "buy"
        elif strong_sell_trend and user_holds_asset and not recent_sell:
            return "sell"
        elif user_holds_asset:
            return "hold"
        else:
            return "buy" if asset_data["confidence_score"] > 0.7 else "watch"
    
    def _generate_reasoning(self, 
                           asset: str, 
                           asset_data: Dict[str, Any], 
                           action: str,
                           user_holds_asset: bool) -> str:
        """Generate reasoning for a recommendation.
        
        Args:
            asset: The asset symbol
            asset_data: Analysis data for the asset
            action: Recommended action
            user_holds_asset: Whether the user already holds this asset
            
        Returns:
            Reasoning text for the recommendation
        """
        supporting_users_count = len(asset_data["supporting_users"])
        buy_count = asset_data["buy_count"]
        sell_count = asset_data["sell_count"]
        
        if action == "buy":
            if user_holds_asset:
                return f"{supporting_users_count} successful traders in your network have recently increased their {asset} positions. There have been {buy_count} buys vs {sell_count} sells among top performers, suggesting positive momentum."
            else:
                return f"{supporting_users_count} successful traders in your network have recently added {asset} to their portfolios. With {buy_count} buys vs {sell_count} sells among top performers, this could be a good entry opportunity."
        
        elif action == "sell":
            return f"There's a selling trend for {asset} among {supporting_users_count} successful traders in your network. With {sell_count} sells vs {buy_count} buys, it might be time to consider taking profits."
        
        elif action == "hold":
            if buy_count > sell_count:
                return f"Continue holding {asset} as {supporting_users_count} successful traders in your network maintain their positions. The buy/sell ratio of {asset_data['buy_sell_ratio']:.2f} indicates stable interest."
            else:
                return f"While some selling of {asset} is occurring, the overall confidence score of {asset_data['confidence_score']:.2f} suggests holding your position for now. Monitor for changes in trend."
        
        else:  # watch
            return f"Consider adding {asset} to your watchlist. {supporting_users_count} successful traders in your network have shown interest, but the confidence score of {asset_data['confidence_score']:.2f} suggests waiting for a better entry point."
    
    def generate_summary(self, user_data: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> str:
        """Generate a summary of the recommendations and analysis.
        
        Args:
            user_data: The main user's data
            recommendations: List of generated recommendations
            
        Returns:
            Summary text
        """
        username = user_data["twitter_data"]["username"]
        total_holdings_value = sum(holding["value_usd"] for holding in user_data["web3_data"]["holdings"].values())
        profit_loss = user_data["web3_data"]["profit_loss"].get("total", 0)
        
        # Count recommendation types
        action_counts = {}
        for rec in recommendations:
            action = rec["action"]
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # Generate summary text
        summary = f"Investment Recommendations for {username}\n\n"
        summary += f"Based on the analysis of your portfolio (${total_holdings_value:,.2f} total value) "
        summary += f"and the trading patterns of your network, SocialTradeInsight has generated "
        summary += f"{len(recommendations)} personalized recommendations.\n\n"
        
        if "buy" in action_counts:
            summary += f"• {action_counts['buy']} buy recommendations for new opportunities\n"
        if "sell" in action_counts:
            summary += f"• {action_counts['sell']} sell recommendations to optimize your portfolio\n"
        if "hold" in action_counts:
            summary += f"• {action_counts['hold']} hold recommendations for your existing assets\n"
        if "watch" in action_counts:
            summary += f"• {action_counts['watch']} assets to add to your watchlist\n"
        
        summary += f"\nThese recommendations are based on the analysis of successful traders in your network, "
        summary += f"taking into account their recent trading activity and performance metrics.\n"
        
        return summary