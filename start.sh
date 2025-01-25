#!/bin/bash

# Stop the script on errors
set -e

# Set up the database
make setup-db

# Run the bot
make run
