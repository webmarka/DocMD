#!/bin/bash
# DocMD Setup
# Version: 0.0.4
# Authors: webmarka
# 2025-03-14 (v0.0.3) - Added security checks.
# Usage: source ./setup.sh or ./setup.sh

echo
echo -e " ####################################################################### "
echo -e " #                                DocMD                                # "
echo -e " ####################################################################### "
echo

# Version.
echo " Version: 0.0.4 "
echo

# Check if virtual env still exists.
if [ -n "$VIRTUAL_ENV" ] && [ ! -d "$VIRTUAL_ENV" ]; then
    echo " Warning: Current virtual environment ($VIRTUAL_ENV) is invalid. Deactivating..."
    echo
    deactivate
fi

# Script params.
#echo
echo " Script params."
#echo
APP_NAME=docmd
# Script and Command options.
SELF_PATH=$(realpath $0)
SELF_LOC=$(dirname "${SELF_PATH}")
INIT_LOC=$(pwd)
CURRENT_PID=$$
VERBOSITY=""
STRICT_MODE="no"

# Virtual Env.
DEFAULT_VENV_PATH="$HOME/.${APP_NAME:-app_name}/venv"
VENV_PATH="${VENV_PATH:-$DEFAULT_VENV_PATH}"
VENV_PARENT_DIR="$(dirname "${VENV_PATH}")"

# Scripts.
TEST_FILE="test_${APP_NAME}.py"
TEST_FILE_PATH="./${TEST_FILE}"
APP_SCRIPT_FILENAME="${APP_NAME:-app_name}.py"
APP_SCRIPT_PATH="${SELF_LOC}/${APP_SCRIPT_FILENAME}"

# Params.
echo " CURRENT_PID: ${CURRENT_PID}"
echo " SELF_PATH: ${SELF_PATH}"
echo " SELF_LOC: ${SELF_LOC}"
echo " INIT_LOC: ${INIT_LOC}"
[ "" != "${VERBOSITY}" ] && echo " VERBOSITY: ${VERBOSITY}"
[ "yes" == "${STRICT_MODE}" ] && echo " STRICT_MODE: ${STRICT_MODE}"
[ "" != "${VERBOSITY}" ] && echo " DEFAULT_VENV_PATH: ${DEFAULT_VENV_PATH}"
[ "" != "${VERBOSITY}" ] && echo " VENV_PATH: ${VENV_PATH}"
[ "" != "${VERBOSITY}" ] && echo " VENV_PARENT_DIR: ${VENV_PARENT_DIR}"

# Check for dependencies.
echo
echo " Check for dependencies..."
echo

# Check if python3 is available.
echo " Checking for python3..."
echo
if ! command -v python3 &> /dev/null; then
    echo " Error: python3 is not installed or not in PATH."
    exit 1
fi

# Check if pip3 is available.
echo " Checking for pip3..."
#echo
if ! command -v pip3 --version &> /dev/null; then
    echo " Error: pip3 is not installed or not in PATH."
    exit 1
fi

# Setup Virtual Environment.
echo
echo " Setup Virtual Environment..."
echo
# Create the parent folder if necessary.
if [ ! -d "${VENV_PARENT_DIR}" ]; then
    echo " Creating parent directory: ${VENV_PARENT_DIR}"
    mkdir -p "${VENV_PARENT_DIR}" || {
        echo " Error: Failed to create ${VENV_PARENT_DIR} (permissions issue?)"
        [ "yes" == "${STRICT_MODE}" ] && exit 1
    }
fi

# Create the virtual environment if it does not exist.
if [ ! -d "$VENV_PATH" ]; then
    echo " Creating virtual environment at: ${VENV_PATH}"
    python3 -m venv "${VENV_PATH}" || {
        echo " Error: Failed to create virtual environment at ${VENV_PATH}"
        [ "yes" == "${STRICT_MODE}" ] && exit 1
    }
    echo " Sleeping a bit to ensure venv is ready..."
    sleep 2
fi

# Activate the virtual environment.
if [ -f "${VENV_PATH}/bin/activate" ]; then
    echo " Activating virtual environment: ${VENV_PATH}"
    source "${VENV_PATH}/bin/activate" || {
        echo " Error: Failed to activate virtual environment at ${VENV_PATH}"
        [ "yes" == "${STRICT_MODE}" ] && exit 1
    }
else
    echo " Error: Virtual environment activation file not found at ${VENV_PATH}/bin/activate"
    [ "yes" == "${STRICT_MODE}" ] && exit 1
fi

# Install Python packages.
echo
echo " Install Python packages..."
echo
echo " Running pip3 install..."
pip3 install python-dotenv Markdown Jinja2 shutils || {
    echo " Error: Failed to install Python packages"
    exit 1
}

# Running unit tests.
echo
echo " Running unit tests..."
echo
echo " --- Tests beginning --- "
echo
if [ -f "${TEST_FILE_PATH}" ]; then
    echo " Executing python3 ${TEST_FILE_PATH}..."
    python3 "${TEST_FILE_PATH}" || {
        echo " Warning: Unit tests failed, continuing anyway"
    }
else
    echo " Warning: ${TEST_FILE} not found, skipping tests"
fi
echo
echo " --- Tests completed --- "
#echo

# Start the app.
echo
echo " Start the app..."
echo
if [ -f "${APP_SCRIPT_PATH}" ]; then
    echo " Executing python3 ${APP_SCRIPT_PATH}..."
    python3 ./docmd.py || {
        echo " Error: Failed to run ${APP_SCRIPT_FILENAME}"
        [ "yes" == "${STRICT_MODE}" ] && exit 1
    }
else
    echo " Error: ${APP_SCRIPT_FILENAME} not found"
    [ "yes" == "${STRICT_MODE}" ] && exit 1
fi

# Footer.
echo
echo -e "======================================================================="
echo
