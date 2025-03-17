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
import json

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

# Environnement Jinja2 global
JINJA_ENV = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))

# Filtre personnalisé
def has_active_subpage(sub_pages, current_page):
    return any(sub["rel_path"] == current_page for sub in sub_pages)

JINJA_ENV.filters['has_active_subpage'] = has_active_subpage

# Configuration
LANG = clean_lang(os.environ.get("LANG", "en_US.UTF-8"))
#INCLUDE_PATHS = get_paths(os.environ.get("INCLUDE_PATHS", "src"))
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

# Utility to parse INCLUDE_PATHS as string or JSON list of dicts
def parse_include_paths(env_value):
    if not env_value:
        return [{"path": "src", "name": "Source", "excludes": EXCLUDE_PATHS}]
    try:
        # Si c’est un JSON (liste de dicts)
        parsed = json.loads(env_value)
        if isinstance(parsed, list):
            return [
                {
                    "path": p if isinstance(p, str) else p.get("path", "src"),
                    "name": p.get("name", Path(p["path"]).name) if isinstance(p, dict) else Path(p).name,
                    "excludes": get_paths(p.get("excludes", "")) if isinstance(p, dict) else EXCLUDE_PATHS
                }
                for p in parsed
            ]
    except json.JSONDecodeError:
        # Si c’est une string simple (ancien format)
        return [{"path": p, "name": Path(p).name, "excludes": EXCLUDE_PATHS} for p in get_config_array(env_value)]
    return [{"path": "src", "name": "Source", "excludes": EXCLUDE_PATHS}]

INCLUDE_PATHS = parse_include_paths(os.environ.get("INCLUDE_PATHS", "src"))

# Check if a file path should be excluded
def should_exclude(file_path, exclude_paths):
    """ Check if a file or folder should be excluded."""
    return any(excluded in file_path.parents or file_path == excluded for excluded in exclude_paths)

