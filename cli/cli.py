import click
from datetime import datetime, timedelta
from redminelib import Redmine
from redminelib.exceptions import ResourceNotFoundError, AuthError

from cli.config import RedmineConfig, save_config, load_config
from cli.redmine_instance import RedmineInstance
from cli.utils import (
    get_status_color,
    get_activity_id_by_name,
    save_timer,
    load_timer,
    clear_timer,
    TimerConfig,
)


@click.group()
def cli():
    """
    Redmine CLI - A command line interface for Redmine.

    This is the main entry point for the Redmine CLI application. It provides
    a command-line interface to interact with Redmine instances, allowing users
    to configure connections, view credentials, and manage tasks.

    The CLI supports multiple subcommands:
    - config: Configure the Redmine instance URL and API key
    - credentials: Display current configuration
    - tasks: List assigned tasks from Redmine
    - start: Start a timer for working on a specific issue
    - stop: Stop the current timer with option to log time to Redmine
    - timer-status: Show current timer status and elapsed time
    - log: Log time worked on a specific issue
    - time-entries: View logged time entries
    - activities: List available activities for time logging
    - projects: List available projects with their IDs
    - daily: Create daily tasks for a specific team

    Example:
        $ redminecli config --url https://redmine.example.com --key your_api_key
        $ redminecli tasks
        $ redminecli start --issue-id 123
        $ redminecli timer-status
        $ redminecli stop
        $ redminecli log --issue-id 123 --hours 2.5 --activity "Development"
    """


@cli.command()
@click.option("--url", prompt="Redmine URL", help="The URL of your Redmine instance.")
@click.option("--key", prompt="API Key", help="Your Redmine API key.")
def config(url: str, key: str):
    """
    Configure Redmine CLI with URL and API key.

    This command sets up the connection parameters for your Redmine instance.
    The configuration is saved locally and will be used for all subsequent
    CLI operations that require Redmine access.

    Args:
        url (str): The full URL of your Redmine instance (e.g., https://redmine.example.com)
        key (str): Your Redmine API key for authentication

    Example:
        $ redminecli config --url https://redmine.example.com --key abc123def456

    Note:
        - The URL should include the protocol (http:// or https://)
        - API keys can be found in your Redmine user account settings
        - Configuration is stored locally and will persist between sessions
    """
    config_data: RedmineConfig = {"url": url, "key": key}
    save_config(config_data)
    click.echo("Configuration saved successfully.")


@cli.command()
def credentials():
    """
    Display the current Redmine CLI configuration.

    This command shows the currently configured Redmine instance URL and API key.
    It's useful for verifying your current configuration without having to
    reconfigure the CLI.

    Returns:
        None: Outputs configuration information to stdout

    Raises:
        FileNotFoundError: If no configuration file exists (user hasn't run config yet)

    Example:
        $ redminecli credentials
        Redmine URL: https://redmine.example.com
        API Key: abc123def456

    Note:
        - If no configuration exists, you'll need to run 'redminecli config' first
        - The API key is displayed in full for verification purposes
    """
    try:
        current_config: RedmineConfig = load_config()
        click.echo(f"Redmine URL: {current_config['url']}")
        click.echo(f"API Key: {current_config['key']}")
    except FileNotFoundError as e:
        click.echo(str(e))


