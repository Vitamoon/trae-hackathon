import streamlit as st
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any

# Import our data processing and analysis modules
from data_processor import DataProcessor
from user_analyzer import UserAnalyzer
from recommendation_engine import RecommendationEngine

# Set page configuration
st.set_page_config(page_title="Investment Recommendation System", layout="wide")

# Initialize components
data_processor = DataProcessor()
user_analyzer = UserAnalyzer()
recommendation_engine = RecommendationEngine()

# App title and description
st.title("Investment Recommendation System")
st.markdown("""
This application demonstrates how Twitter and Web3 data is processed to generate investment recommendations.
Select a user to view their data and recommendations.
""")

# Get all available users
all_users = data_processor.get_all_users()

# User selection sidebar
with st.sidebar:
    st.header("User Selection")
    selected_user_id = st.selectbox("Select a user", all_users)
    include_friends = st.checkbox("Include friend data for recommendations", value=True)
    max_recommendations = st.slider("Maximum number of recommendations", 1, 10, 5)

# Load user data
try:
    user_data = data_processor.load_user_data(selected_user_id)
    
    # Load friend data for network analysis
    friend_data = data_processor.load_friend_data(user_data) if include_friends else []
    
    # Generate performance metrics for landing page
    user_performances = user_analyzer.analyze_performances(user_data, friend_data)
    
    # Generate recommendations for summary
    recommendations = recommendation_engine.generate_recommendations(
        user_data,
        friend_data,
        user_performances,
        max_recommendations=max_recommendations
    )
    
    # Generate AI summary
    portfolio_summary = recommendation_engine.generate_summary(user_data, recommendations)
    
    # Display user information
    st.header(f"User: {user_data['twitter_data']['username']} ({user_data['twitter_data']['handle']})")
    
    # Landing Page - Network Position and Portfolio Overview
    st.subheader("Your Investment Network Overview")
    
    # Create columns for the landing page layout
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # AI-generated portfolio summary
        st.markdown("### AI-Generated Portfolio Summary")
        st.markdown(portfolio_summary)
        
        # Recent news from friends
        st.markdown("### Recent Activity in Your Network")
        
        # Extract recent activities from friends
        recent_activities = []
        for friend in friend_data[:5]:  # Limit to 5 friends
            username = friend['twitter_data']['username']
            # Get most recent trade
            if friend['web3_data']['recent_trades']:
                recent_trade = friend['web3_data']['recent_trades'][0]
                recent_activities.append({
                    "username": username,
                    "action": f"{recent_trade['action'].upper()} {recent_trade['asset']}",
                    "value": recent_trade['value_usd'],
                    "timestamp": recent_trade['timestamp']
                })
        
        if recent_activities:
            activities_df = pd.DataFrame(recent_activities)
            activities_df['timestamp'] = pd.to_datetime(activities_df['timestamp'])
            activities_df = activities_df.sort_values('timestamp', ascending=False)
            
            for _, activity in activities_df.iterrows():
                st.markdown(f"**{activity['username']}** {activity['action']} worth ${activity['value']:,.2f}")
        else:
            st.info("No recent activities from your network.")
    
    with col2:
        # Network comparison visualization
        st.markdown("### Your Position in the Network")
        
        # Create a dataframe for network comparison
        network_data = []
        for performer in user_performances:
            is_current_user = performer['user_id'] == user_data['user_id']
            network_data.append({
                "Username": performer.get("username", "Unknown"),
                "Total Profit/Loss": performer.get("total_profit_loss", 0),
                "Holdings Value": performer.get("holdings_value", 0),
                "Is Current User": is_current_user
            })
        
        network_df = pd.DataFrame(network_data)
        
        # Create a scatter plot for network comparison
        fig = px.scatter(
            network_df,
            x="Holdings Value",
            y="Total Profit/Loss",
            size=[20 if is_user else 10 for is_user in network_df["Is Current User"]],
            color="Is Current User",
            hover_name="Username",
            title="Your Position vs. Network",
            color_discrete_map={True: "#cf5ce6", False: "#9e9e9e"},
            height=300
        )
        # Add annotations to highlight the current user
        current_user_data = network_df[network_df["Is Current User"] == True]
        if not current_user_data.empty:
            fig.add_annotation(
                x=current_user_data["Holdings Value"].values[0],
                y=current_user_data["Total Profit/Loss"].values[0],
                text="You are here",
                showarrow=True,
                arrowhead=1,
                ax=0,
                ay=-40
            )
        st.plotly_chart(fig, use_container_width=True)
        
        # Portfolio composition
        st.markdown("### Your Portfolio Composition")
        
        # Process holdings data for pie chart
        holdings = user_data['web3_data']['holdings']
        if holdings:
            holdings_data = []
            for asset, details in holdings.items():
                holdings_data.append({
                    "Asset": asset,
                    "Value (USD)": details.get("value_usd", 0)
                })
            
            holdings_df = pd.DataFrame(holdings_data)
            
            # Create a pie chart for holdings distribution
            fig = px.pie(
                holdings_df, 
                values="Value (USD)", 
                names="Asset",
                title="Holdings Distribution",
                height=300,
                color_discrete_sequence=px.colors.sequential.Purp
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No holdings data available.")
    
    # Display key metrics
    profit_loss = user_data['web3_data']['profit_loss']
    if profit_loss:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Portfolio Value", f"${sum(holding['value_usd'] for holding in user_data['web3_data']['holdings'].values()):,.2f}")
        with col2:
            st.metric("Total Profit/Loss", f"${profit_loss.get('total', 0):,.2f}")
        with col3:
            # Calculate user's rank in network
            user_rank = next((i+1 for i, perf in enumerate(user_performances) if perf['user_id'] == user_data['user_id']), 0)
            st.metric("Your Network Rank", f"#{user_rank} of {len(user_performances)}")
        with col4:
            # Get top asset recommendation
            top_rec = recommendations[0] if recommendations else None
            if top_rec:
                st.metric("Top Recommendation", f"{top_rec['action'].upper()} {top_rec['asset']}")
            else:
                st.metric("Top Recommendation", "None available")
    
    st.markdown("---")
    
    # Create tabs for detailed sections
    tab1, tab2, tab3, tab4 = st.tabs(["Twitter Data", "Web3 Holdings", "Recent Trades", "Recommendations"])
    
    # Tab 1: Twitter Data
    with tab1:
        st.subheader("Twitter Activity")
        
        # Display tweets in a table
        if user_data['twitter_data']['tweets']:
            tweets_df = pd.DataFrame(user_data['twitter_data']['tweets'])
            
            # Clean up the dataframe for display
            if 'text' in tweets_df.columns:
                # Select and reorder columns for display
                display_columns = ['text', 'date', 'likes', 'retweets']
                display_columns = [col for col in display_columns if col in tweets_df.columns]
                
                st.dataframe(tweets_df[display_columns], use_container_width=True)
                
                # Create a bar chart for likes and retweets
                if 'likes' in tweets_df.columns and 'retweets' in tweets_df.columns:
                    engagement_df = tweets_df[['likes', 'retweets']].head(10)
                    
                    # Create a bar chart
                    fig = px.bar(
                        engagement_df, 
                        title="Engagement for Last 10 Tweets",
                        labels={"value": "Count", "variable": "Metric"},
                        height=400,
                        color_discrete_sequence=["#cf5ce6"]
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No tweets found for this user.")
    
    # Tab 2: Web3 Holdings
    with tab2:
        st.subheader("Current Holdings")
        
        # Process holdings data
        holdings = user_data['web3_data']['holdings']
        if holdings:
            holdings_data = []
            for asset, details in holdings.items():
                holdings_data.append({
                    "Asset": asset,
                    "Amount": details.get("amount", 0),
                    "Value (USD)": details.get("value_usd", 0),
                    "Is NFT": details.get("is_nft", False),
                    "Is Testnet": details.get("is_testnet", False)
                })
            
            holdings_df = pd.DataFrame(holdings_data)
            
            # Display holdings table
            st.dataframe(holdings_df, use_container_width=True)
            
            # Create a pie chart for holdings distribution
            fig = px.pie(
                holdings_df, 
                values="Value (USD)", 
                names="Asset",
                title="Holdings Distribution by Value",
                height=500,
                color_discrete_sequence=px.colors.sequential.Purp
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Display profit/loss information
            profit_loss = user_data['web3_data']['profit_loss']
            if profit_loss:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Profit/Loss", f"${profit_loss.get('total', 0):,.2f}")
                with col2:
                    st.metric("Realized Profit/Loss", f"${profit_loss.get('realized', 0):,.2f}")
                with col3:
                    st.metric("Unrealized Profit/Loss", f"${profit_loss.get('unrealized', 0):,.2f}")
        else:
            st.info("No holdings data found for this user.")
    
    # Tab 3: Recent Trades
    with tab3:
        st.subheader("Recent Trading Activity")
        
        # Process recent trades
        recent_trades = user_data['web3_data']['recent_trades']
        if recent_trades:
            trades_df = pd.DataFrame(recent_trades)
            
            # Display trades table
            st.dataframe(trades_df, use_container_width=True)
            
            # Create a timeline of trades
            if 'timestamp' in trades_df.columns and 'value_usd' in trades_df.columns:
                # Convert timestamp to datetime
                trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
                
                # Create separate dataframes for buy and sell trades
                buy_trades = trades_df[trades_df['action'] == 'buy']
                sell_trades = trades_df[trades_df['action'] == 'sell']
                
                # Create a scatter plot for trades
                fig = go.Figure()
                
                # Add buy trades
                if not buy_trades.empty:
                    fig.add_trace(go.Scatter(
                        x=buy_trades['timestamp'],
                        y=buy_trades['value_usd'],
                        mode='markers',
                        name='Buy',
                        marker=dict(color='#cf5ce6', size=10)
                    ))
                
                # Add sell trades
                if not sell_trades.empty:
                    fig.add_trace(go.Scatter(
                        x=sell_trades['timestamp'],
                        y=sell_trades['value_usd'],
                        mode='markers',
                        name='Sell',
                        marker=dict(color='#ff9999', size=10)
                    ))
                
                fig.update_layout(
                    title="Recent Trading Activity",
                    xaxis_title="Date",
                    yaxis_title="Value (USD)",
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No recent trades found for this user.")
    
    # Tab 4: Recommendations
    with tab4:
        st.subheader("Investment Recommendations")
        
        # Load friend data if requested
        if include_friends:
            friend_data = data_processor.load_friend_data(user_data)
            st.info(f"Including data from {len(friend_data)} friends for recommendations.")
        else:
            friend_data = []
            st.info("Friend data not included in recommendations.")
        
        # Generate performance metrics
        user_performances = user_analyzer.analyze_performances(user_data, friend_data)
        
        # Generate recommendations
        recommendations = recommendation_engine.generate_recommendations(
            user_data,
            friend_data,
            user_performances,
            max_recommendations=max_recommendations
        )
        
        # Display recommendations
        if recommendations:
            for i, rec in enumerate(recommendations):
                with st.expander(f"{i+1}. {rec['action'].upper()} {rec['asset']} (Confidence: {rec['confidence_score']:.2f})"):
                    st.write(f"**Reasoning:** {rec['reasoning']}")
                    st.write(f"**Supporting Users:** {', '.join(rec['supporting_users'])}")
        else:
            st.warning("No recommendations generated. Try including friend data or adjusting the confidence threshold.")
        
        # Display top performers
        st.subheader("Top Performers")
        top_performers = user_analyzer.identify_top_performers(user_performances)
        
        if top_performers:
            # Create a dataframe for display
            performers_data = []
            for performer in top_performers:
                performers_data.append({
                    "Username": performer.get("username", "Unknown"),
                    "Total Profit/Loss": performer.get("total_profit_loss", 0),
                    "Holdings Value": performer.get("holdings_value", 0),
                    "Social Influence": performer.get("social_influence_score", 0)
                })
            
            performers_df = pd.DataFrame(performers_data)
            
            # Display table
            st.dataframe(performers_df, use_container_width=True)
            
            # Create a bar chart for profit/loss comparison
            fig = px.bar(
                performers_df,
                x="Username",
                y="Total Profit/Loss",
                title="Profit/Loss Comparison",
                height=400,
                color_discrete_sequence=["#cf5ce6"]
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No performance data available.")

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.info("Please select a different user or check if the data files exist.")

# Footer
st.markdown("---")
st.markdown("""
**Note:** This is a demonstration application showing how the data processor parses and structures Twitter and Web3 data.
The recommendations are generated based on the parsed data and are for demonstration purposes only.
""")