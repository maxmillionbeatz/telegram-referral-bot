"""
Main entry point for the Telegram Referral Bot.

This script initializes the bot, handles database connections, ensures graceful
shutdown during redeployment, and prevents multiple bot instances from running.
"""

from src import bot
from src.db_setup import close_db_pool, init_db_pool
import atexit
import os
import signal
import sys
import time
import logging
from telebot import logger

# Path for lock file to prevent multiple instances
LOCK_FILE = "/tmp/bot.lock"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.INFO)  # Enable detailed logging for TeleBot


def handle_shutdown(signum, frame):
    """
    Handles termination signals (SIGINT, SIGTERM) to gracefully shut down the bot.
    """
    print(f"Received signal {signum}. Shutting down gracefully...")
    close_db_pool()
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
    sys.exit(0)


def ensure_single_instance():
    """
    Ensures that only one instance of the bot is running by creating a lock file.
    """
    if os.path.exists(LOCK_FILE):
        print("Another instance of the bot is already running. Exiting...")
        sys.exit(1)
    with open(LOCK_FILE, "w") as f:
        f.write("locked")


def reset_webhook():
    """
    Resets the Telegram webhook to ensure no lingering webhooks interfere with polling.
    """
    print("Resetting Telegram webhook (if any)...")
    try:
        bot.remove_webhook()
        print("Webhook reset successfully.")
    except Exception as e:
        print(f"Failed to reset webhook: {e}")


def start_polling_with_retry():
    """
    Starts Telegram bot polling with retry logic to handle transient network issues.
    """
    while True:
        try:
            print("Starting the bot...")
            bot.infinity_polling(
                timeout=60, long_polling_timeout=60
            )  # Increased timeouts
        except Exception as e:
            logging.error(f"Polling error: {e}")
            print("Retrying polling in 5 seconds...")
            time.sleep(5)  # Retry after a delay


def main():
    """
    Main function to initialize the bot and start polling.
    """
    print("Connecting to database...")
    try:
        init_db_pool()
        print("Database connection pool initialized.")
    except Exception as e:
        print(f"Failed to initialize database pool: {e}")
        sys.exit(1)  # Exit if the database cannot be initialized

    # Reset webhook to avoid conflicts
    reset_webhook()

    # Register the database cleanup function to be called on exit
    atexit.register(close_db_pool)

    # Handle termination signals for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    # Start polling with retry logic
    start_polling_with_retry()


if __name__ == "__main__":
    ensure_single_instance()  # Prevent multiple instances
    main()  # Start the bot
