"""
UCKN Database Migrations Layer
Manages schema evolution for the PostgreSQL database using Alembic.
"""
import logging
import os

from alembic import command
from alembic.config import Config

_logger = logging.getLogger(__name__)

def run_migrations(connection_string: str, script_location: str, revision: str = "head") -> bool:
    """
    Runs Alembic migrations programmatically.

    Args:
        connection_string: The database connection URL.
        script_location: Path to the Alembic versions directory (e.g., 'src/uckn/storage/migrations').
        revision: The target revision to migrate to (e.g., 'head' for latest).

    Returns:
        True if migrations ran successfully, False otherwise.
    """
    try:
        # Create a dummy alembic.ini in a temporary location or configure programmatically
        # For simplicity, we assume alembic.ini is correctly placed and configured
        # relative to the script_location or in the project root.
        # A more robust solution would generate alembic.ini or pass config directly.

        # For this example, we'll assume alembic.ini is in the script_location
        alembic_cfg_path = os.path.join(script_location, "alembic.ini")
        if not os.path.exists(alembic_cfg_path):
            _logger.error(f"Alembic config file not found at {alembic_cfg_path}. Please run 'alembic init' first.")
            return False

        alembic_cfg = Config(alembic_cfg_path)
        alembic_cfg.set_main_option("script_location", script_location)
        alembic_cfg.set_main_option("sqlalchemy.url", connection_string)

        _logger.info(f"Running Alembic migrations to revision: {revision}")
        command.upgrade(alembic_cfg, revision)
        _logger.info("Alembic migrations completed successfully.")
        return True
    except Exception as e:
        _logger.error(f"Alembic migration failed: {e}")
        return False

# This file primarily serves as a marker for the migrations package.
# The actual migration scripts will be in src/uckn/storage/migrations/versions/
# and managed by Alembic CLI.
