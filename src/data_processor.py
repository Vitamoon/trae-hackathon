import os
import re
import json
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from datetime import datetime

class DataProcessor:
    """Handles loading and processing of Twitter and Web3 data files."""
    
    def __init__(self, twitter_data_dir: str = "TwitterData", web3_data_dir: str = "Web3Data"):
        """Initialize the DataProcessor with directories for data files.
        
        Args:
            twitter_data_dir: Directory containing Twitter data files
            web3_data_dir: Directory containing Web3 data files
        """
        self.twitter_data_dir = twitter_data_dir
        self.web3_data_dir = web3_data_dir
        self.user_mapping = self._build_user_mapping()
    
    def _build_user_mapping(self) -> Dict[str, str]:
        """Build a mapping between user IDs and their file names."""
        mapping = {}
        
        # Get all Twitter data files
        if os.path.exists(self.twitter_data_dir):
            for filename in os.listdir(self.twitter_data_dir):
                if filename.endswith(".txt"):
                    user_id = filename.replace(".txt", "")
                    mapping[user_id] = user_id
        
        return mapping
    
    def load_user_data(self, user_id: str) -> Dict[str, Any]:
        """Load Twitter and Web3 data for a specific user.
        
        Args:
            user_id: The user identifier
            
        Returns:
            Dictionary containing the user's Twitter and Web3 data
        """
        if user_id not in self.user_mapping:
            raise ValueError(f"User {user_id} not found in available data")
        
        file_prefix = self.user_mapping[user_id]
        
        # Load Twitter data
        twitter_data = self._parse_twitter_data(os.path.join(self.twitter_data_dir, f"{file_prefix}.txt"))
        
        # Load Web3 data
        web3_data = self._parse_web3_data(os.path.join(self.web3_data_dir, f"{file_prefix}Web3.txt"))
        
        return {
            "user_id": user_id,
            "twitter_data": twitter_data,
            "web3_data": web3_data
        }
    
    def load_friend_data(self, user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Load data for users that the given user follows or interacts with.
        
        Args:
            user_data: The user's data containing Twitter interactions
            
        Returns:
            List of dictionaries containing data for each friend
        """
        # Extract mentioned users from Twitter data
        mentioned_users = self._extract_mentioned_users(user_data["twitter_data"])
        
        # Load data for all available users except the current user
        friend_data = []
        for potential_friend in self.user_mapping.keys():
            if potential_friend != user_data["user_id"]:
                try:
                    friend_data.append(self.load_user_data(potential_friend))
                except Exception as e:
                    print(f"Error loading data for {potential_friend}: {str(e)}")
        
        return friend_data
    
    def _extract_mentioned_users(self, twitter_data: Dict[str, Any]) -> List[str]:
        """Extract users mentioned in tweets.
        
        Args:
            twitter_data: Parsed Twitter data
            
        Returns:
            List of mentioned user handles
        """
        mentioned_users = []
        
        for tweet in twitter_data["tweets"]:
            # Extract @mentions from tweet text
            mentions = re.findall(r'@(\w+)', tweet["text"])
            mentioned_users.extend(mentions)
        
        return list(set(mentioned_users))  # Remove duplicates
    
    def _parse_twitter_data(self, file_path: str) -> Dict[str, Any]:
        """Parse Twitter data from a text file.
        
        Args:
            file_path: Path to the Twitter data file
            
        Returns:
            Dictionary containing parsed Twitter data
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Twitter data file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Handle empty files
        if not lines:
            return {
                "username": "",
                "handle": "",
                "tweets": []
            }
        
        # Extract user info - handle case where username appears twice
        username = lines[0].strip()
        
        # Skip duplicate username line if present
        start_idx = 1
        if len(lines) > 1 and lines[1].strip() == username:
            start_idx = 2
        
        # Extract handle from the next line if available
        handle = ""
        if len(lines) > start_idx:
            handle_match = re.search(r'@(\w+)', lines[start_idx].strip())
            if handle_match:
                handle = handle_match.group(0)
                start_idx += 1
        
        tweets = []
        current_tweet = {}
        
        # Skip header lines if present
        if len(lines) > start_idx and "User\tTweet\tDate\tStats\tLink" in lines[start_idx]:
            start_idx += 1
        
        for i in range(start_idx, len(lines)):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check if this is the start of a new tweet
            if line.startswith(username):
                # Save the previous tweet if it exists
                if current_tweet and "text" in current_tweet:
                    tweets.append(current_tweet)
                
                # Start a new tweet
                current_tweet = {"user": username, "handle": handle}
            elif "Likes" in line:
                # Extract likes count
                likes_match = re.search(r'(\d+) Likes', line)
                if likes_match:
                    current_tweet["likes"] = int(likes_match.group(1))
            elif "Retweets" in line:
                # Extract retweets count
                retweets_match = re.search(r'(\d+) Retweets', line)
                if retweets_match:
                    current_tweet["retweets"] = int(retweets_match.group(1))
            elif re.search(r'\d+/\d+/\d+, \d+:\d+:\d+ [AP]M', line):
                # This is a date line
                current_tweet["date"] = line
            elif "Link unavailable" not in line and not line.startswith(username) and not line.startswith('@'):
                # This is likely the tweet text
                current_tweet["text"] = line
        
        # Add the last tweet if it exists
        if current_tweet and "text" in current_tweet:
            tweets.append(current_tweet)
        
        # Handle case where tweets array is empty
        if not tweets:
            tweets = [{"text": "No tweets found"}]
        
        return {
            "username": username,
            "handle": handle,
            "tweets": tweets
        }
    
    def _parse_web3_data(self, file_path: str) -> Dict[str, Any]:
        """Parse Web3 data from a text file.
        
        Args:
            file_path: Path to the Web3 data file
            
        Returns:
            Dictionary containing parsed Web3 data
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Web3 data file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        data = {
            "holdings": {},
            "profit_loss": {},
            "recent_trades": []
        }
        
        section = None
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and header lines
            if not line or line.startswith("Birth Time") or line.startswith("Birthplace") or line.startswith("Gender") or line.startswith("User's actual"):
                continue
            
            # Determine which section we're in
            if line.startswith("Holdings:"):
                section = "holdings"
                holdings_str = line.replace("Holdings: ", "")
                # Parse holdings
                holdings_items = holdings_str.split(", ")
                for item in holdings_items:
                    # Handle NFT entries (special format)
                    if '#' in item and 'NFT' in item:
                        try:
                            # Extract NFT information using regex
                            nft_match = re.search(r'([\w\s]+) #(\d+) \((\d+) NFT, \$(\d+[,\d]*\.\d+)\)', item)
                            if nft_match:
                                collection, token_id, quantity, value_str = nft_match.groups()
                                asset = f"{collection.strip()} #{token_id}"
                                data["holdings"][asset] = {
                                    "amount": int(quantity),
                                    "value_usd": float(value_str.replace(",", "")),
                                    "is_nft": True
                                }
                        except Exception as e:
                            print(f"Error parsing NFT: {item} - {str(e)}")
                        continue
                    
                    # Handle regular token entries
                    try:
                        # First, extract the asset name and the rest by finding the first colon
                        colon_index = item.find(":")
                        if colon_index > 0:
                            asset_name = item[:colon_index].strip()
                            remaining = item[colon_index+1:].strip()
                            
                            # Check for testnet assets (they have a different format)
                            testnet_match = re.search(r'^([\d.]+)\s+\(Testnet\)', remaining)
                            if testnet_match:
                                amount_str = testnet_match.group(1)
                                amount = float(amount_str)
                                # For testnet assets, set value to 0 as they don't have real value
                                data["holdings"][asset_name] = {"amount": amount, "value_usd": 0, "is_testnet": True}
                            else:
                                # Check for regular assets with dollar values
                                dollar_match = re.search(r'^([\d.]+)\s+\(\$(\d+[,\d]*\.\d+)\)', remaining)
                                if dollar_match:
                                    amount_str, value_str = dollar_match.groups()
                                    amount = float(amount_str)
                                    value = float(value_str.replace(",", ""))
                                    data["holdings"][asset_name] = {"amount": amount, "value_usd": value}
                                else:
                                    # Try to parse in a more generic way
                                    parts = remaining.split(" ", 1)
                                    if len(parts) >= 2:
                                        try:
                                            amount = float(parts[0])
                                            # Check if this is a testnet asset
                                            if "(Testnet)" in parts[1]:
                                                data["holdings"][asset_name] = {"amount": amount, "value_usd": 0, "is_testnet": True}
                                            else:
                                                # Try to extract the dollar value
                                                value_match = re.search(r'\$(\d+[,\d]*\.\d+)', parts[1])
                                                if value_match:
                                                    value_str = value_match.group(1)
                                                    value = float(value_str.replace(",", ""))
                                                    data["holdings"][asset_name] = {"amount": amount, "value_usd": value}
                                        except ValueError:
                                            print(f"Error parsing amount in: {item}")
                        else:
                            # Fallback to the old method for backward compatibility
                            parts = item.split(" ")
                            if len(parts) >= 3:
                                try:
                                    asset = parts[0]
                                    amount = float(parts[1].replace(":", ""))
                                    value_str = parts[2].replace("($", "").replace("),", "").replace(")", "").replace(",", "")
                                    value = float(value_str)
                                    data["holdings"][asset] = {"amount": amount, "value_usd": value}
                                except (ValueError, IndexError):
                                    print(f"Error parsing with fallback method: {item}")
                    except Exception as e:
                        print(f"Error parsing holding: {item} - {str(e)}")
                        continue
            
            elif line.startswith("Profit/Loss:"):
                section = "profit_loss"
            
            elif line.startswith("Recent Trades:"):
                section = "recent_trades"
            
            elif section == "profit_loss":
                if line.startswith("Total:"):
                    data["profit_loss"]["total"] = float(line.replace("Total: $", "").replace(",", ""))
                elif line.startswith("Realized:"):
                    data["profit_loss"]["realized"] = float(line.replace("Realized: $", "").replace(",", ""))
                elif line.startswith("Unrealized:"):
                    data["profit_loss"]["unrealized"] = float(line.replace("Unrealized: $", "").replace(",", ""))
            
            elif section == "recent_trades":
                # Parse trade data
                trade_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (buy|sell) (.+)', line)
                if trade_match:
                    timestamp, action, details = trade_match.groups()
                    
                    # Parse the details part
                    amount_asset_match = re.match(r'([\d.]+) (\w+)', details)
                    if amount_asset_match:
                        amount, asset = amount_asset_match.groups()
                        
                        # Extract the currency used and value
                        currency_match = re.search(r'(with|for) (\w+), \$(\d+[,\d]*\.\d+)', details)
                        if currency_match:
                            _, currency, value = currency_match.groups()
                            
                            trade = {
                                "timestamp": timestamp,
                                "action": action,
                                "asset": asset,
                                "amount": float(amount),
                                "currency": currency,
                                "value_usd": float(value.replace(",", ""))
                            }
                            
                            data["recent_trades"].append(trade)
        
        return data
    
    def get_all_users(self) -> List[str]:
        """Get a list of all available users.
        
        Returns:
            List of user IDs
        """
        return list(self.user_mapping.keys())