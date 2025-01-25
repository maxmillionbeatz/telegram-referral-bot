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

# Path for lock file to prevent multiple instances
LOCK_FILE = "/tmp/bot.lock"


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


def main():
    """
    Main function to initialize the bot and start polling.
    """
    print("Connecting to database...")
    init_db_pool()

    print("Resetting Telegram webhook (if any)...")
    bot.remove_webhook()  # Reset any active webhooks to avoid conflicts

    print("Starting the bot...")
    atexit.register(close_db_pool)  # Ensure database cleanup on exit

    # Handle termination signals for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    try:
        bot.infinity_polling()  # Start polling
    finally:
        # Cleanup lock file and close database pool on exit
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
        close_db_pool()


if __name__ == "__main__":
    ensure_single_instance()  # Prevent multiple instances
    main()  # Start the bot
