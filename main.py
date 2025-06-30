import requests
import json
import sys
import os
import argparse
import subprocess
import tempfile
import urllib.request
import stat
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

def find_kvm_server(api_key, server_identifier):
    """Find KVM server by name or internal_id and return server info."""
    try:
        # Make direct API call to get raw service data
        url = 'https://manage.24fire.de/api/account/services'
        response = requests.get(url, headers={'X-Fire-Apikey': api_key})
        
        if response.status_code != 200:
            return None
            
        json_response = response.json()
        services = json_response.get('data', {}).get('services', {})
        
        # Look specifically in the KVM section
        kvm_servers = services.get('KVM', [])
        
        for server in kvm_servers:
            if (server['name'] == server_identifier or 
                server['internal_id'] == server_identifier):
                # Return server info with type added for consistency
                server_info = server.copy()
                server_info['type'] = 'KVM'
                return server_info
        
        return None
    except Exception as e:
        print(f"{RED}Error finding KVM server: {e}{RESET}")
        return None

def control_kvm_server(api_key, server_identifier, mode):
    """Control KVM server power state."""
    # Find the server
    server = find_kvm_server(api_key, server_identifier)
    
    if not server:
        print(f"{RED}Server '{server_identifier}' not found or is not a KVM server.{RESET}")
        return
    
    # Make the API call
    url = f"https://manage.24fire.de/api/kvm/{server['internal_id']}/power"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Fire-Apikey': api_key
    }
    data = {'mode': mode}
    
    try:
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 200:
            json_response = response.json()
            if json_response.get('status') == 'success':
                # Success message
                action_past = {
                    'start': 'Started',
                    'stop': 'Stopped', 
                    'restart': 'Restarted'
                }
                print(f"{GREEN}{server['name']} successfully {action_past[mode]}{RESET}")
            else:
                # API returned error
                action_verb = {
                    'start': 'Start',
                    'stop': 'Stop',
                    'restart': 'Restart'
                }
                print(f"{RED}Failed to {action_verb[mode]} {server['name']}{RESET}")
        else:
            # HTTP error
            action_verb = {
                'start': 'Start',
                'stop': 'Stop', 
                'restart': 'Restart'
            }
            print(f"{RED}Failed to {action_verb[mode]} {server['name']}{RESET}")
            
    except requests.RequestException:
        action_verb = {
            'start': 'Start',
            'stop': 'Stop',
            'restart': 'Restart'
        }
        print(f"{RED}Failed to {action_verb[mode]} {server['name']} - Network error{RESET}")

def format_backups(data):
    """Format backup data with better structure."""
    if not data or 'data' not in data:
        print(f"{RED}No backup data available{RESET}")
        return
    
    backups = data['data']
    
    print(f"\n{BOLD}{CYAN}=== VM BACKUPS ==={RESET}")
    print(f"{GREEN}Status: {data.get('status', 'N/A')}{RESET}")
    print(f"{BLUE}Message: {data.get('message', 'N/A')}{RESET}")
    
    if backups:
        print(f"\n{BOLD}{YELLOW}Found {len(backups)} backup(s):{RESET}")
        
        for idx, backup in enumerate(backups, 1):
            print(f"\n{BOLD}{MAGENTA}=== BACKUP #{idx} ==={RESET}")
            print(f"  {BLUE}Backup ID:{RESET} {backup.get('backup_id', 'N/A')}")
            print(f"  {BLUE}Operating System:{RESET} {backup.get('backup_os', 'N/A').replace('_', ' ').title()}")
            
            # Description with fallback
            description = backup.get('backup_description', '').strip()
            desc_text = description if description else "No description"
            desc_color = WHITE if description else BRIGHT_BLACK
            print(f"  {BLUE}Description:{RESET} {desc_color}{desc_text}{RESET}")
            
            # Size with safe handling for None values
            size = backup.get('size')
            if size is not None and isinstance(size, (int, float)):
                if size >= 1024:
                    size_text = f"{size/1024:.2f} GB"
                else:
                    size_text = f"{size:.2f} MB"
                print(f"  {BLUE}Size:{RESET} {CYAN}{size_text}{RESET}")
            else:
                print(f"  {BLUE}Size:{RESET} {BRIGHT_BLACK}Unknown{RESET}")
            
            # Created date formatting
            created = backup.get('created', 'N/A')
            if created != 'N/A':
                # Convert ISO format to readable format
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    formatted_date = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                    print(f"  {BLUE}Created:{RESET} {GREEN}{formatted_date}{RESET}")
                except:
                    print(f"  {BLUE}Created:{RESET} {created}")
            else:
                print(f"  {BLUE}Created:{RESET} {created}")
            
            # Status with color coding
            status = backup.get('status', 'unknown').lower()
            if status == 'finished':
                status_color = GREEN
                status_icon = "✓"
            elif status == 'running':
                status_color = YELLOW
                status_icon = "⏳"
            elif status == 'failed':
                status_color = RED
                status_icon = "✗"
            else:
                status_color = BRIGHT_BLACK
                status_icon = "?"
            
            print(f"  {BLUE}Status:{RESET} {status_color}{status_icon} {status.title()}{RESET}")
            
            # Add separator line except for last backup
            if idx < len(backups):
                print(f"  {BRIGHT_BLACK}{'─' * 50}{RESET}")
    else:
        print(f"  {YELLOW}No backups found{RESET}")
    
    # Summary with safe size calculation
    if backups:
        total_size = 0
        valid_sizes = []
        
        for backup in backups:
            size = backup.get('size')
            if size is not None and isinstance(size, (int, float)):
                total_size += size
                valid_sizes.append(size)
        
        if total_size >= 1024:
            total_size_text = f"{total_size/1024:.2f} GB"
        else:
            total_size_text = f"{total_size:.2f} MB"
        
        finished_count = sum(1 for backup in backups if backup.get('status') == 'finished')
        running_count = sum(1 for backup in backups if backup.get('status') == 'running')
        failed_count = sum(1 for backup in backups if backup.get('status') == 'failed')
        
        print(f"\n{BOLD}{CYAN}=== SUMMARY ==={RESET}")
        print(f"  {BLUE}Total Backups:{RESET} {BRIGHT_WHITE}{len(backups)}{RESET}")
        print(f"  {BLUE}Finished:{RESET} {GREEN}{finished_count}{RESET}")
        if running_count > 0:
            print(f"  {BLUE}Running:{RESET} {YELLOW}{running_count}{RESET}")
        if failed_count > 0:
            print(f"  {BLUE}Failed:{RESET} {RED}{failed_count}{RESET}")
        
        if valid_sizes:
            print(f"  {BLUE}Total Size:{RESET} {CYAN}{total_size_text}{RESET}")
        else:
            print(f"  {BLUE}Total Size:{RESET} {BRIGHT_BLACK}Unknown{RESET}")