# Scan for Markdown files and build hierarchy
def scan_markdown_files(projects, global_exclude_paths):
    markdown_files = []
    folders_with_md = []
    project_groups = {}

    for project in projects:
        base_path = Path(project["path"])
        project_name = project["name"]
        exclude_paths = project["excludes"] + global_exclude_paths
        project_files = []
        project_folders = []

        for root, _, files in os.walk(base_path):
            root_path = Path(root)
            has_md = False
            for file in files:
                if file.endswith(".md"):
                    file_path = root_path / file
                    if not should_exclude(file_path, exclude_paths):
                        has_md = True
                        rel_path = file_path.relative_to(base_path).with_suffix(".html")
                        project_files.append({
                            "file_path": file_path,
                            "rel_path": str(rel_path),
                            "title": file_path.stem,
                            "parent": str(file_path.parent.relative_to(base_path)) if file_path.parent != base_path else None,
                            "project": project_name
                        })
            if has_md:
                current = root_path
                while current != base_path.parent and current != current.parent:
                    rel_folder = str(current.relative_to(base_path))
                    if rel_folder not in project_folders and rel_folder != ".":
                        project_folders.append(rel_folder)
                    current = current.parent

        # Construire la hiérarchie par projet
        hierarchy = {}
        for folder in sorted(project_folders):
            folder_path = Path(folder) / "index.html"
            hierarchy[str(folder_path)] = {
                "title": folder.split('/')[-1] if folder else project_name,
                "rel_path": str(folder_path),
                "target_path": str(base_path / folder),  # Chemin absolu basé sur base_path
                "sub_pages": [],
                "is_folder": True,
                "project": project_name
            }
        if any(not file["parent"] for file in project_files):
            hierarchy["index.html"] = {
                "title": project_name,
                "rel_path": "index.html",
                "target_path": str(base_path),  # Chemin absolu de la racine du projet
                "sub_pages": [],
                "is_folder": True,
                "project": project_name
            }

        for file in project_files:
            parent_key = str(Path(file["parent"] or "").joinpath("index.html")) if file["parent"] else "index.html"
            if file["rel_path"] != parent_key:
                hierarchy[parent_key]["sub_pages"].append({
                    "title": file["title"],
                    "rel_path": file["rel_path"],
                    "target_path": str(file["file_path"]),  # Chemin absolu du fichier
                    "is_folder": False,
                    "project": project_name
                })

        for page in hierarchy.values():
            page["sub_pages"].sort(key=lambda x: x["rel_path"])
        project_groups[project_name] = list(hierarchy.values())
        markdown_files.extend(project_files)

    all_pages = []
    for project_hierarchy in project_groups.values():
        all_pages.extend(project_hierarchy)
    return markdown_files, all_pages

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
    print(f"convert_md_to_html: current_page={current_page}, adjusted_pages={[p['rel_path'] for p in adjusted_pages]}")
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
    print(f"generate_folder_index: current_page={current_page}, adjusted_pages={[p['rel_path'] for p in adjusted_pages]}")
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
    
    try:
        template = JINJA_ENV.get_template(TEMPLATE)
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
        page = page.copy()
        page["ref_path"] = page["rel_path"]
        page["rel_path"] = get_relative_path(page["rel_path"], current_dir)
        page["sub_pages"] = [
            {**sub, 
              "ref_path": sub["rel_path"],
              "rel_path": get_relative_path(sub["rel_path"], current_dir), 
              "target_path": get_relative_path(sub["target_path"], base_path).replace(".md", ".html")
            }
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
    global OUTPUT_DIR
    if not directory_security_check(OUTPUT_DIR):
        print(f"Warning: OUTPUT_DIR '{OUTPUT_DIR}' is unsafe, resetting to 'docs'.")
        OUTPUT_DIR = Path("docs")
    
    clean_dir(OUTPUT_DIR)
    
    save_dir = OUTPUT_DIR
    if directory_security_check(SAVE_DIR) and SAVE_DIR != OUTPUT_DIR:
        clean_dir(SAVE_DIR)
        save_dir = SAVE_DIR
    
    for project in INCLUDE_PATHS:
        if not Path(project["path"]).exists():
            print(f"Error: Source path '{project['path']}' does not exist.")
            return
    
    md_files, pages_hierarchy = scan_markdown_files(INCLUDE_PATHS, EXCLUDE_PATHS)
    if not md_files:
        print('Sources folders empty.')
        return
    
    print("\nCopy MD files.")
    for md_file in md_files:
        base_path = next(bp["path"] for bp in INCLUDE_PATHS if md_file["file_path"].is_relative_to(bp["path"]))
        save_md_file(md_file["file_path"], save_dir, base_path)
    
    print("\nWrite HTML files.")
    for md_file in md_files:
        base_path = next(bp["path"] for bp in INCLUDE_PATHS if md_file["file_path"].is_relative_to(bp["path"]))
        convert_md_to_html(md_file, OUTPUT_DIR, pages_hierarchy, base_path)
    
    print("\nGenerate folder indexes.")
    for page in pages_hierarchy:
        try:
            base_path = next(bp["path"] for bp in INCLUDE_PATHS if Path(page["target_path"]).is_relative_to(bp["path"]))
        except StopIteration:
            # Fallback si aucun projet ne correspond (cas rare)
            base_path = Path(INCLUDE_PATHS[0]["path"])
            print(f"Warning: Could not determine base_path for {page['target_path']}, using {base_path}")
        folder_path = Path(page["rel_path"]).parent
        generate_folder_index(folder_path, OUTPUT_DIR, pages_hierarchy, page["sub_pages"], base_path)
    
    print("\nCopy the static assets folder.")
    if os.path.exists(f"{save_dir}/static"):
        shutil.rmtree(f"{save_dir}/static")
    shutil.copytree("./static", f"{save_dir}/static")

# Main function
if __name__ == "__main__":
    generate_site()