@cli.command()
@click.option("--status", default=None, help="Filter tasks by status (optional).")
def tasks(status: str):
    """
    List all tasks assigned to the current user from Redmine.

    This command retrieves and displays all issues/tasks that are assigned to
    the authenticated user. Each task is shown with its ID, subject, and current
    status for quick overview.

    Args:
        status (str): Optional status filter to show only tasks with specific status

    Returns:
        None: Outputs task information to stdout

    Raises:
        ResourceNotFoundError: If the Redmine resource cannot be found
        AuthError: If authentication fails (invalid API key or permissions)

    Example:
        $ redminecli tasks
        123: Fix login bug (Status: In Progress)
        124: Update documentation (Status: New)
        125: Code review (Status: Assigned)

        $ redminecli tasks --status "In Progress"
        123: Fix login bug (Status: In Progress)

    Note:
        - Only shows tasks assigned to "me" (the authenticated user)
        - Requires valid configuration (run 'redminecli config' first)
        - If no tasks are found, displays "No tasks found."
        - Task IDs can be used to reference specific issues in Redmine
        - Use --status to filter by specific status name
    """
    redmine: Redmine = RedmineInstance.get_instance()

    try:
        issues = redmine.issue.filter(assigned_to_id="me")

        # Filter by status if specified
        if status:
            issues = [
                issue for issue in issues if issue.status.name.lower() == status.lower()
            ]

        if not issues:
            if status:
                click.echo(f"No tasks found with status '{status}'.")
            else:
                click.echo("No tasks found.")
        else:
            for issue in issues:
                status_color = get_status_color(issue.status.name)
                colored_status = click.style(
                    issue.status.name, fg=status_color, bold=True
                )
                click.echo(f"{issue.id}: {issue.subject} (Status: {colored_status})")
    except (ResourceNotFoundError, AuthError) as e:
        click.echo(f"Error fetching tasks: {str(e)}")


@cli.command("log")
@click.option(
    "--issue-id",
    prompt="Issue ID",
    type=int,
    help="The ID of the issue to log time for.",
)
@click.option(
    "--hours",
    prompt="Hours worked",
    type=float,
    help="Number of hours worked (e.g., 2.5 for 2.5 hours).",
)
@click.option(
    "--comment", "-m", default="", help="Optional comment describing the work done."
)
@click.option(
    "--activity",
    prompt="Activity name",
    type=str,
    help="Activity name (e.g., 'Development', 'Testing', 'Documentation').",
)
def log_time(issue_id: int, hours: float, comment: str, activity: str):
    """
    Log time worked on a specific Redmine issue.

    This command allows you to register time spent working on a particular issue.
    The time entry will be associated with your user account and the specified issue.

    Args:
        issue_id (int): The ID of the issue to log time for
        hours (float): Number of hours worked (can be decimal, e.g., 2.5)
        comment (str): Optional description of the work performed
        activity (str): Activity name (e.g., 'Development', 'Testing', 'Documentation')

    Returns:
        None: Outputs confirmation message to stdout

    Raises:
        ResourceNotFoundError: If the issue ID doesn't exist
        AuthError: If authentication fails or insufficient permissions
        ValueError: If the activity name is not found

    Example:
        $ redminecli log --issue-id 123 \\
            --hours 2.5 \\
            --activity "Development" \\
            --comment "Fixed login bug"
        Time logged successfully: 2.5 hours on issue #123

        $ redminecli log --issue-id 124 --hours 1.0 --activity "Testing"
        Time logged successfully: 1.0 hours on issue #124

    Note:
        - Hours can be decimal values (e.g., 0.5 for 30 minutes, 2.25 for 2 hours 15 minutes)
        - Comments are optional but recommended for tracking work details
        - Activity names are case-insensitive (e.g., 'development', 'Development', 'DEVELOPMENT')
        - If you enter an invalid activity name, the command will show available activities
        - Requires valid configuration and permissions to log time in Redmine
        - The time entry will be associated with today's date
    """
    redmine: Redmine = RedmineInstance.get_instance()

    try:
        # Verify the issue exists and get its details
        redmine.issue.get(issue_id)

        # Get activity ID from activity name
        activity_id = get_activity_id_by_name(redmine, activity)

        # Prepare time entry data
        time_entry_data = {
            "issue_id": issue_id,
            "hours": hours,
            "comments": comment,
            "activity_id": activity_id,
        }

        # Create the time entry
        time_entry = redmine.time_entry.create(**time_entry_data)

        # Success message
        click.echo(f"Time logged successfully: {hours:.2f} hours on issue #{issue_id}")
        click.echo(f"Activity: {activity}")
        if comment:
            click.echo(f"Comment: {comment}")
        click.echo(f"Time entry ID: {time_entry.id}")

    except ResourceNotFoundError:
        click.echo(f"Error: Issue #{issue_id} not found. Please check the issue ID.")
    except AuthError as e:
        click.echo(
            f"Error: Authentication failed or insufficient permissions - {str(e)}"
        )
    except ValueError as e:
        click.echo(f"Error: {str(e)}")
    except TypeError as e:
        click.echo(f"Error logging time: Invalid input - {str(e)}")
    except ConnectionError as e:
        click.echo(f"Error logging time: Connection failed - {str(e)}")


