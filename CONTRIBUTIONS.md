# Contributing to 24fire API CLI

Thank you for your interest in contributing to the 24fire API CLI! This document provides guidelines and information for contributors.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Contributing Process](#contributing-process)
- [Feature Requests](#feature-requests)
- [Bug Reports](#bug-reports)
- [API Integration](#api-integration)
- [Testing](#testing)
- [Documentation](#documentation)

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Basic understanding of REST APIs
- Familiarity with the 24fire hosting platform

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/24fire-api-cli.git
   cd 24fire-api-cli
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Environment**
   ```bash
   cp .env.example .env
   # Add your 24fire API key to .env
   echo "FIRE_API_KEY=your_api_key_here" >> .env
   ```

5. **Test Installation**
   ```bash
   python main.py
   ```

## Code Style Guidelines

### Python Style

- Follow PEP 8 guidelines
- Use 4 spaces for indentation
- Maximum line length: 88 characters
- Use descriptive variable and function names

### Color Coding Standards

The CLI uses ANSI color codes for output formatting:

```python
# Status Colors
GREEN = "\033[32m"    # Success messages
RED = "\033[31m"      # Error messages  
YELLOW = "\033[33m"   # Warnings/prompts
BLUE = "\033[34m"     # Information labels
CYAN = "\033[36m"     # Data values
MAGENTA = "\033[35m"  # Section headers
```

### Function Structure

Follow this pattern for new API functions:

```python
def handle_new_feature(api_key, target, action):
    """Handle new feature requests with proper error handling."""
    server = find_kvm_server(api_key, target)
    
    if not server:
        print(f"{RED}Server '{target}' not found or is not a KVM server.{RESET}")
        return
    
    server_internal_id = server['internal_id']
    
    try:
        url = f'https://manage.24fire.de/api/kvm/{server_internal_id}/feature'
        response = requests.get(url, headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Fire-Apikey': api_key
        })
        
        if response.status_code == 200:
            json_response = response.json()
            if json_response.get('status') == 'success':
                format_new_feature(json_response)
            else:
                print(f"{RED}Failed to fetch feature: {json_response.get('message', 'Unknown error')}{RESET}")
        else:
            print(f"{RED}Failed to fetch feature - HTTP {response.status_code}{RESET}")
            
    except requests.RequestException as e:
        print(f"{RED}Network error: {e}{RESET}")
```

### Output Formatting

Use consistent formatting for data display:

```python
def format_new_data(data):
    """Format new data with comprehensive structure."""
    if not data or 'data' not in data:
        print(f"{RED}No data available{RESET}")
        return
    
    print(f"\n{BOLD}{CYAN}=== SECTION HEADER ==={RESET}")
    print(f"{GREEN}Status: {data.get('status', 'N/A')}{RESET}")
    
    # Use consistent spacing and color coding
    for item in data.get('items', []):
        print(f"  {BLUE}Label:{RESET} {BRIGHT_WHITE}{item.get('value', 'N/A')}{RESET}")
```

## Contributing Process

### 1. Issue First

- Check existing issues before creating new ones
- For major features, create an issue to discuss the approach
- Reference issue numbers in your commits

### 2. Branch Naming

Use descriptive branch names:
- `feature/add-console-access`
- `bugfix/backup-restore-error`
- `improvement/better-error-handling`

### 3. Commit Messages

Follow conventional commit format:
```
type(scope): description

feat(backup): add backup scheduling functionality
fix(monitoring): resolve null pointer in readings display
docs(readme): update installation instructions
```

### 4. Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write clean, documented code
   - Add appropriate error handling
   - Follow existing patterns

3. **Test Thoroughly**
   - Test with different server types
   - Verify error handling
   - Check output formatting

4. **Submit Pull Request**
   - Clear title and description
   - Reference related issues
   - Include screenshots for UI changes

## Feature Requests

### Current API Endpoints

The CLI currently supports these 24fire API endpoints:

**KVM Management:**
- `/api/kvm/{id}/power` - Server control
- `/api/kvm/{id}/config` - Configuration
- `/api/kvm/{id}/backup/*` - Backup operations
- `/api/kvm/{id}/traffic/*` - Traffic monitoring
- `/api/kvm/{id}/monitoring/*` - Performance monitoring
- `/api/kvm/{id}/ddos` - DDoS protection

**Account Management:**
- `/api/account` - Account information
- `/api/account/services` - Service listing
- `/api/account/donations` - Donation management
- `/api/account/affiliate` - Affiliate program

### Potential New Features

We welcome contributions for:

- **Console Access**: VNC/SSH integration
- **File Management**: SFTP/FTP operations
- **Automated Backups**: Scheduling and rotation
- **Resource Monitoring**: Real-time stats
- **Bulk Operations**: Multi-server management
- **Configuration Templates**: Server setup automation
- **Notification System**: Status alerts
- **Web Interface**: GUI wrapper

### Implementation Guidelines

When adding new features:

1. **API Integration**
   - Use existing request patterns
   - Implement proper error handling
   - Add response validation

2. **CLI Arguments**
   - Follow existing argument patterns
   - Add help text and examples
   - Maintain backward compatibility

3. **Output Formatting**
   - Use consistent color schemes
   - Provide summary information
   - Include progress indicators for long operations

## Bug Reports

### Information to Include

- **Environment**: OS, Python version
- **Command**: Exact command that failed
- **Expected vs Actual**: What should happen vs what happened
- **API Response**: Include relevant API responses
- **Logs**: Any error messages or stack traces

### Example Bug Report

```markdown
**Environment:**
- OS: Ubuntu 22.04
- Python: 3.11.2
- CLI Version: 1.2.0

**Command:**
```bash
24fire -b restore -t myserver --backup-id 12345
```

**Expected:** Backup restoration should start
**Actual:** Error message "Backup not found"

**API Response:**
```json
{
  "status": "error",
  "message": "Invalid backup ID"
}
```
```

## API Integration

### Authentication

All API requests use the X-Fire-Apikey header:

```python
headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Fire-Apikey': api_key
}
```

### Error Handling

Always implement comprehensive error handling:

```python
try:
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        json_response = response.json()
        if json_response.get('status') == 'success':
            # Handle success
            pass
        else:
            # Handle API error
            print(f"{RED}API Error: {json_response.get('message')}{RESET}")
    else:
        # Handle HTTP error
        print(f"{RED}HTTP Error: {response.status_code}{RESET}")
        
except requests.RequestException as e:
    # Handle network error
    print(f"{RED}Network Error: {e}{RESET}")
```

### Rate Limiting

Be mindful of API rate limits:
- Add delays between bulk operations
- Implement retry logic with exponential backoff
- Cache responses when appropriate

## Testing

### Manual Testing

Test your changes with:

1. **Different Server Types**: KVM, Webspace, Domain
2. **Error Conditions**: Invalid IDs, network failures
3. **Edge Cases**: Empty responses, malformed data
4. **Multiple Platforms**: Windows, Linux, macOS

### Test Checklist

- [ ] Command line arguments work correctly
- [ ] Error messages are clear and helpful
- [ ] Output formatting is consistent
- [ ] API responses are handled properly
- [ ] Network errors are caught
- [ ] Help text is accurate

## Documentation

### Code Documentation

- Add docstrings to all functions
- Include parameter descriptions
- Document return values and exceptions
- Provide usage examples

### User Documentation

When adding features, update:
- README.md with new commands
- Help text in argument parser
- Example usage in docstrings

### API Documentation

Document any new API endpoints:
- Request format
- Response structure
- Error codes
- Rate limits

## Release Process

### Version Numbering

We use semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Checklist

- [ ] Update version in relevant files
- [ ] Update CHANGELOG.md
- [ ] Test on all supported platforms
- [ ] Update documentation
- [ ] Create release tag
- [ ] Verify automated builds

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help newcomers get started
- Focus on the technical aspects

### Communication

- Use GitHub issues for bug reports and feature requests
- Join discussions in pull requests
- Ask questions if you're unsure about anything

## Getting Help

- **Issues**: Create a GitHub issue for bugs or questions
- **Discussions**: Use GitHub Discussions for general questions
- **Documentation**: Check README.md and code comments
- **Examples**: Look at existing code patterns

## Recognition

Contributors will be:
- Listed in the project's contributors section
- Mentioned in release notes for significant contributions
- Invited to participate in project decisions

Thank you for contributing to 24fire API CLI! 🚀