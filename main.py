import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def extract_name_and_id(json_response):
    result = []
    services = json_response.get('data', {}).get('services', {})
    
    for service_type in services:
        for service in services[service_type]:
            result.append({
                'name': service['name'],
                'internal_id': service['internal_id']
            })
    
    return result

def request_data(api_key: str):
    url = 'https://manage.24fire.de/api/account/services'
    response = requests.get(url, headers={'X-Fire-Apikey': api_key})
    result = extract_name_and_id(response.json())
    return result

if __name__ == "__main__":
    result = request_data(os.environ.get('FIRE_API_KEY'))
    print(result)