@cli.command("time-entries")
@click.option(
    "--issue-id",
    default=None,
    type=int,
    help="Filter time entries by issue ID (optional).",
)
@click.option(
    "--limit",
    default=10,
    type=int,
    help="Number of time entries to show (default: 10).",
)
def time_entries(issue_id: int, limit: int):
    """
    List recent time entries for the current user.

    This command displays recent time entries logged by the authenticated user.
    You can filter by a specific issue or view all recent entries.

    Args:
        issue_id (int): Optional issue ID to filter time entries
        limit (int): Maximum number of entries to display (default: 10)

    Returns:
        None: Outputs time entries information to stdout

    Raises:
        ResourceNotFoundError: If the specified issue doesn't exist
        AuthError: If authentication fails

    Example:
        $ redminecli time-entries
        Time Entry #456: 2.5 hours on Issue #123 [Development] - "Fixed login bug" (2025-06-26)
        Time Entry #457: 1.0 hours on Issue #124 [Testing] - "Code review" (2025-06-26)

        $ redminecli time-entries --issue-id 123
        Time Entry #456: 2.5 hours on Issue #123 [Development] - "Fixed login bug" (2025-06-26)
        Time Entry #458: 3.0 hours on Issue #123 [Testing] - "Testing fixes" (2025-06-25)

    Note:
        - Shows only time entries logged by the current user
        - Entries are ordered by most recent first
        - Use --issue-id to see time entries for a specific issue
        - Use --limit to control how many entries are displayed
    """
    redmine: Redmine = RedmineInstance.get_instance()

    try:
        # Get current user to filter time entries
        current_user = redmine.user.get("current")

        # Build filter parameters
        filter_params = {"user_id": current_user.id, "limit": limit}

        # Add issue filter if specified
        if issue_id:
            filter_params["issue_id"] = issue_id

        # Get time entries
        entries_resource = redmine.time_entry.filter(**filter_params)
        entries = list(entries_resource)

        if not entries:
            if issue_id:
                click.echo(f"No time entries found for issue #{issue_id}.")
            else:
                click.echo("No time entries found.")
        else:
            total_hours = 0
            for entry in entries:
                # Format the date
                spent_on = (
                    entry.spent_on.strftime("%Y-%m-%d")
                    if hasattr(entry, "spent_on")
                    else "Unknown date"
                )

                # Build display string
                comment_text = (
                    f' - "{entry.comments}"'
                    if hasattr(entry, "comments") and entry.comments
                    else ""
                )
                issue_text = (
                    f"Issue #{entry.issue.id}"
                    if hasattr(entry, "issue")
                    else "Unknown issue"
                )
                activity_text = (
                    f" [{entry.activity.name}]"
                    if hasattr(entry, "activity") and hasattr(entry.activity, "name")
                    else " [Unknown activity]"
                )

                click.echo(
                    (
                        f"Time Entry #{entry.id}: "
                        f"{entry.hours} hours on "
                        f"{issue_text}"
                        f"{activity_text}"
                        f"{comment_text} "
                        f"({spent_on})"
                    )
                )
                total_hours += entry.hours

            click.echo(f"\nTotal hours shown: {total_hours}")

    except ResourceNotFoundError as e:
        click.echo(f"Error: {str(e)}")
    except AuthError as e:
        click.echo(f"Error: Authentication failed - {str(e)}")
    except (ValueError, TypeError) as e:
        click.echo(f"Error fetching time entries: {str(e)}")
    except ConnectionError as e:
        click.echo(f"Error fetching time entries: {str(e)}")


