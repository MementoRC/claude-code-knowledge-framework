#!/usr/bin/env python3
"""
UCKN Database Manager Atom

Automatically manages PostgreSQL database availability for UCKN.
Ensures database is running via Docker if needed.
"""

import logging
import os
import socket
import subprocess
import time
from typing import Any


class DatabaseManager:
    """
    Atomic component for managing UCKN database availability.

    Responsibilities:
    - Check if PostgreSQL is accessible
    - Auto-start Docker container if needed
    - Initialize database schema
    - Provide database connection status
    """

    def __init__(self, auto_start: bool = True, container_name: str = "uckn-postgres"):
        self.auto_start = auto_start
        self.container_name = container_name
        self._logger = logging.getLogger(__name__)

        # Database configuration from environment
        self.database_url = os.environ.get("UCKN_DATABASE_URL")
        self.default_db_config = {
            "user": os.environ.get("UCKN_DB_USER", "uckn"),
            "password": os.environ.get("UCKN_DB_PASSWORD", "uckn_secure_password"),
            "host": os.environ.get("UCKN_DB_HOST", "localhost"),
            "port": int(os.environ.get("UCKN_DB_PORT", "5432")),
            "database": os.environ.get("UCKN_DB_NAME", "shared_uckn"),
        }

        # Auto-start can be disabled via environment variable
        if os.environ.get("UCKN_AUTO_START_DB", "true").lower() == "false":
            self.auto_start = False

    def is_database_accessible(self, host: str = "localhost", port: int = 5432) -> bool:
        """Check if PostgreSQL is accessible on the given host and port."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception as e:
            self._logger.debug(f"Database accessibility check failed: {e}")
            return False

    def is_docker_available(self) -> bool:
        """Check if Docker is available and running."""
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            self._logger.debug(f"Docker availability check failed: {e}")
            return False

    def is_container_running(self, container_name: str) -> bool:
        """Check if a Docker container is currently running."""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    f"name={container_name}",
                    "--format",
                    "{{.Names}}",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return container_name in result.stdout
        except Exception as e:
            self._logger.debug(f"Container status check failed: {e}")
            return False

    def start_database_container(self) -> bool:
        """Start the UCKN PostgreSQL Docker container."""
        if not self.is_docker_available():
            self._logger.error("Docker is not available. Cannot auto-start database.")
            return False

        config = self.default_db_config

        try:
            # Stop and remove existing container if it exists
            self._logger.info(f"Cleaning up existing container: {self.container_name}")
            subprocess.run(
                ["docker", "stop", self.container_name], capture_output=True, timeout=10
            )
            subprocess.run(
                ["docker", "rm", self.container_name], capture_output=True, timeout=10
            )

            # Start new container
            self._logger.info(f"Starting PostgreSQL container: {self.container_name}")
            docker_cmd = [
                "docker",
                "run",
                "--name",
                self.container_name,
                "-e",
                f"POSTGRES_USER={config['user']}",
                "-e",
                f"POSTGRES_PASSWORD={config['password']}",
                "-e",
                f"POSTGRES_DB={config['database']}",
                "-p",
                f"{config['port']}:5432",
                "-v",
                f"{self.container_name}_data:/var/lib/postgresql/data",
                "-d",
                "postgres:15",
            ]

            result = subprocess.run(
                docker_cmd, capture_output=True, text=True, timeout=30
            )

            if result.returncode != 0:
                self._logger.error(f"Failed to start container: {result.stderr}")
                return False

            # Wait for PostgreSQL to be ready
            self._logger.info("Waiting for PostgreSQL to be ready...")
            for _i in range(30):  # Wait up to 30 seconds
                if self.is_database_accessible(config["host"], config["port"]):
                    break
                time.sleep(1)
            else:
                self._logger.error("PostgreSQL container did not become ready in time")
                return False

            # Create required extensions
            self._create_extensions()

            self._logger.info("✅ PostgreSQL container started successfully")
            return True

        except subprocess.TimeoutExpired:
            self._logger.error("Docker command timed out")
            return False
        except Exception as e:
            self._logger.error(f"Failed to start database container: {e}")
            return False

    def _create_extensions(self) -> None:
        """Create required PostgreSQL extensions."""
        config = self.default_db_config
        extensions = [
            'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";',
            'CREATE EXTENSION IF NOT EXISTS "btree_gin";',
        ]

        for ext_sql in extensions:
            try:
                subprocess.run(
                    [
                        "docker",
                        "exec",
                        self.container_name,
                        "psql",
                        "-U",
                        config["user"],
                        "-d",
                        config["database"],
                        "-c",
                        ext_sql,
                    ],
                    capture_output=True,
                    timeout=10,
                )
            except Exception as e:
                self._logger.warning(f"Failed to create extension: {e}")

    def ensure_database_available(self) -> dict[str, Any]:
        """
        Ensure PostgreSQL database is available.

        Returns:
            Dict with status information:
            - available: bool - Whether database is accessible
            - auto_started: bool - Whether we auto-started the container
            - message: str - Status message
            - database_url: str - Connection URL if available
        """
        config = self.default_db_config
        host, port = config["host"], config["port"]

        # Check if database is already accessible
        if self.is_database_accessible(host, port):
            self._logger.info("✅ PostgreSQL is already accessible")
            return {
                "available": True,
                "auto_started": False,
                "message": "Database already accessible",
                "database_url": self._get_connection_url(),
            }

        # If auto-start is disabled, return not available
        if not self.auto_start:
            self._logger.info("Database not accessible and auto-start disabled")
            return {
                "available": False,
                "auto_started": False,
                "message": "Database not accessible, auto-start disabled",
                "database_url": None,
            }

        # Try to auto-start database container
        self._logger.info("Database not accessible, attempting auto-start...")

        if self.start_database_container():
            return {
                "available": True,
                "auto_started": True,
                "message": "Database auto-started successfully",
                "database_url": self._get_connection_url(),
            }
        else:
            return {
                "available": False,
                "auto_started": False,
                "message": "Failed to auto-start database",
                "database_url": None,
            }

    def _get_connection_url(self) -> str:
        """Get the database connection URL."""
        if self.database_url:
            return self.database_url

        config = self.default_db_config
        return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"

    def get_status(self) -> dict[str, Any]:
        """Get current database status."""
        config = self.default_db_config

        return {
            "database_accessible": self.is_database_accessible(
                config["host"], config["port"]
            ),
            "docker_available": self.is_docker_available(),
            "container_running": self.is_container_running(self.container_name),
            "auto_start_enabled": self.auto_start,
            "container_name": self.container_name,
            "connection_url": self._get_connection_url(),
        }

    def stop_container(self) -> bool:
        """Stop the database container."""
        if not self.is_docker_available():
            return False

        try:
            result = subprocess.run(
                ["docker", "stop", self.container_name], capture_output=True, timeout=15
            )
            return result.returncode == 0
        except Exception as e:
            self._logger.error(f"Failed to stop container: {e}")
            return False