def handle_backup_request(api_key, action, target, backup_id=None):
    server = find_kvm_server(api_key, target)
    
    if not server:
        print(f"{RED}Server '{target}' not found or is not a KVM server.{RESET}")
        return
    
    server_internal_id = server['internal_id']
    
    if action == 'list':
        url = f'https://manage.24fire.de/api/kvm/{server_internal_id}/backup/list'
        response = requests.get(url,
                                headers = {
                                    'Content-Type': 'application/x-www-form-urlencoded',
                                    'X-Fire-Apikey': api_key
                                })
        
        if response.status_code == 200:
            json_response = response.json()
            if json_response.get('status') == 'success':
                format_backups(json_response)
            else:
                print(f"{RED}Failed to fetch backups: {json_response.get('message', 'Unknown error')}{RESET}")
        else:
            print(f"{RED}Failed to fetch backups for {server['name']} - HTTP {response.status_code}{RESET}")
    
    elif action == 'create':
        url = f'https://manage.24fire.de/api/kvm/{server_internal_id}/backup/create'
        response = requests.post(url,
                                headers = {
                                    'Content-Type': 'application/x-www-form-urlencoded',
                                    'X-Fire-Apikey': api_key
                                })
        
        if response.status_code == 200:
            json_response = response.json()
            if json_response.get('status') == 'success':
                print(f"{GREEN}✓ Backup creation started for {server['name']}{RESET}")
                print(f"{BLUE}Message: {json_response.get('message', 'Backup initiated')}{RESET}")
                print(f"{BLUE}Backup ID: {json_response.get('data', {}).get('backup_id', 'N/A')}{RESET}")
            else:
                print(f"{RED}✗ Failed to create backup: {json_response.get('message', 'Unknown error')}{RESET}")
        else:
            print(f"{RED}✗ Failed to create backup for {server['name']} - HTTP {response.status_code}{RESET}")
    
    elif action == 'restore':
        url = f'https://manage.24fire.de/api/kvm/{server_internal_id}/backup/restore'
        data = {'backup_id': backup_id}
        response = requests.post(url,
                                headers = {
                                    'Content-Type': 'application/x-www-form-urlencoded',
                                    'X-Fire-Apikey': api_key
                                },
                                data=data)
        
        if response.status_code == 200:
            json_response = response.json()
            if json_response.get('status') == 'success':
                print(f"{GREEN}✓ Backup restore started for {server['name']}{RESET}")
                print(f"{BLUE}Backup ID: {backup_id}{RESET}")
                print(f"{BLUE}Message: {json_response.get('message', 'Restore initiated')}{RESET}")
            else:
                print(f"{RED}✗ Failed to restore backup: {json_response.get('message', 'Unknown error')}{RESET}")
        else:
            print(f"{RED}✗ Failed to restore backup for {server['name']} - HTTP {response.status_code}{RESET}")
    
    elif action == 'delete':
        url = f'https://manage.24fire.de/api/kvm/{server_internal_id}/backup/delete'
        data = {'backup_id': backup_id}
        response = requests.delete(url,
                                headers = {
                                    'Content-Type': 'application/x-www-form-urlencoded',
                                    'X-Fire-Apikey': api_key
                                },
                                data=data)
        
        if response.status_code == 200:
            json_response = response.json()
            if json_response.get('status') == 'success':
                print(f"{GREEN}✓ Backup deleted successfully{RESET}")
                print(f"{BLUE}Backup ID: {backup_id}{RESET}")
                print(f"{BLUE}Message: {json_response.get('message', 'Backup deleted')}{RESET}")
            else:
                print(f"{RED}✗ Failed to delete backup: {json_response.get('message', 'Unknown error')}{RESET}")
        else:
            print(f"{RED}✗ Failed to delete backup - HTTP {response.status_code}{RESET}")

def format_traffic(response):
    """Format traffic data with better structure."""
    if response.status_code != 200:
        print(f"{RED}Failed to fetch traffic data - HTTP {response.status_code}{RESET}")
        return
    
    try:
        data = response.json()
    except:
        print(f"{RED}Failed to parse traffic data{RESET}")
        return
    
    if not data or data.get('status') != 'success':
        print(f"{RED}Error: {data.get('message', 'Unknown error')}{RESET}")
        return
    
    print(f"\n{BOLD}{CYAN}=== TRAFFIC DATA ==={RESET}")
    print(f"{GREEN}Status: {data.get('status', 'N/A')}{RESET}")
    print(f"{BLUE}Message: {data.get('message', 'N/A')}{RESET}")
    
    traffic_data = data.get('data', {})
    month = traffic_data.get('month', 'N/A')
    
    # Check if this is usage data (has 'usage' key) or logs data (has 'log' key)
    if 'usage' in traffic_data:
        format_traffic_usage(traffic_data, month)
    elif 'log' in traffic_data:
        format_traffic_logs(traffic_data, month)
    else:
        print(f"{RED}Unknown traffic data format{RESET}")

def format_traffic_usage(data, month):
    """Format traffic usage data with comprehensive null handling."""
    # Safe extraction with fallbacks
    usage = data.get('usage') if data else None
    limit = data.get('limit') if data else None
    
    print(f"\n{BOLD}{MAGENTA}=== TRAFFIC USAGE FOR {month} ==={RESET}")
    
    # Usage statistics with safe handling
    if usage and isinstance(usage, dict):
        total = usage.get('total', 0)
        traffic_in = usage.get('in', 0)
        traffic_out = usage.get('out', 0)
        
        # Ensure values are numeric
        total = total if isinstance(total, (int, float)) else 0
        traffic_in = traffic_in if isinstance(traffic_in, (int, float)) else 0
        traffic_out = traffic_out if isinstance(traffic_out, (int, float)) else 0
    else:
        total = traffic_in = traffic_out = 0
    
    print(f"  {BLUE}Total Usage:{RESET} {CYAN}{total:.2f} GB{RESET}")
    print(f"  {BLUE}Incoming:{RESET} {GREEN}{traffic_in:.2f} GB{RESET}")
    print(f"  {BLUE}Outgoing:{RESET} {YELLOW}{traffic_out:.2f} GB{RESET}")
    
    # Limit information with comprehensive null checking
    print(f"\n{BOLD}{CYAN}=== LIMITS & STATUS ==={RESET}")
    
    if limit and isinstance(limit, dict):
        monthly_limit = limit.get('monthly', 0)
        remaining = limit.get('remaining', 0)
        vm_status = limit.get('vm_status', 'unknown')
        additional = limit.get('additional')
        
        # Ensure numeric values
        monthly_limit = monthly_limit if isinstance(monthly_limit, (int, float)) else 0
        remaining = remaining if isinstance(remaining, (int, float)) else 0
        
        print(f"  {BLUE}Monthly Limit:{RESET} {BRIGHT_WHITE}{monthly_limit} GB{RESET}")
        print(f"  {BLUE}Remaining:{RESET} {GREEN}{remaining:.2f} GB{RESET}")
        
        if additional is not None:
            print(f"  {BLUE}Additional:{RESET} {CYAN}{additional} GB{RESET}")
        else:
            print(f"  {BLUE}Additional:{RESET} {BRIGHT_BLACK}None{RESET}")
        
        # VM Status with color coding
        if vm_status:
            status_color = GREEN if vm_status == 'normal' else RED if vm_status == 'limited' else YELLOW
            print(f"  {BLUE}VM Status:{RESET} {status_color}{vm_status.title()}{RESET}")
        
        # Usage percentage and progress bar
        if monthly_limit > 0:
            usage_percent = (total / monthly_limit) * 100
            percent_color = GREEN if usage_percent < 70 else YELLOW if usage_percent < 90 else RED
            print(f"  {BLUE}Usage Percentage:{RESET} {percent_color}{usage_percent:.1f}%{RESET}")
            
            # Progress bar
            bar_length = 30
            filled_length = int(bar_length * total / monthly_limit)
            filled_length = max(0, min(filled_length, bar_length))  # Clamp to valid range
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            bar_color = GREEN if usage_percent < 70 else YELLOW if usage_percent < 90 else RED
            print(f"  {BLUE}Progress:{RESET} {bar_color}[{bar}]{RESET}")
    else:
        print(f"  {BRIGHT_BLACK}No limit information available{RESET}")

