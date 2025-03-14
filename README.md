# DocMD

**DocMD** is a lightweight tool to generate a static documentation website from Markdown files located in your project's source directories. It creates a navigable HTML structure with an intuitive sidebar, perfect for documenting code or projects, usable locally or on a web server.

## Version

- **0.0.3** (March 2025) - Customizations, themes and dark mode.

## Features

- Automatic conversion of Markdown files to HTML.
- Generation of a sidebar navigation with folder hierarchy.
- Index pages for each folder containing Markdown files.
- Correct relative paths for seamless navigation in local (`file://`) or web server contexts.
- User customizations, themes and dark mode.
- Built-in unit tests to validate generation.

## Prerequisites

- Python 3.10+
- Dependencies: `python-dotenv`, `Markdown`, `Jinja2`, `shutils` (installed via `setup.sh`).

## Installation

**Clone the project:**

    # bash
    cd /path/to/project
    git clone git@gitlab.com:webmarka/docmd.git docmd
    cd docmd

**Set up the environment:**

- Place your Markdown files in the `src/` folder (or customize via `INCLUDE_PATHS` in `.env`).
- Create a `.env` file with your custom parameters (see example below).
- Optionally, add `.env.development` and `.env.production` for environment-specific overrides.

**Example `.env`:**

    ENV=dev
    LANG=en_US.UTF-8  # Converted to 'en-US' for HTML
    INCLUDE_PATHS=src
    EXCLUDE_PATHS=.git,.hg
    SAVE_DIR=docs
    OUTPUT_DIR=docs
    BACKUP_DIR=~/.docmd/archives
    VENV_PATH=~/.docmd/venv
    TEMPLATE=default.html
    NAV_TITLE=Documentation
    THEME=default
    USE_EXTERNAL_ASSETS=False

**Run the setup and generation script:**

  `./setup.sh`

- Creates a virtual environment in `~/.docmd/venv/` (or as set in `VENV_PATH`).
- Installs Python dependencies.
- Runs unit tests.
- Generates the static site in `docs/`, with backups in `~/.docmd/archives/` (or as set in `BACKUP_DIR`).

After the first run, you can use the `source ./setup.sh` command instead and enter into the Python environment at the same time. 

## Usage

- Open `docs/index.html` in a browser to explore the generated documentation.
- To test on a local server:  

    # bash
    cd docs
    python3 -m http.server

Then visit [http://localhost:8000](http://localhost:8000).

## Troubleshooting

On the first run, you may need to install some packages et the Python environment will be set up. If any problem occurs while running `source ./setup.py`, use this instead (prevents the terminal to close on error): 

    # bash
    ./setup.py

## Customization

- **Input paths:** Modify `INCLUDE_PATHS` in `.env` to point to your Markdown folders (e.g., `INCLUDE_PATHS=../src1,../src2`).
- **Excluded paths:** Adjust `EXCLUDE_PATHS` to skip specific folders (e.g., `.git,.hg`).

## Changelog

- **0.0.3** (March 2025) - Customizations, themes and dark mode.
- **0.0.2** (March 2025) - Improved navigation, robust unit tests, folder index page generation.
- **0.0.1** (March 2025) - First proof-of-concept version.
