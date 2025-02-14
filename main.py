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

def extract_services(json_response):
    """Extract service name, internal_id, and type from JSON response."""
    result = []

    services = json_response.get('data', {}).get('services', {})

    for service_type, service_list in services.items():
        for service in service_list:
            result.append({
                'name': service['name'],
                'internal_id': service['internal_id'],
                'type': service_type
            })

    return result

def request_data(api_key: str):
    """Fetch service data from API."""
    url = 'https://manage.24fire.de/api/account/services'
    response = requests.get(url, headers={'X-Fire-Apikey': api_key})

    if response.status_code == 200:
        return extract_services(response.json())
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return []

def get_service_type(services, search_value):
    """Find service type by internal_id or name."""
    for service in services:
        if service['internal_id'] == search_value or service['name'] == search_value:
            return service['type']
    return None

def request_data(api_key: str):
    """Fetch service data from API with support for numeric selection."""
    url = 'https://manage.24fire.de/api/account/services'
    response = requests.get(url, headers={'X-Fire-Apikey': api_key})

    if response.status_code == 200:
        services = extract_services(response.json())
        # Create a mapping of index to service
        numbered_services = {str(idx): service for idx, service in enumerate(services, start=1)}
        return services, numbered_services
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return [], {}

def fetch_infos(api_key, internal_id, service_type):
    """Fetch service infos from API."""
    kvm_url = f"https://manage.24fire.de/api/kvm/{internal_id}/status"
    webspace_url = f"https://manage.24fire.de/api/webspace/{internal_id}"
    domain_url = f"https://manage.24fire.de/api/domain/{internal_id}"

    if service_type == 'KVM':
        response = requests.get(kvm_url, headers={'X-Fire-Apikey': api_key})
        return response.json()
    elif service_type == 'WEBSPACE':
        response = requests.get(webspace_url, headers={'X-Fire-Apikey': api_key})
        return response.json()
    elif service_type == 'DOMAIN':
        response = requests.get(domain_url, headers={'X-Fire-Apikey': api_key})
        return response.json()
    else:
        print("Invalid service type.")
        return

def main(api_key: str):
    data, numbered_services = request_data(api_key)

    if not data:
        print("No services found.")
        return

    # Print services with numbers
    for idx, service in enumerate(data, start=1):
        print(f"{BLUE}{idx}. {service['name']}{RESET}")

    # User input to find service type
    user_input = input(f"{YELLOW}Enter the number to fetch the infos from:{RESET} ").strip()
    
    # Handle numeric input
    if user_input.isdigit() and 1 <= int(user_input) <= len(data):
        selected_service = data[int(user_input) - 1]
        infos = fetch_infos(api_key, selected_service['internal_id'], selected_service['type'])
        print(infos)
    else:
        print("Invalid selection. Please enter a valid number.")

if __name__ == "__main__":
    main(os.getenv('FIRE_API_KEY'))
