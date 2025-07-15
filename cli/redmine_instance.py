"""Redmine instance management module.

This module provides a singleton class to manage Redmine API connections,
ensuring only one instance is created and reused throughout the application.
"""

from redminelib import Redmine
from cli.config import RedmineConfig, load_config


class RedmineInstance:
    """Singleton class for managing Redmine API connections.

    This class ensures that only one Redmine instance is created and reused
    throughout the application lifecycle.
    """

    _instance = None

    @staticmethod
    def get_instance() -> Redmine:
        """Get the singleton instance of Redmine."""
        if RedmineInstance._instance is None:
            config: RedmineConfig = load_config()
            RedmineInstance._instance = Redmine(
                config["url"],
                key=config["key"],
            )
        return RedmineInstance._instance
