#!/bin/bash
# DocMD Setup
# Version: 0.0.2
# Authors: webmarka
# 2025-03-13 (v0.0.2) - Added unit tests.
# Usage: source ./setup.sh or ./setup.sh

echo
echo -e "#######################################################################"
echo -e "#                                DocMD                                #"
echo -e "#######################################################################"
echo

# Version
echo "- Version: 0.0.2"

# Check if python3 is available
echo "Checking for python3..."
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed or not in PATH."
    exit 1
fi

# Setup Virtual Environment
echo
echo "- Setup Virtual Environment."
echo

APP_NAME=docmd
INIT_LOC=$(pwd)
DEFAULT_VENV_PATH="$HOME/.docmd/venv"
VENV_PATH="${VENV_PATH:-$DEFAULT_VENV_PATH}"
VENV_PARENT_DIR="$(dirname "$VENV_PATH")"

echo "Using VENV_PATH: $VENV_PATH"

# Create the parent folder if necessary
if [ ! -d "$VENV_PARENT_DIR" ]; then
    echo "Creating parent directory: $VENV_PARENT_DIR"
    mkdir -p "$VENV_PARENT_DIR" || {
        echo "Error: Failed to create $VENV_PARENT_DIR (permissions issue?)"
        exit 1
    }
fi

# Create the virtual environment if it does not exist
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment at: $VENV_PATH"
    python3 -m venv "$VENV_PATH" || {
        echo "Error: Failed to create virtual environment at $VENV_PATH"
        exit 1
    }
    echo "Sleeping for 1 second to ensure venv is ready..."
    sleep 1
fi

# Activate the virtual environment
if [ -f "$VENV_PATH/bin/activate" ]; then
    echo "Activating virtual environment: $VENV_PATH"
    source "$VENV_PATH/bin/activate" || {
        echo "Error: Failed to activate virtual environment at $VENV_PATH"
        exit 1
    }
else
    echo "Error: Virtual environment activation file not found at $VENV_PATH/bin/activate"
    exit 1
fi

# Install Python packages
echo
echo "- Install Python packages."
echo
echo "Running pip install..."
pip install python-dotenv Markdown Jinja2 shutils || {
    echo "Error: Failed to install Python packages"
    exit 1
}

# Running unit tests
echo
echo "- Running unit tests..."
echo
if [ -f "./test_docmd.py" ]; then
    echo "Executing python3 ./test_docmd.py..."
    python3 ./test_docmd.py || {
        echo "Warning: Unit tests failed, continuing anyway"
    }
else
    echo "Warning: test_docmd.py not found, skipping tests"
fi

echo
echo "--- Tests completed ---"
echo

# Start the app
echo
echo "- Start the app."
echo
if [ -f "./docmd.py" ]; then
    echo "Executing python3 ./docmd.py..."
    python3 ./docmd.py || {
        echo "Error: Failed to run docmd.py"
        exit 1
    }
else
    echo "Error: docmd.py not found"
    exit 1
fi

# Footer
echo
echo -e "======================================================================="
echo
