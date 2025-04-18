import os
import json
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import httpx

# Import our custom modules
from src.data_processor import DataProcessor
from src.recommendation_engine import RecommendationEngine
from src.user_analyzer import UserAnalyzer
from pinai_agent_sdk import PinAIClient

# Load environment variables
load_dotenv()
PINAI_API_KEY = os.getenv("PINAI_API_KEY")
PINAI_WALLET = os.getenv("PINAI_WALLET")

if not PINAI_API_KEY or not PINAI_WALLET:
    raise ValueError("PINAI_API_KEY and PINAI_WALLET must be set in .env file")

class SocialTradeInsight:
    """PinAI agent for personalized investment recommendations based on social and Web3 data."""
    
    def __init__(self, api_key: str, wallet_address: str):
        """Initialize the SocialTradeInsight agent.
        
        Args:
            api_key: PinAI API key
            wallet_address: User's wallet address
        """
        self.api_key = api_key
        self.wallet_address = wallet_address
        self.data_processor = DataProcessor()
        self.user_analyzer = UserAnalyzer()
        self.recommendation_engine = RecommendationEngine()
        self.pinai_client = PinAIClient(api_key)

        print(f"SocialTradeInsight agent initialized with wallet: {wallet_address[:6]}...{wallet_address[-4:]}")
    
    def analyze_user(self, user_id: str, include_friends: bool = True) -> Dict[str, Any]:
        """Analyze a user's data and generate personalized recommendations.
        
        Args:
            user_id: The user identifier
            include_friends: Whether to include friend data in the analysis
            
        Returns:
            Dictionary containing analysis results and recommendations
        """
        print(f"\nAnalyzing data for user: {user_id}")
        
        # Load user data
        try:
            user_data = self.data_processor.load_user_data(user_id)
            print(f"Loaded Twitter and Web3 data for {user_data['twitter_data']['username']}")
        except Exception as e:
            print(f"Error loading user data: {str(e)}")
            return {"error": str(e)}
        
        # Load friend data if requested
        friend_data = []
        if include_friends:
            try:
                friend_data = self.data_processor.load_friend_data(user_data)
                print(f"Loaded data for {len(friend_data)} connections")
            except Exception as e:
                print(f"Warning: Error loading friend data: {str(e)}")
        
        # Analyze user performances
        user_performances = self.user_analyzer.analyze_performances(user_data, friend_data)
        print(f"Analyzed performance metrics for {len(user_performances)} users")
        
        # Generate recommendations
        recommendations = self.recommendation_engine.generate_recommendations(
            user_data,
            friend_data,
            user_performances,
            max_recommendations=5
        )
        print(f"Generated {len(recommendations)} investment recommendations")
        
        # Generate summary
        summary = self.recommendation_engine.generate_summary(user_data, recommendations)
        
        # Prepare result
        result = {
            "user": {
                "username": user_data["twitter_data"]["username"],
                "user_id": user_id,
                "holdings_value": sum(holding["value_usd"] for holding in user_data["web3_data"]["holdings"].values()),
                "profit_loss": user_data["web3_data"]["profit_loss"]
            },
            "recommendations": recommendations,
            "user_rankings": user_performances[:5],  # Top 5 users by performance
            "summary": summary
        }
        
        return result
    
    def register_with_pinai(self) -> Dict[str, Any]:
        response = self.pinai_client.register_agent(
            name="SocialTradeInsight",
            description="A PinAI agent for personalized investment recommendations based on social and Web3 data",
            capabilities=[
                "social_media_analysis",
                "web3_transaction_analysis",
                "investment_recommendations",
                "performance_comparison"
            ],
            wallet_address=self.wallet_address
        )
        return response
        
    def query_agent_capabilities(self, agent_id: str) -> Dict[str, Any]:
        """Query another agent's capabilities using the PinAI SDK.
        
        Args:
            agent_id: The ID of the agent to query
            
        Returns:
            Dictionary containing the agent's capabilities and metadata
        """
        return self.pinai_client.query_agent(agent_id)
        
    def share_analysis_with_agent(self, agent_id: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Share analysis results with another PinAI agent.
        
        Args:
            agent_id: The ID of the agent to share with
            analysis_data: The analysis data to share
            
        Returns:
            Response from the agent receiving the data
        """
        return self.pinai_client.send_to_agent(
            agent_id=agent_id,
            message_type="analysis_results",
            payload=analysis_data
        )
        
    def get_available_agents(self, capability_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of available agents, optionally filtered by capability.
        
        Args:
            capability_filter: Optional capability to filter agents by
            
        Returns:
            List of agent metadata dictionaries
        """
        return self.pinai_client.list_agents(capability=capability_filter)

# Demo function to showcase the agent's capabilities
def run_demo():
    """Run a demonstration of the SocialTradeInsight agent."""
    print("\n===== SocialTradeInsight: PinAI Investment Recommendation Agent =====\n")
    
    # Initialize the agent
    agent = SocialTradeInsight(PINAI_API_KEY, PINAI_WALLET)
    
    # Register with PinAI
    registration = agent.register_with_pinai()
    print(f"Registration status: {registration['status']}")
    print(f"Agent ID: {registration['agent_id']}")
    print(f"Message: {registration['message']}\n")
    
    # Get available users
    data_processor = DataProcessor()
    available_users = data_processor.get_all_users()
    
    print(f"Available users for analysis: {', '.join(available_users)}\n")
    
    # Analyze a sample user
    sample_user = "JohnDefi"  # Can be changed to any available user
    analysis_result = agent.analyze_user(sample_user, include_friends=True)
    
    # Display results
    print("\n===== Analysis Results =====\n")
    print(f"User: {analysis_result['user']['username']}")
    print(f"Portfolio Value: ${analysis_result['user']['holdings_value']:,.2f}")
    print(f"Total Profit/Loss: ${analysis_result['user']['profit_loss'].get('total', 0):,.2f}\n")
    
    print("Top Performing Users in Network:")
    for i, user in enumerate(analysis_result['user_rankings'][:3], 1):
        print(f"{i}. {user['username']} - ${user['total_profit_loss']:,.2f} profit/loss")
    
    print("\nInvestment Recommendations:")
    for i, rec in enumerate(analysis_result['recommendations'], 1):
        print(f"{i}. {rec['action'].upper()} {rec['asset']} - Confidence: {rec['confidence_score']:.2f}")
        print(f"   Reasoning: {rec['reasoning']}")
        print(f"   Supporting Users: {', '.join(rec['supporting_users'])}\n")
    
    print("\n===== Summary =====\n")
    print(analysis_result['summary'])
    print("\n===== End of Demo =====\n")

if __name__ == "__main__":
    run_demo()