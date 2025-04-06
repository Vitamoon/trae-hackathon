import os
import json
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional

# Load environment variables
load_dotenv()
PINAI_API_KEY = os.getenv("PINAI_API_KEY")
PINAI_WALLET = os.getenv("PINAI_WALLET")

if not PINAI_API_KEY or not PINAI_WALLET:
    raise ValueError("PINAI_API_KEY and PINAI_WALLET must be set in .env file")

# Initialize FastAPI app
app = FastAPI(title="SocialTradeInsight", description="A PinAI agent for personalized investment recommendations based on social and Web3 data")

# Define data models
class UserData(BaseModel):
    username: str
    twitter_data_path: Optional[str] = None
    web3_data_path: Optional[str] = None

class RecommendationRequest(BaseModel):
    user_id: str
    include_friends: bool = True
    max_recommendations: int = 5

class TradeInfo(BaseModel):
    asset: str
    action: str  # buy or sell
    amount: float
    value_usd: float
    timestamp: str

class UserPerformance(BaseModel):
    username: str
    total_profit_loss: float
    realized_profit_loss: float
    unrealized_profit_loss: float
    recent_trades: List[TradeInfo]
    holdings_value: float

class InvestmentRecommendation(BaseModel):
    asset: str
    action: str  # buy or sell
    confidence_score: float
    reasoning: str
    supporting_users: List[str]

class RecommendationResponse(BaseModel):
    recommendations: List[InvestmentRecommendation]
    user_rankings: List[UserPerformance]
    analysis_summary: str

# Main application logic will be implemented in the following files
from src.data_processor import DataProcessor
from src.recommendation_engine import RecommendationEngine
from src.user_analyzer import UserAnalyzer

# API endpoints
@app.get("/")
async def root():
    return {"message": "Welcome to SocialTradeInsight - Your personalized investment recommendation agent"}

@app.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    try:
        # Initialize components
        data_processor = DataProcessor()
        user_analyzer = UserAnalyzer()
        recommendation_engine = RecommendationEngine()
        
        # Process user data and generate recommendations
        user_data = data_processor.load_user_data(request.user_id)
        if request.include_friends:
            friend_data = data_processor.load_friend_data(user_data)
        else:
            friend_data = []
            
        user_performances = user_analyzer.analyze_performances(user_data, friend_data)
        recommendations = recommendation_engine.generate_recommendations(
            user_data, 
            friend_data,
            user_performances,
            max_recommendations=request.max_recommendations
        )
        
        analysis_summary = recommendation_engine.generate_summary(user_data, recommendations)
        
        return RecommendationResponse(
            recommendations=recommendations,
            user_rankings=user_performances,
            analysis_summary=analysis_summary
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)