def format_traffic_logs(data, month):
    """Format traffic logs data."""
    logs = data.get('log', [])
    
    print(f"\n{BOLD}{MAGENTA}=== TRAFFIC LOGS FOR {month} ==={RESET}")
    
    if logs:
        print(f"{BOLD}{YELLOW}Found {len(logs)} log entries:{RESET}")
        
        # Table header
        print(f"\n{BOLD}{BLUE}{'Date & Time':<20} {'Incoming (MB)':<15} {'Outgoing (MB)':<15}{RESET}")
        print(f"{BRIGHT_BLACK}{'─' * 20} {'─' * 15} {'─' * 15}{RESET}")
        
        total_in = 0
        total_out = 0
        
        for log_entry in logs:
            date_str = log_entry.get('date', 'N/A')
            traffic_in = log_entry.get('in', 0)
            traffic_out = log_entry.get('out', 0)
            
            # Format date
            if date_str != 'N/A':
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    formatted_date = dt.strftime('%m-%d %H:%M:%S')
                except:
                    formatted_date = date_str[:16]  # Fallback
            else:
                formatted_date = 'N/A'
            
            # Add to totals
            if isinstance(traffic_in, (int, float)):
                total_in += traffic_in
            if isinstance(traffic_out, (int, float)):
                total_out += traffic_out
            
            # Print log entry
            print(f"{GREEN}{formatted_date:<20}{RESET} {CYAN}{traffic_in:<15.4f}{RESET} {YELLOW}{traffic_out:<15.4f}{RESET}")
        
        # Summary
        print(f"\n{BOLD}{CYAN}=== LOG SUMMARY ==={RESET}")
        print(f"  {BLUE}Total Entries:{RESET} {BRIGHT_WHITE}{len(logs)}{RESET}")
        print(f"  {BLUE}Total Incoming:{RESET} {CYAN}{total_in:.2f} MB{RESET} ({CYAN}{total_in/1024:.2f} GB{RESET})")
        print(f"  {BLUE}Total Outgoing:{RESET} {YELLOW}{total_out:.2f} MB{RESET} ({YELLOW}{total_out/1024:.2f} GB{RESET})")
        print(f"  {BLUE}Combined Total:{RESET} {BRIGHT_WHITE}{(total_in + total_out):.2f} MB{RESET} ({BRIGHT_WHITE}{(total_in + total_out)/1024:.2f} GB{RESET})")
        
        # Average per entry
        if len(logs) > 0:
            avg_in = total_in / len(logs)
            avg_out = total_out / len(logs)
            print(f"  {BLUE}Average In/Entry:{RESET} {CYAN}{avg_in:.2f} MB{RESET}")
            print(f"  {BLUE}Average Out/Entry:{RESET} {YELLOW}{avg_out:.2f} MB{RESET}")
    else:
        print(f"  {YELLOW}No traffic logs found{RESET}")

def handle_traffic(api_key, target, action):
    """Handle traffic requests with proper error handling."""
    server = find_kvm_server(api_key, target)
    
    if not server:
        print(f"{RED}Server '{target}' not found or is not a KVM server.{RESET}")
        return
    
    server_internal_id = server['internal_id']
    
    if action == 'usage':
        url = f'https://manage.24fire.de/api/kvm/{server_internal_id}/traffic/current'
        try:
            response = requests.get(url,
                                    headers = {
                                        'Content-Type': 'application/x-www-form-urlencoded',
                                        'X-Fire-Apikey': api_key
                                    })
            format_traffic(response)
        except requests.RequestException as e:
            print(f"{RED}Network error fetching traffic usage: {e}{RESET}")
    
    elif action == 'logs':
        url = f'https://manage.24fire.de/api/kvm/{server_internal_id}/traffic/log'
        try:
            response = requests.get(url,
                                    headers = {
                                        'Content-Type': 'application/x-www-form-urlencoded',
                                        'X-Fire-Apikey': api_key
                                    })
            format_traffic(response)
        except requests.RequestException as e:
            print(f"{RED}Network error fetching traffic logs: {e}{RESET}")
    
    else:
        print(f"{RED}Invalid traffic action: {action}. Valid actions: usage, logs{RESET}")

def format_monitoring_outages(data):
    """Format monitoring outages data with comprehensive structure."""
    if not data or 'data' not in data:
        print(f"{RED}No monitoring data available{RESET}")
        return
    
    monitoring_data = data['data']
    statistics = monitoring_data.get('statistic', {})
    incidences = monitoring_data.get('incidences', [])
    
    print(f"\n{BOLD}{CYAN}=== MONITORING OUTAGES ==={RESET}")
    print(f"{GREEN}Status: {data.get('status', 'N/A')}{RESET}")
    print(f"{BLUE}Message: {data.get('message', 'N/A')}{RESET}")
    
    # Statistics section
    if statistics:
        print(f"\n{BOLD}{MAGENTA}=== AVAILABILITY STATISTICS ==={RESET}")
        
        periods = [
            ('LAST_24_HOURS', '24 Hours'),
            ('LAST_7_DAYS', '7 Days'),
            ('LAST_14_DAYS', '14 Days'),
            ('LAST_30_DAYS', '30 Days'),
            ('LAST_90_DAYS', '90 Days'),
            ('LAST_180_DAYS', '180 Days')
        ]
        
        for period_key, period_name in periods:
            if period_key in statistics:
                stat = statistics[period_key]
                availability = stat.get('availability', 0)
                downtime = stat.get('downtime', 0)
                incidences_count = stat.get('incidences', 0)
                longest = stat.get('longest_incidence', 0)
                average = stat.get('average_incidence', 0)
                
                # Color code availability
                if availability >= 99.9:
                    avail_color = GREEN
                elif availability >= 99.0:
                    avail_color = YELLOW
                else:
                    avail_color = RED
                
                print(f"\n{BOLD}{BLUE}=== {period_name.upper()} ==={RESET}")
                print(f"  {BLUE}Availability:{RESET} {avail_color}{availability:.4f}%{RESET}")
                print(f"  {BLUE}Total Downtime:{RESET} {RED}{downtime} minutes{RESET}")
                print(f"  {BLUE}Incidents:{RESET} {YELLOW}{incidences_count}{RESET}")
                print(f"  {BLUE}Longest Incident:{RESET} {RED}{longest} minutes{RESET}")
                print(f"  {BLUE}Average Incident:{RESET} {CYAN}{average:.2f} minutes{RESET}")
    
    # Incidents section
    if incidences:
        print(f"\n{BOLD}{MAGENTA}=== INCIDENT HISTORY ==={RESET}")
        print(f"{BOLD}{YELLOW}Found {len(incidences)} incident(s):{RESET}")
        
        # Sort incidents by start date (most recent first)
        sorted_incidents = sorted(incidences, key=lambda x: x.get('start', ''), reverse=True)
        
        for idx, incident in enumerate(sorted_incidents, 1):
            start_time = incident.get('start', 'N/A')
            end_time = incident.get('end')
            downtime = incident.get('downtime', 0)
            incident_type = incident.get('type', 'UNKNOWN')
            
            # Format dates
            if start_time != 'N/A':
                try:
                    from datetime import datetime
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    formatted_start = start_dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                except:
                    formatted_start = start_time
            else:
                formatted_start = 'N/A'
            
            if end_time:
                try:
                    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    formatted_end = end_dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                    status_text = "Resolved"
                    status_color = GREEN
                    status_icon = "✓"
                except:
                    formatted_end = end_time
                    status_text = "Resolved"
                    status_color = GREEN
                    status_icon = "✓"
            else:
                formatted_end = "Ongoing"
                status_text = "Ongoing"
                status_color = RED
                status_icon = "⚠"
            
            # Color code incident type
            if incident_type == 'PING_TIMEOUT':
                type_color = YELLOW
                type_icon = "🔌"
            elif incident_type == 'VM_STOPPED':
                type_color = RED
                type_icon = "⏹"
            else:
                type_color = CYAN
                type_icon = "❓"
            
            print(f"\n{BOLD}{CYAN}=== INCIDENT #{idx} ==={RESET}")
            print(f"  {BLUE}Type:{RESET} {type_color}{type_icon} {incident_type.replace('_', ' ').title()}{RESET}")
            print(f"  {BLUE}Status:{RESET} {status_color}{status_icon} {status_text}{RESET}")
            print(f"  {BLUE}Started:{RESET} {BRIGHT_WHITE}{formatted_start}{RESET}")
            print(f"  {BLUE}Ended:{RESET} {BRIGHT_WHITE}{formatted_end}{RESET}")
            print(f"  {BLUE}Duration:{RESET} {RED}{downtime} minutes{RESET}")
            
            # Add separator except for last incident
            if idx < len(sorted_incidents):
                print(f"  {BRIGHT_BLACK}{'─' * 50}{RESET}")
        
        # Summary
        total_downtime = sum(incident.get('downtime', 0) for incident in incidences)
        ongoing_incidents = sum(1 for incident in incidences if not incident.get('end'))
        resolved_incidents = len(incidences) - ongoing_incidents
        
        # Incident type breakdown
        type_counts = {}
        for incident in incidences:
            incident_type = incident.get('type', 'UNKNOWN')
            type_counts[incident_type] = type_counts.get(incident_type, 0) + 1
        
        print(f"\n{BOLD}{CYAN}=== INCIDENT SUMMARY ==={RESET}")
        print(f"  {BLUE}Total Incidents:{RESET} {BRIGHT_WHITE}{len(incidences)}{RESET}")
        print(f"  {BLUE}Resolved:{RESET} {GREEN}{resolved_incidents}{RESET}")
        if ongoing_incidents > 0:
            print(f"  {BLUE}Ongoing:{RESET} {RED}{ongoing_incidents}{RESET}")
        print(f"  {BLUE}Total Downtime:{RESET} {RED}{total_downtime} minutes{RESET} ({RED}{total_downtime/60:.1f} hours{RESET})")
        
        if type_counts:
            print(f"\n{BOLD}{CYAN}=== INCIDENT TYPES ==={RESET}")
            for incident_type, count in type_counts.items():
                type_display = incident_type.replace('_', ' ').title()
                if incident_type == 'PING_TIMEOUT':
                    type_color = YELLOW
                elif incident_type == 'VM_STOPPED':
                    type_color = RED
                else:
                    type_color = CYAN
                print(f"  {BLUE}{type_display}:{RESET} {type_color}{count}{RESET}")
    else:
        print(f"  {GREEN}No incidents found - Perfect uptime! 🎉{RESET}")

