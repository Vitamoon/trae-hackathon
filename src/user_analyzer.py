import os
import re
import json
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from datetime import datetime

class UserAnalyzer:
    """Analyzes user performance based on Web3 data and social interactions."""
    
    def __init__(self):
        """Initialize the UserAnalyzer."""
        pass
    
    def analyze_performances(self, user_data: Dict[str, Any], friend_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze performance metrics for the user and their friends.
        
        Args:
            user_data: The main user's data
            friend_data: Data for the user's friends/connections
            
        Returns:
            List of performance metrics for each user, sorted by performance
        """
        # Combine user and friend data for analysis
        all_users_data = [user_data] + friend_data
        
        # Calculate performance metrics for each user
        performance_metrics = []
        for data in all_users_data:
            metrics = self._calculate_user_metrics(data)
            performance_metrics.append(metrics)
        
        # Sort by total profit/loss (descending)
        performance_metrics.sort(key=lambda x: x["total_profit_loss"], reverse=True)
        
        return performance_metrics
    
    def _calculate_user_metrics(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics for a single user.
        
        Args:
            user_data: User data containing Twitter and Web3 information
            
        Returns:
            Dictionary of performance metrics
        """
        web3_data = user_data["web3_data"]
        twitter_data = user_data["twitter_data"]
        
        # Extract basic metrics from Web3 data
        total_profit_loss = web3_data["profit_loss"].get("total", 0)
        realized_profit_loss = web3_data["profit_loss"].get("realized", 0)
        unrealized_profit_loss = web3_data["profit_loss"].get("unrealized", 0)
        
        # Calculate total holdings value
        holdings_value = sum(holding["value_usd"] for holding in web3_data["holdings"].values())
        
        # Process recent trades
        recent_trades = []
        for trade in web3_data["recent_trades"][:10]:  # Limit to 10 most recent trades
            recent_trades.append({
                "asset": trade["asset"],
                "action": trade["action"],
                "amount": trade["amount"],
                "value_usd": trade["value_usd"],
                "timestamp": trade["timestamp"]
            })
        
        # Calculate additional metrics
        trade_frequency = len(web3_data["recent_trades"])
        unique_assets_traded = len(set(trade["asset"] for trade in web3_data["recent_trades"]))
        avg_trade_value = sum(trade["value_usd"] for trade in web3_data["recent_trades"]) / max(1, trade_frequency)
        
        # Calculate social engagement metrics
        avg_likes = sum(tweet.get("likes", 0) for tweet in twitter_data["tweets"]) / max(1, len(twitter_data["tweets"]))
        avg_retweets = sum(tweet.get("retweets", 0) for tweet in twitter_data["tweets"]) / max(1, len(twitter_data["tweets"]))
        
        # Calculate success rate (percentage of profitable trades)
        buy_assets = {}
        sell_assets = {}
        for trade in web3_data["recent_trades"]:
            asset = trade["asset"]
            if trade["action"] == "buy":
                if asset not in buy_assets:
                    buy_assets[asset] = []
                buy_assets[asset].append({
                    "amount": trade["amount"],
                    "value": trade["value_usd"],
                    "price": trade["value_usd"] / max(0.000001, trade["amount"]),  # Prevent division by zero
                    "timestamp": trade["timestamp"]
                })
            elif trade["action"] == "sell":
                if asset not in sell_assets:
                    sell_assets[asset] = []
                sell_assets[asset].append({
                    "amount": trade["amount"],
                    "value": trade["value_usd"],
                    "price": trade["value_usd"] / max(0.000001, trade["amount"]),  # Prevent division by zero
                    "timestamp": trade["timestamp"]
                })
        
        # Combine metrics
        return {
            "username": twitter_data["username"],
            "user_id": user_data["user_id"],
            "total_profit_loss": total_profit_loss,
            "realized_profit_loss": realized_profit_loss,
            "unrealized_profit_loss": unrealized_profit_loss,
            "holdings_value": holdings_value,
            "recent_trades": recent_trades,
            "trade_frequency": trade_frequency,
            "unique_assets_traded": unique_assets_traded,
            "avg_trade_value": avg_trade_value,
            "avg_likes": avg_likes,
            "avg_retweets": avg_retweets,
            "social_influence_score": (avg_likes + avg_retweets * 2) / 3  # Simple weighted score
        }
    
    def identify_top_performers(self, performance_metrics: List[Dict[str, Any]], top_n: int = 3) -> List[Dict[str, Any]]:
        """Identify the top performing users based on profit/loss and other metrics.
        
        Args:
            performance_metrics: List of user performance metrics
            top_n: Number of top performers to return
            
        Returns:
            List of top performers with their metrics
        """
        # Sort by total profit/loss (descending)
        sorted_metrics = sorted(performance_metrics, key=lambda x: x["total_profit_loss"], reverse=True)
        
        return sorted_metrics[:top_n]
    
    def identify_trending_assets(self, performance_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify trending assets among users.
        
        Args:
            performance_metrics: List of user performance metrics
            
        Returns:
            Dictionary of trending assets with frequency and average performance
        """
        asset_data = {}
        
        # Collect data on all assets being traded
        for user_metrics in performance_metrics:
            for trade in user_metrics["recent_trades"]:
                asset = trade["asset"]
                if asset not in asset_data:
                    asset_data[asset] = {
                        "buy_count": 0,
                        "sell_count": 0,
                        "total_volume": 0,
                        "users_trading": set()
                    }
                
                asset_data[asset][f"{trade['action']}_count"] += 1
                asset_data[asset]["total_volume"] += trade["value_usd"]
                asset_data[asset]["users_trading"].add(user_metrics["user_id"])
        
        # Calculate additional metrics for each asset
        for asset, data in asset_data.items():
            data["net_buy_sell_ratio"] = data["buy_count"] / max(1, data["sell_count"])
            data["user_count"] = len(data["users_trading"])
            data["users_trading"] = list(data["users_trading"])  # Convert set to list for serialization
        
        # Sort assets by trading volume
        trending_assets = sorted(asset_data.items(), key=lambda x: x[1]["total_volume"], reverse=True)
        
        return dict(trending_assets)