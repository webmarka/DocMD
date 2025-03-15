# DocMD
# Description: Generate a static documentation website from Markdown files in a project's source-code.
# Version: 0.0.3
# Authors: webmarka
# URL: https://gitlab.com/webmarka/docmd

# Imports
import os
from dotenv import load_dotenv
from pathlib import Path
import markdown
import jinja2
import shutil
from datetime import datetime
from urllib.parse import quote

# Environment setup
debug = False
load_dotenv()
ENV = os.environ.get("ENV", "prod")
if ENV == "prod":
    load_dotenv(".env.prod")
elif ENV == "dev":
    load_dotenv(".env.dev")
    debug = True

# Utility to convert comma-separated string to a list of Path objects
def get_paths(string):
    paths = []
    for base_path in get_config_array(string):
        paths.append(Path(base_path))
    return paths

# Utility to split and strip a comma-separated string
def get_config_array(string):
    return list(map(str.strip, string.split(',')))

# Function to clean LANG in BCP 47 code
def clean_lang(lang_str):
    """ Convert a POSIX locale (e.g., 'en_US.UTF-8') to a BCP 47 language tag (e.g., 'en-US')."""
    base_lang = lang_str.split(".")[0].replace("_", "-")
    return base_lang

# Configuration
LANG = clean_lang(os.environ.get("LANG", "en_US.UTF-8"))
INCLUDE_PATHS = get_paths(os.environ.get("INCLUDE_PATHS", "src"))
EXCLUDE_PATHS = get_paths(os.environ.get("EXCLUDE_PATHS", ".git,.hg"))
SAVE_DIR = Path(os.environ.get("SAVE_DIR", "docs"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "docs"))
TEMPLATE = os.environ.get("TEMPLATE", "default.html")
BACKUP_DIR = Path(os.path.expanduser(os.getenv("BACKUP_DIR", "~/.docmd/archives")))
DATE_TAG = datetime.now().strftime("%Y%m%d-%H%M%S")
DATE_TAG_HUMAN = datetime.now().strftime("%Y-%m-%d at %H:%M:%S")

# Variables.
APP_NAME = 'DocMD'
APP_VERSION = '0.0.3'
APP_URL = 'https://docmd.us/'
NAV_TITLE = os.environ.get("NAV_TITLE", "Documentation")
ASSETS_PATH = 'static'
CSS_PATH = 'static/css/style.css'
THEMES = {'default', 'dark'}
THEME = os.environ.get("THEME", "default")
THEME_MODE = 'dark' if THEME == 'dark' else 'light'
FOOTER = f"Powered by <a href=\"{APP_URL}\" target=\"_blank\">{APP_NAME}</a><br /><small>Document generated on {DATE_TAG_HUMAN}</small>"
USE_EXTERNAL_ASSETS = os.environ.get("USE_EXTERNAL_ASSETS", 'False')
BS_CSS_URL = "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
BS_CSS_PATH = 'static/css/bootstrap.min.css'

# Check if a file path should be excluded
def should_exclude(file_path, exclude_paths):
    """ Check if a file or folder should be excluded."""
    return any(excluded in file_path.parents or file_path == excluded for excluded in exclude_paths)

# Scan for Markdown files and build hierarchy
def scan_markdown_files(include_paths, exclude_paths):
    """ Scan folders for Markdown files and return their metadata and folder hierarchy."""
    markdown_files = []
    folders_with_md = []  # List to preserve order
    
    for base_path in include_paths:
        for root, _, files in os.walk(base_path):
            root_path = Path(root)
            has_md = False
            for file in files:
                if file.endswith(".md"):
                    file_path = root_path / file
                    if not should_exclude(file_path, exclude_paths):
                        has_md = True
                        rel_path = file_path.relative_to(base_path).with_suffix(".html")
                        markdown_files.append({
                            "file_path": file_path,
                            "rel_path": str(rel_path),
                            "title": file_path.stem,
                            "parent": str(file_path.parent.relative_to(base_path)) if file_path.parent != base_path else None
                        })
            if has_md:
                current = root_path
                while current != base_path.parent and current != current.parent:
                    rel_folder = str(current.relative_to(base_path))
                    if rel_folder not in folders_with_md and rel_folder != ".":
                        folders_with_md.append(rel_folder)
                    current = current.parent
    
    # Build hierarchy with index pages for relevant folders
    hierarchy = {}
    for folder in sorted(folders_with_md):
        folder_path = Path(folder) / "index.html"
        hierarchy[str(folder_path)] = {
            "title": folder.split('/')[-1] if folder else "Home",
            "rel_path": str(folder_path),
            "target_path": str(folder_path),
            "sub_pages": [],
            "is_folder": True
        }
    if any(not file["parent"] for file in markdown_files):
        hierarchy["index.html"] = {
            "title": "Home",
            "rel_path": "index.html",
            "target_path": "index.html",
            "sub_pages": [],
            "is_folder": True
        }
    
    for file in markdown_files:
        parent_key = str(Path(file["parent"] or "").joinpath("index.html")) if file["parent"] else "index.html"
        filename = os.path.basename(file["file_path"])
        if file["rel_path"] != parent_key:
            hierarchy[parent_key]["sub_pages"].append({
                "title": file["title"],
                "rel_path": file["rel_path"],
                "target_path": str(file["file_path"]),
                "is_folder": False
            })
    
    for page in hierarchy.values():
        page["sub_pages"].sort(key=lambda x: x["rel_path"])
    
    return markdown_files, list(hierarchy.values())