def format_monitoring_readings(data):
    """Format monitoring readings data with comprehensive structure."""
    if not data or 'data' not in data:
        print(f"{RED}No monitoring data available{RESET}")
        return
    
    timings = data['data'].get('timings', [])
    
    print(f"\n{BOLD}{CYAN}=== MONITORING READINGS ==={RESET}")
    print(f"{GREEN}Status: {data.get('status', 'N/A')}{RESET}")
    print(f"{BLUE}Message: {data.get('message', 'N/A')}{RESET}")
    
    if timings:
        print(f"\n{BOLD}{YELLOW}Found {len(timings)} monitoring readings:{RESET}")
        
        # Sort by date (most recent first)
        sorted_timings = sorted(timings, key=lambda x: x.get('date', ''), reverse=True)
        
        # Table header
        print(f"\n{BOLD}{BLUE}{'Date & Time':<20} {'CPU %':<8} {'Memory %':<10} {'Ping (ms)':<10}{RESET}")
        print(f"{BRIGHT_BLACK}{'─' * 20} {'─' * 8} {'─' * 10} {'─' * 10}{RESET}")
        
        cpu_values = []
        mem_values = []
        ping_values = []
        
        for timing in sorted_timings:
            date_str = timing.get('date', 'N/A')
            cpu = timing.get('cpu', 'N/A')
            mem = timing.get('mem', 'N/A')
            ping = timing.get('ping', 'N/A')
            
            # Format date
            if date_str != 'N/A':
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    formatted_date = dt.strftime('%m-%d %H:%M:%S')
                except:
                    formatted_date = date_str[:16]
            else:
                formatted_date = 'N/A'
            
            # Color code values based on thresholds
            if cpu != 'N/A':
                try:
                    cpu_float = float(cpu)
                    cpu_values.append(cpu_float)
                    if cpu_float < 50:
                        cpu_color = GREEN
                    elif cpu_float < 80:
                        cpu_color = YELLOW
                    else:
                        cpu_color = RED
                    cpu_display = f"{cpu_float:.1f}%"
                except:
                    cpu_color = BRIGHT_BLACK
                    cpu_display = str(cpu)
            else:
                cpu_color = BRIGHT_BLACK
                cpu_display = 'N/A'
            
            if mem != 'N/A':
                try:
                    mem_float = float(mem)
                    mem_values.append(mem_float)
                    if mem_float < 70:
                        mem_color = GREEN
                    elif mem_float < 90:
                        mem_color = YELLOW
                    else:
                        mem_color = RED
                    mem_display = f"{mem_float:.1f}%"
                except:
                    mem_color = BRIGHT_BLACK
                    mem_display = str(mem)
            else:
                mem_color = BRIGHT_BLACK
                mem_display = 'N/A'
            
            if ping != 'N/A':
                try:
                    ping_int = int(ping)
                    ping_values.append(ping_int)
                    if ping_int < 50:
                        ping_color = GREEN
                    elif ping_int < 100:
                        ping_color = YELLOW
                    else:
                        ping_color = RED
                    ping_display = f"{ping_int}ms"
                except:
                    ping_color = BRIGHT_BLACK
                    ping_display = str(ping)
            else:
                ping_color = BRIGHT_BLACK
                ping_display = 'N/A'
            
            print(f"{BRIGHT_WHITE}{formatted_date:<20}{RESET} {cpu_color}{cpu_display:<8}{RESET} {mem_color}{mem_display:<10}{RESET} {ping_color}{ping_display:<10}{RESET}")
        
        # Statistics summary
        if cpu_values or mem_values or ping_values:
            print(f"\n{BOLD}{CYAN}=== PERFORMANCE SUMMARY ==={RESET}")
            
            if cpu_values:
                avg_cpu = sum(cpu_values) / len(cpu_values)
                max_cpu = max(cpu_values)
                min_cpu = min(cpu_values)
                print(f"  {BLUE}CPU Usage:{RESET}")
                print(f"    {BLUE}Average:{RESET} {CYAN}{avg_cpu:.2f}%{RESET}")
                print(f"    {BLUE}Maximum:{RESET} {RED}{max_cpu:.2f}%{RESET}")
                print(f"    {BLUE}Minimum:{RESET} {GREEN}{min_cpu:.2f}%{RESET}")
            
            if mem_values:
                avg_mem = sum(mem_values) / len(mem_values)
                max_mem = max(mem_values)
                min_mem = min(mem_values)
                print(f"  {BLUE}Memory Usage:{RESET}")
                print(f"    {BLUE}Average:{RESET} {CYAN}{avg_mem:.2f}%{RESET}")
                print(f"    {BLUE}Maximum:{RESET} {RED}{max_mem:.2f}%{RESET}")
                print(f"    {BLUE}Minimum:{RESET} {GREEN}{min_mem:.2f}%{RESET}")
            
            if ping_values:
                avg_ping = sum(ping_values) / len(ping_values)
                max_ping = max(ping_values)
                min_ping = min(ping_values)
                print(f"  {BLUE}Ping Response:{RESET}")
                print(f"    {BLUE}Average:{RESET} {CYAN}{avg_ping:.1f}ms{RESET}")
                print(f"    {BLUE}Maximum:{RESET} {RED}{max_ping}ms{RESET}")
                print(f"    {BLUE}Minimum:{RESET} {GREEN}{min_ping}ms{RESET}")
            
            # Performance indicators
            print(f"\n{BOLD}{CYAN}=== PERFORMANCE INDICATORS ==={RESET}")
            
            if cpu_values:
                high_cpu_count = sum(1 for cpu in cpu_values if cpu > 80)
                if high_cpu_count > 0:
                    print(f"  {RED}⚠ High CPU usage detected in {high_cpu_count} readings{RESET}")
                else:
                    print(f"  {GREEN}✓ CPU usage within normal range{RESET}")
            
            if mem_values:
                high_mem_count = sum(1 for mem in mem_values if mem > 90)
                if high_mem_count > 0:
                    print(f"  {RED}⚠ High memory usage detected in {high_mem_count} readings{RESET}")
                else:
                    print(f"  {GREEN}✓ Memory usage within normal range{RESET}")

            if ping_values:
                high_ping_count = sum(1 for ping in ping_values if ping > 100)
                if high_ping_count > 0:
                    print(f"  {RED}⚠ High ping detected in {high_ping_count} readings{RESET}")
                else:
                    print(f"  {GREEN}✓ Network latency within acceptable range{RESET}")
    else:
        print(f"  {YELLOW}No monitoring readings found{RESET}")

