#!/bin/bash
# DocMD Setup
# Version: 0.0.1
# Authors: webmarka
# 2025-03-11 (v0.0.1) - New bash version.
# source ./setup.sh

echo
echo -e "#######################################################################"
echo -e "#                                DocMD                                #"
echo -e "#######################################################################"
echo

# Install Python 3 (commented as assumed already installed)
# sudo yum install python3
# sudo apt-get install python3

# Update pip (commented as optional)
# python3 -m pip install --upgrade pip

# Environment
echo -e "- Setup Virtual Environment." ; echo
# sudo apt-get install -y python3-venv
APP_NAME=docmd
INIT_LOC=$(pwd)
ENV_PATH="../../environments/"
ENV_APP_PATH="${ENV_PATH}${APP_NAME}/"
if [ ! -d "${ENV_APP_PATH}" ] ; then
  mkdir -p "${ENV_PATH}"
  cd "${ENV_PATH}"
  python3 -m venv "${APP_NAME}"
  cd "${INIT_LOC}"
fi
source "${ENV_APP_PATH}bin/activate"

# Python packages
echo -e "- Install Python packages." ; echo
pip3 install python-dotenv
pip3 install Markdown
pip3 install Jinja2
pip3 install shutils
# pip3 install urllib3
# pip3 install mkdocs

# Unit tests
echo -e "- Running unit tests..." ; echo
python3 ./test_docmd.py
echo -e "\n--- Tests completed ---\n"

# Run app
echo -e "- Start the app." ; echo
python3 ./docmd.py

# Exit the script properly
echo
echo -e "======================================================================="
echo
# exit 0
