import requests
import json
import os
from dotenv import load_dotenv

# ANSI escape codes for CLI colors
RESET = "\033[0m"
BOLD = "\033[1m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

# Text Colors
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

# Bright Text Colors
BRIGHT_BLACK = "\033[90m"
BRIGHT_RED = "\033[91m"
BRIGHT_GREEN = "\033[92m"
BRIGHT_YELLOW = "\033[93m"
BRIGHT_BLUE = "\033[94m"
BRIGHT_MAGENTA = "\033[95m"
BRIGHT_CYAN = "\033[96m"
BRIGHT_WHITE = "\033[97m"

# Background Colors
BG_BLACK = "\033[40m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"
BG_WHITE = "\033[47m"

# Bright Background Colors
BG_BRIGHT_BLACK = "\033[100m"
BG_BRIGHT_RED = "\033[101m"
BG_BRIGHT_GREEN = "\033[102m"
BG_BRIGHT_YELLOW = "\033[103m"
BG_BRIGHT_BLUE = "\033[104m"
BG_BRIGHT_MAGENTA = "\033[105m"
BG_BRIGHT_CYAN = "\033[106m"
BG_BRIGHT_WHITE = "\033[107m"

# Load environment variables from .env file
load_dotenv()

def extract_name_and_id(json_response):
    # Placeholder for the result
    result = []

    # Extracting the services from the JSON response
    services = json_response.get('data', {}).get('services', {})
    
    # Making a new JSON object with the desired structure
    for service_type in services:
        for service in services[service_type]:
            result.append({
                'name': service['name'],
                'internal_id': service['internal_id']
            })
    
    return result

def request_data(api_key: str):
    # Url for requesting the names/internal_ids
    url = 'https://manage.24fire.de/api/account/services'

    # Fetch Response from 24fire
    response = requests.get(url, headers={'X-Fire-Apikey': api_key})

    # Fetch the name and internal_ids
    result = extract_name_and_id(response.json())

    return result

def main(api_key: str):
    # Placeholder number
    num = 0

    # Define the main Variables
    data = request_data(api_key)
    names = [service['name'] for service in data]

    # Define the Logo
    logo = """
.d8888b.     d8888  .d888d8b                   .d8888b. 888     8888888 
d88P  Y88b   d8P888 d88P" Y8P                  d88P  Y88b888       888   
       888  d8P 888 888                        888    888888       888   
     .d88P d8P  888 888888888888d888 .d88b.    888       888       888   
 .od888P" d88   888 888   888888P"  d8P  Y8b   888       888       888   
d88P"     8888888888888   888888    88888888   888    888888       888   
888"            888 888   888888    Y8b.       Y88b  d88P888       888   
888888888       888 888   888888     "Y8888     "Y8888P" 888888888888888 
Coded by SyncWide Solutions
                                                                         
    """

    # Print the logo
    print(f"{RED}{logo}")

    # list names numberized
    for name in names:
        num += 1
        print(f"{BLUE}{num} - {name}")


if __name__ == "__main__":
    main(os.getenv('FIRE_API_KEY'))
    print(RESET)