def handle_monitoring(api_key, target, action):
    """Handle monitoring requests with proper error handling."""
    server = find_kvm_server(api_key, target)
    
    if not server:
        print(f"{RED}Server '{target}' not found or is not a KVM server.{RESET}")
        return
    
    server_internal_id = server['internal_id']
    
    if action == 'outages':
        url = f'https://manage.24fire.de/api/kvm/{server_internal_id}/monitoring/incidences'
        try:
            response = requests.get(url,
                                    headers = {
                                        'Content-Type': 'application/x-www-form-urlencoded',
                                        'X-Fire-Apikey': api_key
                                    })
            
            if response.status_code == 200:
                json_response = response.json()
                if json_response.get('status') == 'success':
                    format_monitoring_outages(json_response)
                else:
                    print(f"{RED}Failed to fetch monitoring outages: {json_response.get('message', 'Unknown error')}{RESET}")
            else:
                print(f"{RED}Failed to fetch monitoring outages for {server['name']} - HTTP {response.status_code}{RESET}")
                
        except requests.RequestException as e:
            print(f"{RED}Network error fetching monitoring outages: {e}{RESET}")
    
    elif action == 'reading':
        url = f'https://manage.24fire.de/api/kvm/{server_internal_id}/monitoring/timings'
        try:
            response = requests.get(url,
                                    headers = {
                                        'Content-Type': 'application/x-www-form-urlencoded',
                                        'X-Fire-Apikey': api_key
                                    })
            
            if response.status_code == 200:
                json_response = response.json()
                if json_response.get('status') == 'success':
                    format_monitoring_readings(json_response)
                else:
                    print(f"{RED}Failed to fetch monitoring readings: {json_response.get('message', 'Unknown error')}{RESET}")
            else:
                print(f"{RED}Failed to fetch monitoring readings for {server['name']} - HTTP {response.status_code}{RESET}")
                
        except requests.RequestException as e:
            print(f"{RED}Network error fetching monitoring readings: {e}{RESET}")
    
    else:
        print(f"{RED}Invalid monitoring action: {action}. Valid actions: reading, outages{RESET}")

def format_ddos_protection(data):
    """Format DDoS protection data with comprehensive structure."""
    if not data or 'data' not in data:
        print(f"{RED}No DDoS protection data available{RESET}")
        return
    
    ddos_data = data['data']
    
    print(f"\n{BOLD}{CYAN}=== DDOS PROTECTION STATUS ==={RESET}")
    print(f"{GREEN}Status: {data.get('status', 'N/A')}{RESET}")
    print(f"{BLUE}Message: {data.get('message', 'N/A')}{RESET}")
    
    if ddos_data:
        ip_count = len(ddos_data)
        print(f"\n{BOLD}{YELLOW}Found {ip_count} IP address(es) with DDoS protection:{RESET}")
        
        # Track statistics
        layer4_stats = {'off': 0, 'dynamic': 0, 'permanent': 0}
        layer7_stats = {'off': 0, 'on': 0}
        
        for idx, (ip_address, protection_settings) in enumerate(ddos_data.items(), 1):
            layer4_status = protection_settings.get('layer4', 'unknown')
            layer7_status = protection_settings.get('layer7', 'unknown')
            
            # Update statistics
            if layer4_status in layer4_stats:
                layer4_stats[layer4_status] += 1
            if layer7_status in layer7_stats:
                layer7_stats[layer7_status] += 1
            
            print(f"\n{BOLD}{MAGENTA}=== IP ADDRESS #{idx} ==={RESET}")
            print(f"  {BLUE}IP Address:{RESET} {BRIGHT_WHITE}{ip_address}{RESET}")
            
            # Layer 4 Protection with color coding and icons
            if layer4_status == 'off':
                layer4_color = RED
                layer4_icon = "❌"
                layer4_desc = "Disabled"
            elif layer4_status == 'dynamic':
                layer4_color = YELLOW
                layer4_icon = "🔄"
                layer4_desc = "Dynamic (Auto-enabled when attack detected)"
            elif layer4_status == 'permanent':
                layer4_color = GREEN
                layer4_icon = "🛡️"
                layer4_desc = "Always Active"
            else:
                layer4_color = BRIGHT_BLACK
                layer4_icon = "❓"
                layer4_desc = "Unknown Status"
            
            print(f"  {BLUE}Layer 4 Protection:{RESET} {layer4_color}{layer4_icon} {layer4_status.title()}{RESET}")
            print(f"    {BRIGHT_BLACK}└─ {layer4_desc}{RESET}")
            
            # Layer 7 Protection with color coding and icons
            if layer7_status == 'off':
                layer7_color = RED
                layer7_icon = "❌"
                layer7_desc = "Disabled"
            elif layer7_status == 'on':
                layer7_color = GREEN
                layer7_icon = "🛡️"
                layer7_desc = "Active"
            else:
                layer7_color = BRIGHT_BLACK
                layer7_icon = "❓"
                layer7_desc = "Unknown Status"
            
            print(f"  {BLUE}Layer 7 Protection:{RESET} {layer7_color}{layer7_icon} {layer7_status.title()}{RESET}")
            print(f"    {BRIGHT_BLACK}└─ {layer7_desc}{RESET}")
            
            # Protection level indicator
            protection_level = 0
            if layer4_status == 'dynamic':
                protection_level += 1
            elif layer4_status == 'permanent':
                protection_level += 2
            if layer7_status == 'on':
                protection_level += 2
            
            if protection_level == 0:
                level_color = RED
                level_text = "No Protection"
                level_icon = "🚨"
            elif protection_level <= 2:
                level_color = YELLOW
                level_text = "Basic Protection"
                level_icon = "⚠️"
            elif protection_level <= 3:
                level_color = CYAN
                level_text = "Good Protection"
                level_icon = "🔒"
            else:
                level_color = GREEN
                level_text = "Maximum Protection"
                level_icon = "🛡️"
            
            print(f"  {BLUE}Protection Level:{RESET} {level_color}{level_icon} {level_text}{RESET}")
            
            # Add separator except for last IP
            if idx < ip_count:
                print(f"  {BRIGHT_BLACK}{'─' * 50}{RESET}")
        
        # Summary statistics
        print(f"\n{BOLD}{CYAN}=== PROTECTION SUMMARY ==={RESET}")
        print(f"  {BLUE}Total IP Addresses:{RESET} {BRIGHT_WHITE}{ip_count}{RESET}")
        
        print(f"\n{BOLD}{BLUE}Layer 4 Protection Status:{RESET}")
        if layer4_stats['permanent'] > 0:
            print(f"  {GREEN}🛡️  Permanent:{RESET} {GREEN}{layer4_stats['permanent']}{RESET}")
        if layer4_stats['dynamic'] > 0:
            print(f"  {YELLOW}🔄 Dynamic:{RESET} {YELLOW}{layer4_stats['dynamic']}{RESET}")
        if layer4_stats['off'] > 0:
            print(f"  {RED}❌ Disabled:{RESET} {RED}{layer4_stats['off']}{RESET}")
        
        print(f"\n{BOLD}{BLUE}Layer 7 Protection Status:{RESET}")
        if layer7_stats['on'] > 0:
            print(f"  {GREEN}🛡️  Active:{RESET} {GREEN}{layer7_stats['on']}{RESET}")
        if layer7_stats['off'] > 0:
            print(f"  {RED}❌ Disabled:{RESET} {RED}{layer7_stats['off']}{RESET}")
        
        # Security recommendations
        print(f"\n{BOLD}{CYAN}=== SECURITY RECOMMENDATIONS ==={RESET}")
        
        recommendations = []
        if layer4_stats['off'] > 0:
            recommendations.append(f"{YELLOW}⚠️  Consider enabling Layer 4 protection for {layer4_stats['off']} IP(s){RESET}")
        
        if layer7_stats['off'] > 0:
            recommendations.append(f"{YELLOW}⚠️  Consider enabling Layer 7 protection for {layer7_stats['off']} IP(s){RESET}")
        
        if layer4_stats['dynamic'] > 0:
            recommendations.append(f"{CYAN}💡 {layer4_stats['dynamic']} IP(s) have dynamic Layer 4 protection - consider permanent for high-risk servers{RESET}")
        
        if not recommendations:
            recommendations.append(f"{GREEN}✅ All IP addresses have optimal DDoS protection configured{RESET}")
        
        for recommendation in recommendations:
            print(f"  {recommendation}")
        
        # Protection effectiveness indicator
        total_protected = layer4_stats['permanent'] + layer4_stats['dynamic'] + layer7_stats['on']
        total_possible = ip_count * 2  # Each IP can have both Layer 4 and Layer 7
        protection_percentage = (total_protected / total_possible) * 100 if total_possible > 0 else 0
        
        print(f"\n{BOLD}{CYAN}=== OVERALL PROTECTION SCORE ==={RESET}")
        if protection_percentage >= 80:
            score_color = GREEN
            score_icon = "🛡️"
            score_text = "Excellent"
        elif protection_percentage >= 60:
            score_color = CYAN
            score_icon = "🔒"
            score_text = "Good"
        elif protection_percentage >= 40:
            score_color = YELLOW
            score_icon = "⚠️"
            score_text = "Fair"
        else:
            score_color = RED
            score_icon = "🚨"
            score_text = "Poor"
        
        # Progress bar for protection score
        bar_length = 20
        filled_length = int(bar_length * protection_percentage / 100)
        filled_length = max(0, min(filled_length, bar_length))
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        print(f"  {BLUE}Protection Score:{RESET} {score_color}{score_icon} {protection_percentage:.1f}% - {score_text}{RESET}")
        print(f"  {BLUE}Progress:{RESET} {score_color}[{bar}]{RESET}")
        
    else:
        print(f"  {YELLOW}No DDoS protection information available{RESET}")

