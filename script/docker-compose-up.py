#!/usr/bin/python3
# pylint: disable=invalid-name
"""Compose up the configured docker-compose file."""
import home_automation.server.backend
home_automation.server.backend.compose_up_exec()
