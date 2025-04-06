import sys
import os

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_processor import DataProcessor

# Initialize the data processor
dp = DataProcessor()

# Test BillSun's data for "lucky money"
print("Testing BillSun's data for 'lucky money'...")
user_data = dp.load_user_data('BillSun')
lucky_money = user_data['web3_data']['holdings'].get('lucky money')
print(f"Lucky money holdings: {lucky_money}")

# Test DavidDev's data for "Fuji AVAX"
print("\nTesting DavidDev's data for 'Fuji AVAX'...")
user_data2 = dp.load_user_data('DavidDev')
fuji_avax = user_data2['web3_data']['holdings'].get('Fuji AVAX')
print(f"Fuji AVAX holdings: {fuji_avax}")

# Print all holdings keys to verify
print("\nAll holdings keys for BillSun:")
for key in user_data['web3_data']['holdings'].keys():
    print(f"  - '{key}'")

print("\nAll holdings keys for DavidDev:")
for key in user_data2['web3_data']['holdings'].keys():
    print(f"  - '{key}'")