@cli.command("activities")
def list_activities():
    """
    List all available time entry activities.

    This command displays all available activities that can be used when logging time.
    This is useful to see what activity names are available for use with the 'log' command.

    Returns:
        None: Outputs available activities to stdout

    Raises:
        AuthError: If authentication fails
        ConnectionError: If connection to Redmine fails

    Example:
        $ redminecli activities
        Available activities:
        - Development
        - Testing
        - Documentation
        - Design
        - Support

    Note:
        - Activity names are case-insensitive when used with the 'log' command
        - This list comes from your Redmine instance configuration
        - Only shows activities that are available for time entry logging
    """
    redmine: Redmine = RedmineInstance.get_instance()

    try:
        # Get all available activities
        activities = redmine.enumeration.filter(resource="time_entry_activities")

        if not activities:
            click.echo("No activities found.")
        else:
            click.echo("Available activities:")
            for activity in activities:
                click.echo(f"- {activity.name}")

    except AuthError as e:
        click.echo(f"Error: Authentication failed - {str(e)}")
    except ConnectionError as e:
        click.echo(f"Error: Connection failed - {str(e)}")
    except ResourceNotFoundError as e:
        click.echo(f"Error fetching activities: {str(e)}")
    except TypeError as e:
        click.echo(f"Error fetching activities: {str(e)}")
    except ValueError as e:
        click.echo(f"Error fetching activities: {str(e)}")


@cli.command("projects")
def list_projects():
    """
    List all available projects.

    This command displays all projects available in the Redmine instance
    with their ID and name. This is useful to see what project IDs are
    available for use with other commands like 'daily'.

    Returns:
        None: Outputs available projects to stdout

    Raises:
        AuthError: If authentication fails
        ConnectionError: If connection to Redmine fails

    Example:
        $ redminecli projects
        Available projects:
        1: Project Alpha
        2: Project Beta
        3: Internal Tools
        4: Documentation

    Note:
        - Shows all projects visible to the current user
        - Project IDs can be used with other commands that require project-id parameter
        - Only shows projects where the user has at least view permissions
    """
    redmine: Redmine = RedmineInstance.get_instance()

    try:
        # Get all available projects
        projects = redmine.project.all()

        if not projects:
            click.echo("No projects found.")
        else:
            click.echo("Available projects:")
            for project in projects:
                click.echo(f"{project.id}: {project.name}")

    except AuthError as e:
        click.echo(f"Error: Authentication failed - {str(e)}")
    except ConnectionError as e:
        click.echo(f"Error: Connection failed - {str(e)}")
    except ResourceNotFoundError as e:
        click.echo(f"Error fetching projects: {str(e)}")
    except TypeError as e:
        click.echo(f"Error fetching projects: {str(e)}")
    except ValueError as e:
        click.echo(f"Error fetching projects: {str(e)}")


