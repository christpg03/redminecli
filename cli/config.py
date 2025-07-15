"""Configuration management for Redmine CLI.

This module provides functions to load and save Redmine configuration
including URL and API key settings.
"""

import os
import json
from typing import TypedDict

CONFIG_DIR = os.path.expanduser("~/.redminecli")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
TIMER_FILE = os.path.join(CONFIG_DIR, "timer.json")


class RedmineConfig(TypedDict):
    """A TypedDict for Redmine configuration."""

    url: str
    key: str


def load_config() -> RedmineConfig:
    """Load the Redmine configuration from a JSON file."""
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(
            f"Configuration file not found: {CONFIG_FILE}. "
            "Use 'redminecli config' to set up your configuration."
        )
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: RedmineConfig) -> None:
    """Save the Redmine configuration to a JSON file."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
