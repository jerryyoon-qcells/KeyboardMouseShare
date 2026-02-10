"""
Main entry point for Keyboard Mouse Share application.

Handles CLI argument parsing and application initialization.
"""

import argparse
import logging
import sys
from pathlib import Path

from src.config import Config
from src.logger import setup_logging


def main() -> int:
    """
    Main entry point for the application.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Share keyboard and mouse across Windows and macOS devices on local network",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  keyboard-mouse-share --role master --device-name "My MacBook"
  keyboard-mouse-share --role client --discover
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0-dev",
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to configuration file (default: ~/.keyboard-mouse-share/config.json)",
    )

    parser.add_argument(
        "--role",
        choices=["master", "client", "unassigned"],
        default="unassigned",
        help="Device role: master (controls input) or client (receives input)",
    )

    parser.add_argument(
        "--device-name",
        type=str,
        default=None,
        help="User-friendly device name (e.g., 'My MacBook')",
    )

    parser.add_argument(
        "--discover",
        action="store_true",
        help="Scan network for available devices",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = setup_logging(log_level=log_level)

    try:
        logger.info("Starting Keyboard Mouse Share application")
        logger.info(f"Role: {args.role}")

        if args.device_name:
            logger.info(f"Device name: {args.device_name}")

        if args.discover:
            logger.info("Discovery mode enabled")

        # Load configuration
        config = Config(config_file=args.config)
        logger.info(f"Configuration loaded from: {config.config_file}")

        # TODO: Initialize application components
        # - Start mDNS discovery service
        # - Initialize input handler
        # - Start network server
        # - Launch UI

        logger.info("Application initialization complete")
        return 0

    except KeyboardInterrupt:
        logger.info("Received shutdown signal (Ctrl+C)")
        return 0
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