@cli.command("start")
@click.option(
    "--issue-id",
    prompt="Issue ID",
    type=int,
    help="The ID of the issue to start timing for.",
)
def start_timer(issue_id: int):
    """
    Start a timer for working on a specific Redmine issue.

    This command starts a timer to track time spent working on a particular issue.
    The timer will continue running until you stop it or start a new timer for
    a different issue.

    Args:
        issue_id (int): The ID of the issue to start timing for

    Returns:
        None: Outputs confirmation message to stdout

    Raises:
        ResourceNotFoundError: If the issue ID doesn't exist
        AuthError: If authentication fails or insufficient permissions

    Example:
        $ redminecli start --issue-id 123
        Timer started for issue #123: Fix login bug
        Started at: 2025-07-14 10:30:00

        $ redminecli start --issue-id 124
        Previous timer for issue #123 stopped.
        Timer started for issue #124: Update documentation
        Started at: 2025-07-14 11:15:00

    Note:
        - Only one timer can be active at a time
        - Starting a new timer will automatically stop any existing timer
        - Use 'redminecli stop' or 'redminecli log' to stop the timer and log time
        - Requires valid configuration and permissions to access Redmine issues
    """
    redmine: Redmine = RedmineInstance.get_instance()

    try:
        # Verify the issue exists and get its details
        issue = redmine.issue.get(issue_id)

        # Check if there's already a timer running
        existing_timer = load_timer()
        if existing_timer:
            click.echo(
                f"Previous timer for issue #{existing_timer['issue_id']} stopped."
            )

        # Create new timer configuration
        start_time = datetime.now().isoformat()
        timer_config: TimerConfig = {
            "issue_id": issue_id,
            "start_time": start_time,
        }

        # Save the timer
        save_timer(timer_config)

        # Format start time for display
        start_datetime = datetime.fromisoformat(start_time)
        formatted_time = start_datetime.strftime("%Y-%m-%d %H:%M:%S")

        # Success message
        click.echo(f"Timer started for issue #{issue_id}: {issue.subject}")
        click.echo(f"Started at: {formatted_time}")

    except ResourceNotFoundError:
        click.echo(f"Error: Issue #{issue_id} not found. Please check the issue ID.")
    except AuthError as e:
        click.echo(
            f"Error: Authentication failed or insufficient permissions - {str(e)}"
        )
    except (TypeError, ValueError) as e:
        click.echo(f"Error starting timer: Invalid input - {str(e)}")
    except ConnectionError as e:
        click.echo(f"Error starting timer: Connection failed - {str(e)}")


@cli.command("stop")
@click.option(
    "--comment", "-m", default="", help="Optional comment describing the work done."
)
def stop_timer(comment: str):
    """
    Stop the current timer and optionally log time to Redmine.

    This command stops any currently running timer and offers to create a time entry
    in Redmine with the elapsed time. You'll be prompted to confirm if you want to
    log the time and select an activity.

    Args:
        comment (str): Optional description of the work performed

    Returns:
        None: Outputs confirmation message to stdout

    Example:
        $ redminecli stop
        Timer for issue #123 stopped. Time elapsed: 2.5 hours
        Do you want to log this time to Redmine? [Y/n]: Y
        Activity name: Development
        Time logged successfully: 2.5 hours on issue #123

        $ redminecli stop --comment "Fixed login bug"
        Timer for issue #123 stopped. Time elapsed: 1.5 hours
        Do you want to log this time to Redmine? [Y/n]: n
        Timer stopped without logging time.

    Note:
        - Prompts to log time with "Y" as default
        - If you choose to log time, you'll be asked for the activity
        - Comments can be provided via --comment or will be prompted if logging
        - If no timer is running, displays an appropriate message
    """
    timer = load_timer()

    if not timer:
        click.echo("No timer is currently running.")
        return

    # Calculate elapsed time
    start_time = datetime.fromisoformat(timer["start_time"])
    end_time = datetime.now()
    elapsed = end_time - start_time
    elapsed_hours = elapsed.total_seconds() / 3600

    click.echo(f"Timer for issue #{timer['issue_id']} stopped.")
    click.echo(f"Time elapsed: {elapsed_hours:.2f} hours")

    # Ask if user wants to log the time
    log_time_choice = click.confirm(
        "Do you want to log this time to Redmine?", default=True
    )

    if not log_time_choice:
        # Clear the timer and exit
        clear_timer()
        click.echo("Timer stopped without logging time.")
        return

    # User wants to log time, get activity
    activity = click.prompt("Activity name", type=str)

    # If no comment was provided via option, ask for one
    if not comment:
        comment = click.prompt("Comment (optional)", default="", show_default=False)

    # Now log the time
    redmine: Redmine = RedmineInstance.get_instance()

    try:
        # Verify the issue exists
        issue = redmine.issue.get(timer["issue_id"])

        # Get activity ID from activity name
        activity_id = get_activity_id_by_name(redmine, activity)

        # Prepare time entry data
        time_entry_data = {
            "issue_id": timer["issue_id"],
            "hours": elapsed_hours,
            "comments": comment,
            "activity_id": activity_id,
        }

        # Create the time entry
        time_entry = redmine.time_entry.create(**time_entry_data)

        # Clear the timer
        clear_timer()

        # Success message
        click.echo(
            f"Time logged successfully: {elapsed_hours:.2f} hours on issue #{timer['issue_id']}"
        )
        click.echo(f"Activity: {activity}")
        if comment:
            click.echo(f"Comment: {comment}")
        click.echo(f"Time entry ID: {time_entry.id}")

    except ResourceNotFoundError:
        clear_timer()
        click.echo(f"Error: Issue #{timer['issue_id']} not found. Timer cleared.")
    except AuthError as e:
        clear_timer()
        click.echo(f"Error: Authentication failed - {str(e)}. Timer cleared.")
    except ValueError as e:
        clear_timer()
        click.echo(f"Error: {str(e)}. Timer cleared.")
    except (TypeError, ConnectionError) as e:
        clear_timer()
        click.echo(f"Error logging time: {str(e)}. Timer cleared.")