# Save a Markdown file to the output directory
def save_md_file(md_file, save_dir, base_path):
    """ Save Markdown files to a folder."""
    relative_path = md_file.relative_to(base_path)
    save_subdir = save_dir / relative_path.parent
    save_subdir.mkdir(parents=True, exist_ok=True)
    save_file = save_subdir / md_file.name
    shutil.copyfile(md_file, save_file)
    print(f" Saved: {save_file}")

# Convert Markdown file to HTML
def convert_md_to_html(md_file_info, output_dir, all_pages, base_path):
    """ Convert a Markdown file to HTML and place it in the output tree."""
    md_file = md_file_info["file_path"]
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()
    
    html_content = markdown.markdown(md_content)
    relative_path = md_file.relative_to(base_path)
    output_subdir = output_dir / relative_path.parent
    output_subdir.mkdir(parents=True, exist_ok=True)
    output_file = output_subdir / (md_file.stem + ".html")
    current_page = md_file_info["rel_path"]
    current_dir = os.path.dirname(current_page) or "."
    adjusted_pages = get_pages_links(current_dir, all_pages, base_path)
    title=md_file_info["title"]
    css_path = get_relative_path(CSS_PATH, current_dir)
    theme_css_path = get_theme_css_path(current_dir)
    assets_path = get_relative_path(ASSETS_PATH, current_dir)
    bs_css_path = get_relative_path(BS_CSS_PATH, current_dir)
    bs_css_path = BS_CSS_URL if USE_EXTERNAL_ASSETS != 'False' else bs_css_path
    
    if debug:
        print(f" Generating page {title}, current_page: {current_page}")
    
    generate_page(current_page, title, html_content, output_file, adjusted_pages, css_path, theme_css_path, assets_path, bs_css_path)

# Generate folder index page
def generate_folder_index(folder_path, output_dir, all_pages, sub_pages, base_path):
    """ Generate an index.html for a folder."""
    output_file = output_dir / folder_path / "index.html"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    current_page = str(folder_path / "index.html" if folder_path.name else "index.html")
    current_dir = os.path.dirname(current_page) or "."
    adjusted_pages = get_pages_links(current_dir, all_pages, base_path)
    title = folder_path.name if folder_path.name else "Home"
    css_path = get_relative_path(CSS_PATH, current_dir)
    theme_css_path = get_theme_css_path(current_dir)
    assets_path = get_relative_path(ASSETS_PATH, current_dir)
    bs_css_path = get_relative_path(BS_CSS_PATH, current_dir)
    bs_css_path = BS_CSS_URL if USE_EXTERNAL_ASSETS != 'False' else bs_css_path
    
    if debug:
        print(f" Generating index for {folder_path}, current_page: {current_page}, sub_pages: {sub_pages}")
    
    content = f"<h2>{title}</h2><ul>"
    for sub_page in sub_pages:
        sub_target_path = sub_page["rel_path"]
        sub_rel_path = get_relative_path(sub_target_path, current_dir)
        content += f"<li><a href='{quote(sub_rel_path)}'>{sub_page['title']}</a></li>"
    content += "</ul>"
    
    generate_page(current_page, title, content, output_file, adjusted_pages, css_path, theme_css_path, assets_path, bs_css_path)

def generate_page(current_page, title, content, output_file, pages, css_path, theme_css_path, assets_path, bs_css_path):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
    try:
        template = env.get_template(TEMPLATE)
    except jinja2.TemplateNotFound:
        print(f" Error: Template '{TEMPLATE}' not found in 'templates/'")
        return
    title = title if title else "Home"
    
    html_output = template.render(
        title=title,
        content=content,
        lang=LANG,
        pages=pages,
        current_page=current_page,
        css_path=css_path,
        theme_css_path=theme_css_path,
        theme_mode=THEME_MODE,
        assets_path=assets_path,
        footer=FOOTER,
        app_name=APP_NAME,
        nav_title=NAV_TITLE,
        bs_css_path=bs_css_path,
        app_version=APP_VERSION
    )
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f" Generated: {output_file}")

