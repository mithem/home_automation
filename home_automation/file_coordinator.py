"""File coordinator."""
import asyncio
import os
from logging import Logger
from typing import List, Optional

from home_automation.config import Config
from home_automation.file_coordinator_middleware import (
    FileCoordinatorMiddleware,
    LaTeXToPDFMiddleware,
    MarkdownToPDFMiddleware,
)


class FileCoordinator:  # pylint: disable=too-few-public-methods
    """`FileCoordinator` is invoked on appropriate directories just like
    `CompressionManager`, except it handles everything else than compressing."""

    config: Config
    logger: Optional[Logger]
    middlewares: List[FileCoordinatorMiddleware]

    def __init__(self, config: Config, logger: Logger = None):
        self.config = config
        self.logger = logger
        self.middlewares = [
            LaTeXToPDFMiddleware(config, logger),
            MarkdownToPDFMiddleware(config, logger),
        ]

    async def handle_directory(self, path: str):
        """Handle the directory."""
        for fname in os.listdir(path):
            full_path = os.path.join(path, fname)
            for middleware in self.middlewares:
                if await middleware.test(full_path):
                    await middleware.act(full_path)


def run_file_coordinator(config: Config, path: str, logger: Logger = None):
    """Run the file coordinator."""
    coordinator = FileCoordinator(config, logger)
    asyncio.run(coordinator.handle_directory(path))