@cli.command("timer-status")
def timer_status():
    """
    Show the current timer status.

    This command displays information about any currently running timer,
    including the issue being worked on and elapsed time.

    Returns:
        None: Outputs timer status to stdout

    Example:
        $ redminecli timer-status
        Timer is running for issue #123: Fix login bug
        Started at: 2025-07-14 10:30:00
        Elapsed time: 1.5 hours

        $ redminecli timer-status
        No timer is currently running.

    Note:
        - Shows real-time elapsed time
        - Displays issue title if available
        - Use this to check your current work session
    """
    timer = load_timer()

    if not timer:
        click.echo("No timer is currently running.")
        return

    try:
        # Get issue details
        redmine: Redmine = RedmineInstance.get_instance()
        issue = redmine.issue.get(timer["issue_id"])

        # Calculate elapsed time
        start_time = datetime.fromisoformat(timer["start_time"])
        current_time = datetime.now()
        elapsed = current_time - start_time
        elapsed_hours = elapsed.total_seconds() / 3600

        # Format start time for display
        formatted_start = start_time.strftime("%Y-%m-%d %H:%M:%S")

        # Display timer status
        click.echo(f"Timer is running for issue #{timer['issue_id']}: {issue.subject}")
        click.echo(f"Started at: {formatted_start}")
        click.echo(f"Elapsed time: {elapsed_hours:.2f} hours")

    except (ResourceNotFoundError, AuthError) as e:
        # Still show timer info even if we can't get issue details
        start_time = datetime.fromisoformat(timer["start_time"])
        current_time = datetime.now()
        elapsed = current_time - start_time
        elapsed_hours = elapsed.total_seconds() / 3600
        formatted_start = start_time.strftime("%Y-%m-%d %H:%M:%S")

        click.echo(f"Timer is running for issue #{timer['issue_id']}")
        click.echo(f"Started at: {formatted_start}")
        click.echo(f"Elapsed time: {elapsed_hours:.2f} hours")
        click.echo(f"(Could not fetch issue details: {str(e)})")


