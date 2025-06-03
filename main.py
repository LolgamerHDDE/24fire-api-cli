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

# Define API key from environment variable
API_KEY = os.getenv("FIRE_API_KEY")

# Handleing the Not Found Error
if not API_KEY:
    API_KEY = "None"

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
        json_response = response.json()
        print(f"{RED} Error: {json_response.get('message', 'Unknown error')} {RESET}")
        exit(1)

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

def fetch_account(api_key):
    """Fetch account information from API."""
    url = "https://manage.24fire.de/api/account"
    response = requests.get(url, headers={'X-Fire-Apikey': api_key})
    
    if response.status_code == 200:
        return response.json()
    else:
        json_response = response.json()
        print(f"{RED} Error: {json_response.get('message', 'Unknown error')} {RESET}")
        return None

def fetch_donations(api_key):
    """Fetch donation information from API."""
    url = "https://manage.24fire.de/api/account/donations"
    response = requests.get(url, headers={'X-Fire-Apikey': api_key})
    
    if response.status_code == 200:
        return response.json()
    else:
        json_response = response.json()
        print(f"{RED} Error: {json_response.get('message', 'Unknown error')} {RESET}")
        return None

def fetch_affiliate(api_key):
    """Fetch affiliate information from API."""
    url = "https://manage.24fire.de/api/account/affiliate"
    response = requests.get(url, headers={'X-Fire-Apikey': api_key})
    
    if response.status_code == 200:
        return response.json()
    else:
        json_response = response.json()
        print(f"{RED} Error: {json_response.get('message', 'Unknown error')} {RESET}")
        return None

def format_output(data):
    """Format the API response data into readable key-value pairs."""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print(f"\n{CYAN}{key}:{RESET}")
                format_output(value)
            else:
                print(f"  {BLUE}{key}:{RESET} {value}")
    elif isinstance(data, list):
        for item in data:
            format_output(item)
            print()

def format_account(data):
    """Format account data with better structure."""
    if not data or 'data' not in data:
        print(f"{RED}No account data available{RESET}")
        return
    
    account = data['data']
    
    print(f"\n{BOLD}{CYAN}=== ACCOUNT INFORMATION ==={RESET}")
    print(f"  {BLUE}Name:{RESET} {account.get('firstname', 'N/A')} {account.get('lastname', 'N/A')}")
    print(f"  {BLUE}Email:{RESET} {account.get('email', 'N/A')}")
    print(f"  {BLUE}Profile Image:{RESET} {account.get('profile_image', 'N/A')}")
    
    # Balance with color coding
    balance = account.get('balance', 0)
    balance_color = GREEN if balance > 0 else RED if balance < 0 else YELLOW
    print(f"  {BLUE}Balance:{RESET} {balance_color}€{balance}{RESET}")
    
    # Plus user status
    plus_status = account.get('is_plus_user', False)
    plus_color = GREEN if plus_status else YELLOW
    plus_text = "Yes" if plus_status else "No"
    print(f"  {BLUE}Plus User:{RESET} {plus_color}{plus_text}{RESET}")
    
    print(f"  {BLUE}Registry Date:{RESET} {account.get('registry_date', 'N/A')}")
    
    discord_id = account.get('discord_id')
    discord_text = discord_id if discord_id else "Not linked"
    discord_color = GREEN if discord_id else YELLOW
    print(f"  {BLUE}Discord ID:{RESET} {discord_color}{discord_text}{RESET}")
    
    # Invoice address
    invoice_addr = account.get('invoice_address', {})
    if invoice_addr:
        print(f"\n{BOLD}{CYAN}=== INVOICE ADDRESS ==={RESET}")
        print(f"  {BLUE}Name:{RESET} {invoice_addr.get('name', 'N/A')}")
        print(f"  {BLUE}Street:{RESET} {invoice_addr.get('street', 'N/A')} {invoice_addr.get('number', '')}")
        print(f"  {BLUE}ZIP Code:{RESET} {invoice_addr.get('zip', 'N/A')}")
        print(f"  {BLUE}City:{RESET} {invoice_addr.get('city', 'N/A')}")
        print(f"  {BLUE}Country:{RESET} {invoice_addr.get('country', 'N/A')}")

def format_donations(data):
    """Format donation data with better structure."""
    if not data or 'data' not in data:
        print(f"{RED}No donation data available{RESET}")
        return
    
    info = data['data'].get('information', {})
    donations = data['data'].get('donations', [])
    
    print(f"\n{BOLD}{CYAN}=== DONATION PAGE INFORMATION ==={RESET}")
    print(f"  {BLUE}Enabled:{RESET} {info.get('enabled', 'N/A')}")
    print(f"  {BLUE}Description:{RESET} {info.get('description', 'N/A')}")
    print(f"  {BLUE}Link:{RESET} {info.get('link', 'N/A')}")
    print(f"  {BLUE}Background Image:{RESET} {info.get('background_image', 'N/A')}")
    
    print(f"\n{BOLD}{CYAN}=== DONATIONS ==={RESET}")
    if donations:
        for donation in donations:
            print(f"\n  {MAGENTA}Donation ID:{RESET} {donation.get('id', 'N/A')}")
            print(f"  {BLUE}Date:{RESET} {donation.get('date', 'N/A')}")
            print(f"  {BLUE}Donator:{RESET} {donation.get('donator', 'N/A')}")
            print(f"  {BLUE}Amount:{RESET} €{donation.get('amount', 'N/A')}")
            status_color = GREEN if donation.get('status') == 'paid' else YELLOW
            print(f"  {BLUE}Status:{RESET} {status_color}{donation.get('status', 'N/A')}{RESET}")
    else:
        print(f"  {YELLOW}No donations found{RESET}")