def handle_ddos(api_key, target):
    """Handle DDoS protection requests with proper error handling."""
    server = find_kvm_server(api_key, target)
    
    if not server:
        print(f"{RED}Server '{target}' not found or is not a KVM server.{RESET}")
        return
    
    server_internal_id = server['internal_id']
    
    url = f'https://manage.24fire.de/api/kvm/{server_internal_id}/ddos'
    try:
        response = requests.get(url,
                                headers = {
                                    'Content-Type': 'application/x-www-form-urlencoded',
                                    'X-Fire-Apikey': api_key
                                })
        
        if response.status_code == 200:
            json_response = response.json()
            if json_response.get('status') == 'success':
                format_ddos_protection(json_response)
            else:
                print(f"{RED}Failed to fetch DDoS protection settings: {json_response.get('message', 'Unknown error')}{RESET}")
        else:
            print(f"{RED}Failed to fetch DDoS protection settings for {server['name']} - HTTP {response.status_code}{RESET}")
            
    except requests.RequestException as e:
        print(f"{RED}Network error fetching DDoS protection settings: {e}{RESET}")

def install_automations(api_key, target, script_url=None):
    """Install automations script on target server."""
    server = find_kvm_server(api_key, target)
    
    if not server:
        print(f"{RED}Server '{target}' not found or is not a KVM server.{RESET}")
        return
    
    if 1==1:
        print(f"{RED}The Automations system is not finished yet. We are Sorry! :({RESET}")
        sys.exit(0)
    
    # Default to your automations repository
    if not script_url:
        script_url = "https://raw.githubusercontent.com/LolgamerHDDE/24fire-api-cli-automations/main/install.sh"
    
    print(f"{BLUE}Installing automations on {server['name']}...{RESET}")
    print(f"{YELLOW}This will download and execute: {script_url}{RESET}")
    
    # Confirm with user
    confirm = input(f"{YELLOW}Continue? (y/N): {RESET}").strip().lower()
    if confirm != 'y':
        print(f"{YELLOW}Installation cancelled.{RESET}")
        return
    
    try:
        # Download the script
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.sh', delete=False) as temp_file:
            print(f"{BLUE}Downloading installation script...{RESET}")
            with urllib.request.urlopen(script_url) as response:
                script_content = response.read().decode('utf-8')
            
            temp_file.write(script_content)
            temp_file.flush()
            
            # Make executable
            os.chmod(temp_file.name, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
            
            print(f"{BLUE}Executing installation script...{RESET}")
            
            # Execute the script
            result = subprocess.run(['bash', temp_file.name], 
                                  capture_output=True, 
                                  text=True)
            
            if result.returncode == 0:
                print(f"{GREEN}✓ Automations installed successfully on {server['name']}{RESET}")
                if result.stdout:
                    print(f"{CYAN}Output:{RESET}")
                    print(result.stdout)
            else:
                print(f"{RED}✗ Installation failed{RESET}")
                if result.stderr:
                    print(f"{RED}Error:{RESET}")
                    print(result.stderr)
            
            # Clean up
            os.unlink(temp_file.name)
            
    except Exception as e:
        print(f"{RED}Error during installation: {e}{RESET}")

def find_domain(api_key, domain_identifier):
    """Find domain by name or internal_id and return domain info."""
    try:
        # Make direct API call to get raw service data
        url = 'https://manage.24fire.de/api/account/services'
        response = requests.get(url, headers={'X-Fire-Apikey': api_key})
        
        if response.status_code != 200:
            return None
            
        json_response = response.json()
        services = json_response.get('data', {}).get('services', {})
        
        # Look specifically in the DOMAIN section
        domains = services.get('DOMAIN', [])
        
        for domain in domains:
            if (domain['name'] == domain_identifier or 
                domain['internal_id'] == domain_identifier):
                # Return domain info with type added for consistency
                domain_info = domain.copy()
                domain_info['type'] = 'DOMAIN'
                return domain_info
        
        return None
    except Exception as e:
        print(f"{RED}Error finding domain: {e}{RESET}")
        return None
    
def handle_dns_remove(api_key, target, record_id):
    """Remove a DNS record from a domain."""
    domain = find_domain(api_key, target)
    
    if not domain:
        print(f"{RED}Domain '{target}' not found.{RESET}")
        return
    
    domain_internal_id = domain['internal_id']
    
    url = f'https://manage.24fire.de/api/domain/{domain_internal_id}/dns/remove'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Fire-Apikey': api_key
    }
    data = {'record_id': record_id}
    
    try:
        response = requests.delete(url, headers=headers, data=data)
        
        if response.status_code == 200:
            json_response = response.json()
            if json_response.get('status') == 'success':
                print(f"{GREEN}✓ DNS record removed successfully from {domain['name']}{RESET}")
                print(f"{BLUE}Message: {json_response.get('message', 'DNS record removed')}{RESET}")
            else:
                print(f"{RED}✗ Failed to remove DNS record: {json_response.get('message', 'Unknown error')}{RESET}")
        else:
            print(f"{RED}✗ Failed to remove DNS record - HTTP {response.status_code}{RESET}")
            
    except requests.RequestException as e:
        print(f"{RED}✗ Network error removing DNS record: {e}{RESET}")

