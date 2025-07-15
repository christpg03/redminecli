# Redmine CLI

A powerful command-line interface for interacting with Redmine project management systems. This tool allows you to manage tasks, log time, and track work sessions directly from your terminal.

## Features

- 🔧 **Easy Configuration**: Simple setup with URL and API key
- 📋 **Task Management**: List and filter your assigned tasks
- ⏱️ **Time Tracking**: Built-in timer with automatic time logging
- 📊 **Time Entries**: View and manage your logged time entries
- 🎯 **Activity Management**: List and use available time entry activities
- 🎨 **Colored Output**: Status-based color coding for better readability

## Installation

### Prerequisites

- Python 3.8 or higher
- Access to a Redmine instance with API enabled
- Redmine API key (available in your user account settings)

### Install from Source

1. Clone the repository:
```bash
git clone https://github.com/yourusername/redminecli.git
cd redminecli
```

2. Install the package:
```bash
pip install -e .
```

### Using pip (if published to PyPI)
```bash
pip install redminecli
```

## Quick Start

### 1. Configure Your Redmine Connection

Before using any commands, you need to configure your Redmine instance:

```bash
redmine config --url https://your-redmine-instance.com --key your_api_key
```

You can also run the command without options to be prompted for the values:
```bash
redmine config
```

### 2. Verify Your Configuration

Check your current configuration:
```bash
redmine credentials
```

### 3. List Your Tasks

View all tasks assigned to you:
```bash
redmine tasks
```

Filter tasks by status:
```bash
redmine tasks --status "In Progress"
```

## Commands Reference

### Configuration Commands

#### `redmine config`
Configure your Redmine instance URL and API key.

```bash
redmine config --url https://redmine.example.com --key abc123def456
```

**Options:**
- `--url`: Your Redmine instance URL (including protocol)
- `--key`: Your Redmine API key

#### `redmine credentials`
Display current configuration settings.

```bash
redmine credentials
```

### Task Management

#### `redmine tasks`
List all tasks assigned to you.

```bash
# List all tasks
redmine tasks

# Filter by status
redmine tasks --status "New"
redmine tasks --status "In Progress"
```

**Options:**
- `--status`: Filter tasks by status name (case-insensitive)

### Time Tracking

#### `redmine start`
Start a timer for a specific issue.

```bash
redmine start --issue-id 123
```

**Features:**
- Only one timer can be active at a time
- Starting a new timer automatically stops the previous one
- Verifies that the issue exists before starting

#### `redmine timer-status`
Check the status of your current timer.

```bash
redmine timer-status
```

**Output includes:**
- Issue ID and title
- Start time
- Elapsed time

#### `redmine stop`
Stop the current timer and optionally log time to Redmine.

```bash
# Stop and be prompted to log time
redmine stop

# Stop with a comment
redmine stop --comment "Fixed the login bug"
```

**Options:**
- `--comment`, `-m`: Optional work description

**Interactive prompts:**
- Confirmation to log time to Redmine
- Activity selection
- Comment (if not provided via option)

### Time Logging

#### `redmine log`
Manually log time for a specific issue.

```bash
redmine log --issue-id 123 --hours 2.5 --activity "Development" --comment "Fixed login bug"
```

**Options:**
- `--issue-id`: Issue ID to log time for (required)
- `--hours`: Hours worked (decimal values supported, e.g., 2.5)
- `--activity`: Activity name (e.g., "Development", "Testing")
- `--comment`, `-m`: Work description (optional)

#### `redmine time-entries`
View your recent time entries.

```bash
# View recent time entries
redmine time-entries

# Filter by issue
redmine time-entries --issue-id 123

# Limit number of entries
redmine time-entries --limit 20
```

**Options:**
- `--issue-id`: Filter entries for specific issue
- `--limit`: Number of entries to display (default: 10)

#### `redmine activities`
List all available time entry activities.

```bash
redmine activities
```

## Usage Examples

### Daily Workflow Example

1. **Start your day by checking tasks:**
```bash
redmine tasks --status "In Progress"
```

2. **Start working on an issue:**
```bash
redmine start --issue-id 123
```

3. **Check your progress:**
```bash
redmine timer-status
```

4. **Stop and log your work:**
```bash
redmine stop --comment "Implemented user authentication"
```

5. **Review your logged time:**
```bash
redmine time-entries --limit 5
```

### Multiple Work Sessions

```bash
# Work on issue 123 for 2 hours
redmine start --issue-id 123
# ... work for 2 hours ...
redmine stop --comment "Initial implementation"

# Switch to issue 124 for 1 hour
redmine start --issue-id 124
# ... work for 1 hour ...
redmine stop --comment "Code review and testing"

# Check total time logged today
redmine time-entries --limit 10
```

### Manual Time Logging

If you forgot to use the timer:

```bash
redmine log --issue-id 123 --hours 3.5 --activity "Development" --comment "Refactored authentication module"
```

## Configuration

### Configuration File Location

The configuration is stored in a local file in your user directory. The exact location depends on your operating system:

- **Linux/macOS**: `~/.config/redminecli/config.json`
- **Windows**: `%APPDATA%\redminecli\config.json`

### API Key Setup

To get your Redmine API key:

1. Log into your Redmine instance
2. Go to "My account" (usually in the top-right menu)
3. Click on the "API access key" section
4. Click "Show" to reveal your API key
5. Copy the key for use with `redmine config`

## Error Handling

The CLI provides helpful error messages for common issues:

- **Authentication errors**: Invalid API key or insufficient permissions
- **Network errors**: Connection issues with Redmine instance
- **Resource errors**: Invalid issue IDs or missing resources
- **Configuration errors**: Missing or invalid configuration

## Development

### Setting up Development Environment

1. Clone the repository:
```bash
git clone https://github.com/yourusername/redminecli.git
cd redminecli
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
isort .
flake8
```

### Type Checking

```bash
mypy cli/
```

## Dependencies

- **click**: Command-line interface framework
- **python-redmine**: Redmine API client library
- **requests**: HTTP library for API communication

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/yourusername/redminecli/issues) page
2. Create a new issue with detailed information about your problem
3. Include your Redmine version and CLI version in bug reports

## Changelog

### v0.1.0 (Initial Release)
- Basic Redmine integration
- Task listing and filtering
- Time tracking with timer functionality
- Time entry logging and viewing
- Activity management
- Configuration management
- Colored output for better readability