def format_affiliate(data):
    """Format affiliate data with better structure."""
    if not data or 'data' not in data:
        print(f"{RED}No affiliate data available{RESET}")
        return
    
    info = data['data'].get('information', {})
    summary = data['data'].get('summary', {})
    leads = data['data'].get('leads', [])
    
    print(f"\n{BOLD}{CYAN}=== AFFILIATE INFORMATION ==={RESET}")
    print(f"  {BLUE}Referral Link:{RESET} {info.get('link', 'N/A')}")
    
    print(f"\n{BOLD}{CYAN}=== SUMMARY ==={RESET}")
    print(f"  {BLUE}Confirmed Leads:{RESET} {summary.get('confirmed_leads', 'N/A')}")
    print(f"  {BLUE}URL Clicks:{RESET} {summary.get('url_clicks', 'N/A')}")
    print(f"  {BLUE}Balance Paid:{RESET} €{summary.get('balance_paid', 'N/A')}")
    print(f"  {BLUE}Balance Pending:{RESET} €{summary.get('balance_pending', 'N/A')}")
    
    print(f"\n{BOLD}{CYAN}=== LEADS ==={RESET}")
    if leads:
        for lead in leads:
            print(f"\n  {MAGENTA}Customer:{RESET} {lead.get('customer', 'N/A')}")
            print(f"  {BLUE}Date:{RESET} {lead.get('date', 'N/A')}")
            print(f"  {BLUE}Buy Price:{RESET} €{lead.get('buy_price', 'N/A')}")
            print(f"  {BLUE}Product:{RESET} {lead.get('product_name', 'N/A')}")
            status_color = GREEN if lead.get('status') == 'confirmed' else RED if lead.get('status') == 'canceled' else YELLOW
            print(f"  {BLUE}Status:{RESET} {status_color}{lead.get('status', 'N/A')}{RESET}")
    else:
        print(f"  {YELLOW}No leads found{RESET}")

def show_extras_menu(api_key):
    """Show the extras menu with account, donation and affiliate options."""
    print(f"\n{BOLD}{MAGENTA}=== EXTRAS MENU ==={RESET}")
    print(f"{BLUE}1. Account Information{RESET}")
    print(f"{BLUE}2. Donation Site Information{RESET}")
    print(f"{BLUE}3. Affiliate Information{RESET}")
    print(f"{BLUE}4. Back to Main Menu{RESET}")
    
    choice = input(f"{YELLOW}Select an option (1-4): {RESET}").strip()
    
    if choice == "1":
        print(f"\n{BOLD}Fetching account information...{RESET}")
        account_data = fetch_account(api_key)
        if account_data:
            format_account(account_data)
    elif choice == "2":
        print(f"\n{BOLD}Fetching donation information...{RESET}")
        donation_data = fetch_donations(api_key)
        if donation_data:
            format_donations(donation_data)
    elif choice == "3":
        print(f"\n{BOLD}Fetching affiliate information...{RESET}")
        affiliate_data = fetch_affiliate(api_key)
        if affiliate_data:
            format_affiliate(affiliate_data)
    elif choice == "4":
        main(API_KEY)
    else:
        print(f"{RED}Invalid selection. Please enter 1, 2, 3, or 4.{RESET}")
    
    # Ask if user wants to continue in extras menu
    continue_choice = input(f"\n{YELLOW}Return to extras menu? (y/n): {RESET}").strip().lower()
    if continue_choice == 'y':
        show_extras_menu(api_key)

def main(api_key: str):
    data, numbered_services = request_data(api_key)
    
    logo = """
 .d8888b.     d8888  .d888d8b                   .d8888b. 888     8888888 
d88P  Y88b   d8P888 d88P" Y8P                  d88P  Y88b888       888   
       888  d8P 888 888                        888    888888       888   
     .d88P d8P  888 888888888888d888 .d88b.    888       888       888   
 .od888P" d88   888 888   888888P"  d8P  Y8b   888       888       888   
d88P"     8888888888888   888888    88888888   888    888888       888   
888"            888 888   888888    Y8b.       Y88b  d88P888       888   
888888888       888 888   888888     "Y8888     "Y8888P" 888888888888888 
                                                                         
"""
    print(f"{GREEN}{logo}{RESET}")

    # Print extras option first
    print(f"{MAGENTA}0. Extras (Account, Donations & Affiliate){RESET}")
    
    if not data:
        print(f"{RED} No services found. {RESET}")
        # Still allow access to extras even if no services
        user_input = input(f"{YELLOW}Enter 0 for extras or any other key to exit:{RESET} ").strip()
        if user_input == "0":
            show_extras_menu(api_key)
        return

    # Print services with numbers
    for idx, service in enumerate(data, start=1):
        print(f"{BLUE}{idx}. {service['name']}{RESET}")

    # User input to find service type
    user_input = input(f"{YELLOW}Enter the number to fetch the infos from (0 for extras):{RESET} ").strip()
    
    # Handle extras option
    if user_input == "0":
        show_extras_menu(api_key)
    # Handle numeric input for services
    elif user_input.isdigit() and 1 <= int(user_input) <= len(data):
        selected_service = data[int(user_input) - 1]
        infos = fetch_infos(api_key, selected_service['internal_id'], selected_service['type'])
        print(f"\n{BOLD}Service Information:{RESET}")
        format_output(infos)
    else:
        print(f"{RED}Invalid selection. Please enter a valid number.{RESET}")

if __name__ == "__main__":
    main(API_KEY)