def handle_dns_add(api_key, target, dns_type, name, data):
    """Add a DNS record to a domain."""
    domain = find_domain(api_key, target)
    
    if not domain:
        print(f"{RED}Domain '{target}' not found.{RESET}")
        return
    
    domain_internal_id = domain['internal_id']
    
    url = f'https://manage.24fire.de/api/domain/{domain_internal_id}/dns/add'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Fire-Apikey': api_key
    }
    request_data = {
        'type': dns_type,
        'name': name,
        'data': data
    }
    
    try:
        response = requests.put(url, headers=headers, data=request_data)
        
        if response.status_code == 200:
            json_response = response.json()
            if json_response.get('status') == 'success':
                print(f"{GREEN}✓ DNS record added successfully to {domain['name']}{RESET}")
                print(f"{BLUE}Type: {dns_type}, Name: {name}, Data: {data}{RESET}")
                print(f"{BLUE}Message: {json_response.get('message', 'DNS record added')}{RESET}")
            else:
                print(f"{RED}✗ Failed to add DNS record: {json_response.get('message', 'Unknown error')}{RESET}")
        else:
            print(f"{RED}✗ Failed to add DNS record - HTTP {response.status_code}{RESET}")
            
    except requests.RequestException as e:
        print(f"{RED}✗ Network error adding DNS record: {e}{RESET}")

def handle_dns_edit(api_key, target, record_id, dns_type, name, data):
    """Edit a DNS record in a domain."""
    domain = find_domain(api_key, target)
    
    if not domain:
        print(f"{RED}Domain '{target}' not found.{RESET}")
        return
    
    domain_internal_id = domain['internal_id']
    
    url = f'https://manage.24fire.de/api/domain/{domain_internal_id}/dns/edit'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Fire-Apikey': api_key
    }
    request_data = {
        'record_id': record_id,
        'type': dns_type,
        'name': name,
        'data': data
    }
    
    try:
        response = requests.post(url, headers=headers, data=request_data)
        
        if response.status_code == 200:
            json_response = response.json()
            if json_response.get('status') == 'success':
                print(f"{GREEN}✓ DNS record edited successfully in {domain['name']}{RESET}")
                print(f"{BLUE}Record ID: {record_id}, Type: {dns_type}, Name: {name}, Data: {data}{RESET}")
                print(f"{BLUE}Message: {json_response.get('message', 'DNS record changed')}{RESET}")
            else:
                print(f"{RED}✗ Failed to edit DNS record: {json_response.get('message', 'Unknown error')}{RESET}")
        else:
            print(f"{RED}✗ Failed to edit DNS record - HTTP {response.status_code}{RESET}")
            
    except requests.RequestException as e:
        print(f"{RED}✗ Network error editing DNS record: {e}{RESET}")

def handle_dns_list(api_key, target):
    """List all DNS records for a domain."""
    domain = find_domain(api_key, target)
    
    if not domain:
        print(f"{RED}Domain '{target}' not found.{RESET}")
        return
    
    domain_internal_id = domain['internal_id']
    
    url = f'https://manage.24fire.de/api/domain/{domain_internal_id}/dns'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Fire-Apikey': api_key
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            json_response = response.json()
            if json_response.get('status') == 'success':
                format_dns_records(json_response, domain['name'])
            else:
                print(f"{RED}Failed to fetch DNS records: {json_response.get('message', 'Unknown error')}{RESET}")
        else:
            print(f"{RED}Failed to fetch DNS records for {domain['name']} - HTTP {response.status_code}{RESET}")
            
    except requests.RequestException as e:
        print(f"{RED}Network error fetching DNS records: {e}{RESET}")

def format_dns_records(data, domain_name):
    """Format DNS records data with comprehensive structure."""
    if not data or 'data' not in data:
        print(f"{RED}No DNS data available{RESET}")
        return
    
    dns_records = data['data']
    
    print(f"\n{BOLD}{CYAN}=== DNS RECORDS FOR {domain_name.upper()} ==={RESET}")
    print(f"{GREEN}Status: {data.get('status', 'N/A')}{RESET}")
    print(f"{BLUE}Message: {data.get('message', 'N/A')}{RESET}")
    
    if dns_records:
        print(f"\n{BOLD}{YELLOW}Found {len(dns_records)} DNS record(s):{RESET}")
        
        # Table header
        print(f"\n{BOLD}{BLUE}{'Record ID':<12} {'Type':<8} {'Name':<20} {'Data':<35} {'TTL':<8}{RESET}")
        print(f"{BRIGHT_BLACK}{'─' * 12} {'─' * 8} {'─' * 20} {'─' * 35} {'─' * 8}{RESET}")
        
        # Group records by type for statistics
        record_types = {}
        
        for record in dns_records:
            record_id = record.get('record_id', 'N/A')
            record_type = record.get('type', 'N/A')
            record_name = record.get('name', 'N/A')
            record_data = record.get('data', 'N/A')
            record_ttl = record.get('ttl', 'N/A')
            
            # Count record types
            if record_type in record_types:
                record_types[record_type] += 1
            else:
                record_types[record_type] = 1
            
            # Color code by record type
            if record_type == 'A':
                type_color = GREEN
                type_icon = "🌐"
            elif record_type == 'AAAA':
                type_color = CYAN
                type_icon = "🌐"
            elif record_type == 'CNAME':
                type_color = YELLOW
                type_icon = "🔗"
            elif record_type == 'MX':
                type_color = MAGENTA
                type_icon = "📧"
            elif record_type == 'TXT':
                type_color = BLUE
                type_icon = "📝"
            elif record_type == 'NS':
                type_color = BRIGHT_CYAN
                type_icon = "🗂️"
            else:
                type_color = WHITE
                type_icon = "❓"
            
            # Truncate long data for table display
            display_data = str(record_data)
            if len(display_data) > 33:
                display_data = display_data[:30] + "..."
            
            display_name = str(record_name)
            if len(display_name) > 18:
                display_name = display_name[:15] + "..."
            
            # TTL color coding
            ttl_color = GREEN if record_ttl == 300 else YELLOW if record_ttl < 3600 else CYAN
            
            print(f"{BRIGHT_WHITE}{str(record_id):<12}{RESET} {type_color}{record_type:<8}{RESET} {WHITE}{display_name:<20}{RESET} {CYAN}{display_data:<35}{RESET} {ttl_color}{str(record_ttl):<8}{RESET}")
        
        # Summary by record type
        print(f"\n{BOLD}{CYAN}=== RECORD TYPE SUMMARY ==={RESET}")
        for record_type, count in sorted(record_types.items()):
            if record_type == 'A':
                type_color = GREEN
                type_icon = "🌐"
            elif record_type == 'AAAA':
                type_color = CYAN
                type_icon = "🌐"
            elif record_type == 'CNAME':
                type_color = YELLOW
                type_icon = "🔗"
            elif record_type == 'MX':
                type_color = MAGENTA
                type_icon = "📧"
            elif record_type == 'TXT':
                type_color = BLUE
                type_icon = "📝"
            elif record_type == 'NS':
                type_color = BRIGHT_CYAN
                type_icon = "🗂️"
            else:
                type_color = WHITE
                type_icon = "❓"
            
            print(f"  {type_color}{type_icon} {record_type}:{RESET} {BRIGHT_WHITE}{count} record(s){RESET}")
        
        print(f"\n{BOLD}{CYAN}=== TOTAL RECORDS ==={RESET}")
        print(f"  {BLUE}Total DNS Records:{RESET} {BRIGHT_WHITE}{len(dns_records)}{RESET}")
        
    else:
        print(f"  {YELLOW}No DNS records found{RESET}")