@cli.command("daily")
@click.option(
    "--project-id",
    prompt="Project ID",
    type=int,
    help="ID of the project where daily tasks will be created.",
)
@click.option(
    "--team",
    prompt="Team name",
    type=str,
    help="Team name for creating daily tasks.",
)
@click.option(
    "--start-date",
    type=click.DateTime(formats=["%d-%m-%Y"]),
    help="Start date (DD-MM-YYYY format). If not specified, uses current date.",
)
@click.option(
    "--end-date",
    type=click.DateTime(formats=["%d-%m-%Y"]),
    help="End date (DD-MM-YYYY format). If specified, creates tasks for the date range.",
)
def daily(
    team: str, start_date: datetime | None, end_date: datetime | None, project_id: int
):
    """
    Create daily tasks for a specific team.

    This command creates daily tasks with the format [Daily][Team] DD-MM-YYYY.
    It can create a single task for a specific date or multiple tasks
    for a date range.

    Args:
        team (str): Team name for creating the tasks
        start_date (datetime): Start date for creating tasks (optional)
        end_date (datetime): End date for creating a range of tasks (optional)
        project_id (int): ID of the project where tasks will be created

    Returns:
        None: Outputs confirmation messages to stdout

    Raises:
        ResourceNotFoundError: If the project doesn't exist
        AuthError: If authentication fails
        ValueError: If there's an error with date parameters

    Example:
        # Create task for today
        $ redminecli daily --team "Backend" --project-id 1

        # Create task for specific date
        $ redminecli daily --team "Frontend" --start-date 15-07-2025 --project-id 1

        # Create tasks for date range
        $ redminecli daily --team "QA" --start-date 15-07-2025 --end-date 19-07-2025 --project-id 1

    Note:
        - If start-date is not specified, uses current date
        - If end-date is specified, start-date must also be specified
        - Dates must be in DD-MM-YYYY format
        - One task is created for each day in the specified range
        - Tasks are created with start and due dates corresponding to their day
    """
    redmine: Redmine = RedmineInstance.get_instance()

    try:
        # Verify the project exists
        project = redmine.project.get(project_id)

        # Ask for dates if not provided
        if start_date is None:
            start_date_input = click.prompt(
                "Start date (DD-MM-YYYY) or press Enter for today",
                default="",
                show_default=False,
            )
            if start_date_input == "":
                start_date = datetime.now()
            else:
                try:
                    start_date = datetime.strptime(start_date_input, "%d-%m-%Y")
                except ValueError:
                    click.echo("Invalid date format. Please use DD-MM-YYYY format.")
                    return

        if end_date is None:
            end_date_input = click.prompt(
                "End date (DD-MM-YYYY) or press Enter for single day",
                default="",
                show_default=False,
            )
            if end_date_input != "":
                try:
                    end_date = datetime.strptime(end_date_input, "%d-%m-%Y")
                except ValueError:
                    click.echo("Invalid date format. Please use DD-MM-YYYY format.")
                    return

        # Determine dates to process
        if end_date is not None and end_date < start_date:
            click.echo("Error: End date cannot be earlier than start date.")
            return

        # Create list of dates to process
        dates_to_process = []

        if end_date is None:
            # Only one date
            dates_to_process.append(start_date)
        else:
            # Date range
            current_date = start_date
            while current_date <= end_date:
                dates_to_process.append(current_date)
                current_date += timedelta(days=1)

        # Create tasks for each date
        created_tasks = []

        for date in dates_to_process:
            # Format date for title
            formatted_date = date.strftime("%d-%m-%Y")

            # Create task title
            task_title = f"[Daily][{team}] {formatted_date}"

            # Format date for Redmine (YYYY-MM-DD)
            redmine_date = date.strftime("%Y-%m-%d")

            # Prepare task data
            issue_data = {
                "project_id": project_id,
                "subject": task_title,
                "start_date": redmine_date,
                "due_date": redmine_date,
                "description": f"Daily task for team {team} on {formatted_date}",
            }

            try:
                # Create the task
                issue = redmine.issue.create(**issue_data)
                created_tasks.append(
                    {"id": issue.id, "title": task_title, "date": formatted_date}
                )

            except Exception as e:
                click.echo(f"Error creating task for {formatted_date}: {str(e)}")
                continue

        # Show results
        if created_tasks:
            click.echo(f"\n{len(created_tasks)} task(s) created successfully:")
            for task in created_tasks:
                click.echo(f"- Task #{task['id']}: {task['title']}")

            click.echo(f"\nProject: {project.name}")
            click.echo(f"Team: {team}")

            if len(dates_to_process) == 1:
                click.echo(f"Date: {dates_to_process[0].strftime('%d-%m-%Y')}")
            elif end_date is not None:
                click.echo(
                    f"Range: {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}"
                )
        else:
            click.echo("No tasks could be created.")

    except ResourceNotFoundError:
        click.echo(f"Error: Project #{project_id} not found.")
    except AuthError as e:
        click.echo(f"Error: Authentication failed - {str(e)}")
    except ValueError as e:
        click.echo(f"Error: Invalid parameters - {str(e)}")
    except ConnectionError as e:
        click.echo(f"Error: Connection failed - {str(e)}")
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}")
