#!/bin/bash

# Stop the script on errors
set -e

# Install dependencies
make install

# Set up the database
make setup-db

# Run the bot
make run