def get_api_key():
    """Get API key from command line arguments or environment variable."""
    parser = argparse.ArgumentParser(description='24Fire API CLI Tool')
    parser.add_argument('-a', '--api-key', 
                       help='API key for 24Fire (overrides .env file)',
                       type=str)
    parser.add_argument('-S', '--start',
                       help='Start a KVM server by name or internal ID',
                       type=str)
    parser.add_argument('-s', '--stop',
                       help='Stop a KVM server by name or internal ID',
                       type=str)
    parser.add_argument('-r', '--restart',
                       help='Restart a KVM server by name or internal ID',
                       type=str)
    parser.add_argument('-b', '--backup',
                        help="Backup action: list, create, restore, delete",
                        type=str,
                        choices=['list', 'create', 'restore', 'delete'])
    parser.add_argument('-t', '--target',
                        help="Target Service (Required by Backup)",
                        type=str)
    parser.add_argument('--backup-id',
                        help="Backup ID (Required for restore/delete operations)",
                        type=str)
    parser.add_argument('-T', '--traffic',
                        help="Traffic action: usage, logs",
                        type=str,
                        choices=['usage', 'logs'])
    parser.add_argument('-m', '--monitoring',
                        help="Displays Monitoring Info (requires: -t, --target)",
                        type=str,
                        choices=['reading', 'outages'])
    parser.add_argument('-d', '--ddos',
                        help="Display DDoS protection settings (requires: -t, --target)",
                        action='store_true')
    parser.add_argument('-i', '--install',
                        help="Install automations on target server (requires: -t, --target)",
                        action='store_true')
    parser.add_argument('-su', '--script-url',
                        help="Custom script URL for automations installation",
                        type=str)
    parser.add_argument('-dns',
                        help="DNS Management action: add, edit, remove, or leave empty to list records",
                        type=str,
                        nargs='?',
                        const='',
                        choices=['add', 'edit', 'remove', ''])
    parser.add_argument("-rm", '--remove',
                        help="Record ID to remove (used with -dns remove)")
    parser.add_argument("-A", '--add',
                        help="Add DNS record: type,name,data (used with -dns add)")
    parser.add_argument("-e", '--edit',
                        help="Edit DNS record: record_id,type,name,data (used with -dns edit)")
    
    args = parser.parse_args()
    
    # Handle server control operations
    if args.start or args.stop or args.restart:
        api_key = args.api_key or os.getenv("FIRE_API_KEY") or "None"
        
        if args.start:
            control_kvm_server(api_key, args.start, "start")
        elif args.stop:
            control_kvm_server(api_key, args.stop, "stop")
        elif args.restart:
            control_kvm_server(api_key, args.restart, "restart")
        
        sys.exit(0)
    
    # Handle backup operations
    if args.backup:
        api_key = args.api_key or os.getenv("FIRE_API_KEY") or "None"
        
        # Check if target is provided
        if not args.target:
            print(f"{RED}Error: --target is required for backup operations{RESET}")
            print(f"{YELLOW}Usage: 24fire -b <action> -t <server_name_or_id>{RESET}")
            sys.exit(1)
        
        # Check if backup_id is required for restore/delete
        if args.backup in ['restore', 'delete'] and not args.backup_id:
            print(f"{RED}Error: --backup-id is required for {args.backup} operations{RESET}")
            print(f"{YELLOW}Usage: 24fire -b {args.backup} -t <server> --backup-id <backup_id>{RESET}")
            sys.exit(1)
        
        handle_backup_request(api_key, args.backup, args.target, args.backup_id)
        sys.exit(0)

    # Handle traffic operations
    if args.traffic:
        api_key = args.api_key or os.getenv("FIRE_API_KEY") or "None"
        
        # Check if target is provided
        if not args.target:
            print(f"{RED}Error: --target is required for traffic operations{RESET}")
            print(f"{YELLOW}Usage: python main.py --traffic <action> -t <server_name_or_id>{RESET}")
            sys.exit(1)
        
        handle_traffic(api_key, args.target, args.traffic)
        sys.exit(0)
    
    if args.monitoring:
        api_key = args.api_key or os.getenv("FIRE_API_KEY") or "None"

        # Check if target is provided
        if not args.target:
            print(f"{RED}Error: --target is required for monitoring operations{RESET}")
            print(f"{YELLOW}Usage: python main.py --monitoring <action> -t <server_name_or_id>{RESET}")
            sys.exit(1)
        
        handle_monitoring(api_key, args.target, args.monitoring)
        sys.exit(0)

    # Handle automations installation
    if args.install:
        api_key = args.api_key or os.getenv("FIRE_API_KEY") or "None"
        
        if not args.target:
            print(f"{RED}Error: --target is required for automations installation{RESET}")
            print(f"{YELLOW}Usage: 24fire --install-automations -t <server_name_or_id>{RESET}")
            sys.exit(1)
        
        install_automations(api_key, args.target, args.script_url)
        sys.exit(0)

    # Handle DNS operations
    if args.dns is not None:
        api_key = args.api_key or os.getenv("FIRE_API_KEY") or "None"
        
        if not args.target:
            print(f"{RED}Error: --target is required for DNS operations{RESET}")
            print(f"{YELLOW}Usage: python main.py -dns [action] -t <domain_name_or_id>{RESET}")
            sys.exit(1)
        
        if args.dns == 'remove':
            if not args.remove:
                print(f"{RED}Error: --remove <record_id> is required for DNS remove operations{RESET}")
                sys.exit(1)
            handle_dns_remove(api_key, args.target, args.remove)
        
        elif args.dns == 'add':
            if not args.add:
                print(f"{RED}Error: --add <type,name,data> is required for DNS add operations{RESET}")
                print(f"{YELLOW}Example: python main.py -dns add -t domain.com --add A,www,192.168.1.1{RESET}")
                sys.exit(1)
            
            try:
                dns_type, name, data = args.add.split(',', 2)
                handle_dns_add(api_key, args.target, dns_type.strip(), name.strip(), data.strip())
            except ValueError:
                print(f"{RED}Error: Invalid format for --add. Use: type,name,data{RESET}")
                sys.exit(1)
        
        elif args.dns == 'edit':
            if not args.edit:
                print(f"{RED}Error: --edit <record_id,type,name,data> is required for DNS edit operations{RESET}")
                print(f"{YELLOW}Example: python main.py -dns edit -t domain.com --edit 123,A,www,192.168.1.2{RESET}")
                sys.exit(1)
            
            try:
                record_id, dns_type, name, data = args.edit.split(',', 3)
                handle_dns_edit(api_key, args.target, record_id.strip(), dns_type.strip(), name.strip(), data.strip())
            except ValueError:
                print(f"{RED}Error: Invalid format for --edit. Use: record_id,type,name,data{RESET}")
                sys.exit(1)
        
        elif args.dns == '':
            # Handle empty -dns argument (list records)
            handle_dns_list(api_key, args.target)
        
        else:
            print(f"{RED}Invalid DNS action: {args.dns}. Valid actions: add, edit, remove (or leave empty to list){RESET}")
        
        sys.exit(0)

    # Handle DDoS operations
    if args.ddos:
        api_key = args.api_key or os.getenv("FIRE_API_KEY") or "None"

        # Check if target is provided
        if not args.target:
            print(f"{RED}Error: --target is required for DDoS operations{RESET}")
            print(f"{YELLOW}Usage: python main.py --ddos -t <server_name_or_id>{RESET}")
            sys.exit(1)
        
        handle_ddos(api_key, args.target)
        sys.exit(0)

    # Priority: command line argument > environment variable > None
    if args.api_key:
        return args.api_key
    
    env_api_key = os.getenv("FIRE_API_KEY")
    if env_api_key:
        return env_api_key
    
    return "None"

# Define API key with priority handling
API_KEY = get_api_key()

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
        sys.exit(1)

def fetch_infos(api_key, internal_id, service_type):
    """Fetch service infos from API."""
    kvm_url = f"https://manage.24fire.de/api/kvm/{internal_id}/config"
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
