import os
import requests

api_key = os.getenv("ODSAY_API_KEY")
print(f"API Key: {api_key}")

url = "https://api.odsay.com/v1/api/searchPubTransPathT"
params = {
    'apiKey': api_key,
    'SX': 126.9571988,
    'SY': 37.4648267,
    'EX': 126.96388,
    'EY': 37.394346,
    'lang': 1,
    'output': 'json'
}

response = requests.get(url, params=params)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
