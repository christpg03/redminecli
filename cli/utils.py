import json
import os
from typing import TypedDict, Optional

from redminelib import Redmine

from cli.config import TIMER_FILE


class TimerConfig(TypedDict):
    """A TypedDict for timer configuration."""

    issue_id: int
    start_time: str


def get_status_color(status_name: str) -> str:
    """
    Determine the color for a task status.

    Args:
        status_name (str): The name of the status

    Returns:
        str: The color name for click.style()
    """
    status_lower = status_name.lower()

    # TO DO states (blue)
    if any(
        keyword in status_lower
        for keyword in ["new", "to do", "todo", "open", "assigned"]
    ):
        return "blue"

    # IN PROGRESS states (magenta/purple)
    elif any(
        keyword in status_lower
        for keyword in ["in progress", "progress", "working", "active"]
    ):
        return "magenta"

    # DONE states (green)
    elif any(
        keyword in status_lower
        for keyword in ["done", "closed", "resolved", "completed", "finished"]
    ):
        return "green"

    # Default color for unknown states
    else:
        return "white"


def get_activity_id_by_name(redmine: Redmine, activity_name: str) -> int:
    """
    Get activity ID by activity name.

    Args:
        redmine: Redmine instance
        activity_name: Name of the activity (case-insensitive)

    Returns:
        int: Activity ID

    Raises:
        ValueError: If activity name is not found
    """
    try:
        # Get all available activities
        activities = redmine.enumeration.filter(resource="time_entry_activities")

        # Search for activity by name (case-insensitive)
        activity_name_lower = activity_name.lower()
        for activity in activities:
            if activity.name.lower() == activity_name_lower:
                return activity.id

        # If not found, raise an error with available activities
        available_activities = [activity.name for activity in activities]
        raise ValueError(
            f"Activity '{activity_name}' not found. "
            f"Available activities: "
            f"{', '.join(available_activities)}"
        )
    except Exception as e:
        raise ValueError(f"Error fetching activities: {str(e)}") from e


def load_timer() -> Optional[TimerConfig]:
    """
    Load timer configuration from file.

    Returns:
        Optional[TimerConfig]: Timer configuration if exists, None otherwise
    """
    if not os.path.exists(TIMER_FILE):
        return None

    try:
        with open(TIMER_FILE, "r", encoding="utf-8") as f:
            timer_data = json.load(f)
            return TimerConfig(
                issue_id=timer_data["issue_id"], start_time=timer_data["start_time"]
            )
    except (json.JSONDecodeError, KeyError, FileNotFoundError):
        return None


def save_timer(timer_config: TimerConfig) -> None:
    """
    Save timer configuration to file.

    Args:
        timer_config (TimerConfig): Timer configuration to save
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(TIMER_FILE), exist_ok=True)

    with open(TIMER_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "issue_id": timer_config["issue_id"],
                "start_time": timer_config["start_time"],
            },
            f,
            indent=4,
        )


def clear_timer() -> bool:
    """
    Clear (delete) the timer file.

    Returns:
        bool: True if timer was cleared, False if no timer existed
    """
    if os.path.exists(TIMER_FILE):
        try:
            os.remove(TIMER_FILE)
            return True
        except OSError:
            return False
    return False
