# PinAI Social Trading Platform

![PinAI Logo](img/logo-pinai.png)

## Overview

PinAI is an AI-powered social trading platform that leverages Web3 and social media data to provide personalized investment recommendations. By analyzing trading patterns, social interactions, and market trends across your network, PinAI helps you make more informed investment decisions based on the collective intelligence of successful traders in your community.

## Key Features

- **Social Network Analysis**: Analyzes your connections' trading activities and social interactions to identify successful strategies
- **Performance Tracking**: Monitors and compares your portfolio performance against your network
- **AI-Powered Recommendations**: Generates personalized investment recommendations with confidence scores and reasoning
- **Trending Asset Identification**: Identifies which assets are gaining traction among top performers in your network
- **Portfolio Visualization**: Provides clear visual representations of your holdings and performance metrics
- **Real-time Activity Feed**: Shows recent trading activities from your network

## Technology Stack

- **Backend**: Python with FastAPI
- **Frontend**: Streamlit for interactive data visualization
- **Data Processing**: Pandas and NumPy for data analysis
- **Visualization**: Plotly for interactive charts
- **AI Components**: Custom recommendation engine and user analyzer

## Installation

### Prerequisites

- Python 3.8+
- Git

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/trae-hackathon.git
   cd trae-hackathon
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your API keys:
   ```
   PINAI_API_KEY=your_api_key_here
   PINAI_WALLET=your_wallet_address_here
   ```

## Usage

### Running the Streamlit App

```bash
python -m streamlit run src/streamlit_app.py
```

This will launch the web interface where you can:
- Select a user to analyze
- View portfolio composition and performance
- See your position in the network
- Get AI-generated investment recommendations
- Track recent activities in your network

### Using the API

You can also use the FastAPI backend directly:

```bash
uvicorn src.main:app --reload
```

Then access the API documentation at `http://localhost:8000/docs`

## Architecture

The platform consists of three main components:

### 1. Data Processor (`data_processor.py`)

Handles loading and processing of Twitter and Web3 data files. It extracts relevant information from text files containing social media posts and blockchain transaction data.

### 2. User Analyzer (`user_analyzer.py`)

Analyzes user performance based on Web3 data and social interactions. It calculates various metrics including:
- Total profit/loss
- Holdings value
- Trade frequency
- Social influence score

### 3. Recommendation Engine (`recommendation_engine.py`)

Generates personalized investment recommendations by:
- Analyzing trending assets among top performers
- Determining appropriate actions (buy, sell, hold, watch)
- Calculating confidence scores
- Providing reasoning for recommendations

### 4. PinAI Agent (`pinai_agent.py`)

Integrates all components and provides a high-level interface for analyzing users and generating recommendations.

## Data Structure

The platform uses two main types of data:

### Twitter Data

Contains user tweets, likes, retweets, and social interactions stored in text files in the `TwitterData` directory.

### Web3 Data

Contains blockchain transaction data including:
- Holdings (assets, amounts, values)
- Recent trades (buy/sell actions, timestamps, values)
- Profit/loss metrics (realized and unrealized)

Stored in text files in the `Web3Data` directory.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- PinAI for providing the underlying AI technology
- The Web3 and social media data providers