def get_pages_links(current_dir, all_pages, base_path):
    pages = []
    for page in all_pages:
        #target_path = page["target_path"]
        rel_path = get_relative_path(page["rel_path"], current_dir)
        page = page.copy()
        page["rel_path"] = rel_path
        #page["target_path"] = target_path
        page["sub_pages"] = [
            {**sub, "rel_path": get_relative_path(sub["rel_path"], current_dir), "target_path": get_relative_path(sub["target_path"], base_path).replace(".md", ".html")}
            for sub in page["sub_pages"]
        ]
        pages.append(page)
    
    return pages

# Get relative path from current directory.
def get_relative_path(target_path, current_dir):
    rel_path = os.path.relpath(target_path, current_dir).replace("\\", "/")
    return rel_path or target_path

def get_theme(theme):
    if theme and theme in THEMES: 
      return theme
    else:
      return get_default_theme()

def get_current_theme():
    current_theme = THEME if THEME else get_default_theme();
    return current_theme;

def get_default_theme():
    return 'default';

def get_theme_css_path(current_dir):
    current_theme = get_current_theme()
    theme = get_theme(current_theme)
    THEME_CSS_PATH = f"static/css/style-{theme}.css"
    theme_css_path = get_relative_path(THEME_CSS_PATH, current_dir)
    return theme_css_path

# Security check for directories
def directory_security_check(directory):
    """ Check if a directory is safe to use."""
    return (
        directory != Path("") and
        directory != Path(".") and
        directory != Path("..") and
        not directory.is_absolute() and
        directory != Path("/") and
        directory != Path("./")
    )

# Clean a directory with backup
def clean_dir(directory):
    """ Clean a directory with a backup."""
    if not directory_security_check(directory):
        print(f" Error: Attempt to clean invalid directory '{directory}' skipped.")
        return False
    backup_dir = BACKUP_DIR / f"{directory.name}_{DATE_TAG}"
    if directory.exists():
        print(f" Backing up '{directory}' to '{backup_dir}'.")
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(directory, backup_dir)
        except Exception as e:
            print(f" Error: Failed to backup '{directory}' to '{backup_dir}': {e}")
            return False
    directory.mkdir(parents=True, exist_ok=True)
    return True

# Main site generation function.
def generate_site():
    """ Generate the static site."""
    global OUTPUT_DIR  # Déplacé en haut
    # Validate and clean directories
    if not directory_security_check(OUTPUT_DIR):
        print(f" Warning: OUTPUT_DIR '{OUTPUT_DIR}' is unsafe, resetting to 'docs'.")
        OUTPUT_DIR = Path("docs")
    
    clean_dir(OUTPUT_DIR)  # Nettoie uniquement OUTPUT_DIR
    
    # Use SAVE_DIR if specified and safe, otherwise use OUTPUT_DIR
    save_dir = OUTPUT_DIR
    if directory_security_check(SAVE_DIR) and SAVE_DIR != OUTPUT_DIR:
        clean_dir(SAVE_DIR)
        save_dir = SAVE_DIR
    
    # Check if INCLUDE_PATHS exist
    for path in INCLUDE_PATHS:
        if not path.exists():
            print(f" Error: Source path '{path}' does not exist.")
            return
    
    md_files, pages_hierarchy = scan_markdown_files(INCLUDE_PATHS, EXCLUDE_PATHS)
    if not md_files:
        print(' Sources folders empty.')
        return
    
    print("\n Copy MD files.")
    for md_file in md_files:
        base_path = next(bp for bp in INCLUDE_PATHS if md_file["file_path"].is_relative_to(bp))
        save_md_file(md_file["file_path"], save_dir, base_path)
    
    print("\n Write HTML files.")
    for md_file in md_files:
        base_path = next(bp for bp in INCLUDE_PATHS if md_file["file_path"].is_relative_to(bp))
        convert_md_to_html(md_file, OUTPUT_DIR, pages_hierarchy, base_path)
    
    print("\n Generate folder indexes.")
    for page in pages_hierarchy:
        folder_path = Path(page["rel_path"]).parent
        generate_folder_index(folder_path, OUTPUT_DIR, pages_hierarchy, page["sub_pages"], base_path)
    
    print("\n Copy the static assets folder.")
    #assets_path = get_relative_path(ASSETS_PATH, save_dir)
    #assets_path = docmd.get_relative_path('../static/css/', 'src/')
    shutil.copytree("./static", f"{save_dir}/static")

# Main function
if __name__ == "__main__":
    generate_site()
