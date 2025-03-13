# DocMD
# Description: Generate a static documentation website from Markdown files in a project's source-code.
# Version: 0.0.1
# Authors: webmarka
# URL: https://gitlab.com/webmarka/docmd

# Imports.
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

# Configuration
LANG = os.environ.get("LANG", "fr")
INCLUDE_PATHS = get_paths(os.environ.get("INCLUDE_PATHS", "src"))
EXCLUDE_PATHS = get_paths(os.environ.get("EXCLUDE_PATHS", ".git,.hg"))
SAVE_DIR = Path(os.environ.get("SAVE_DIR", "docs"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "docs"))
TEMPLATE = os.environ.get("TEMPLATE", "default.html")
DATE_TAG = datetime.now().strftime('%Y%m%d%H%M%S')

# Check if a file path should be excluded
def should_exclude(file_path, exclude_paths):
    """Check if a file or folder should be excluded."""
    return any(excluded in file_path.parents or file_path == excluded for excluded in exclude_paths)

# Scan for Markdown files and build hierarchy
def scan_markdown_files(include_paths, exclude_paths):
    """Scan folders for Markdown files and return their metadata and folder hierarchy."""
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
                            "rel_path": str(rel_path),  # Relative to docs/ root
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
            "rel_path": str(folder_path),  # Relative to docs/ root
            "sub_pages": [],
            "is_folder": True
        }
    if any(not file["parent"] for file in markdown_files):
        hierarchy["index.html"] = {
            "title": "Home",
            "rel_path": "index.html",
            "sub_pages": [],
            "is_folder": True
        }
    
    for file in markdown_files:
        parent_key = str(Path(file["parent"] or "").joinpath("index.html")) if file["parent"] else "index.html"
        if file["rel_path"] != parent_key:
            hierarchy[parent_key]["sub_pages"].append({
                "title": file["title"],
                "rel_path": file["rel_path"],
                "is_folder": False
            })
    
    # Sort sub-pages for consistent order
    for page in hierarchy.values():
        page["sub_pages"].sort(key=lambda x: x["rel_path"])
    
    return markdown_files, list(hierarchy.values())

# Save a Markdown file to the output directory
def save_md_file(md_file, save_dir, base_path):
    """Save Markdown files to a folder."""
    relative_path = md_file.relative_to(base_path)
    save_subdir = save_dir / relative_path.parent
    save_subdir.mkdir(parents=True, exist_ok=True)
    save_file = save_subdir / md_file.name
    shutil.copyfile(md_file, save_file)
    print(f"Saved: {save_file}")

# Dans docmd.py, modifier ces fonctions :

import os
from pathlib import Path

# Convert Markdown file to HTML
def convert_md_to_html(md_file_info, output_dir, all_pages, base_path):
    """Convert a Markdown file to HTML and place it in the output tree."""
    md_file = md_file_info["file_path"]
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()
    
    html_content = markdown.markdown(md_content)
    relative_path = md_file.relative_to(base_path)
    output_subdir = output_dir / relative_path.parent
    output_subdir.mkdir(parents=True, exist_ok=True)
    output_file = output_subdir / (md_file.stem + ".html")
    
    # Calculate relative paths for navigation
    current_page = md_file_info["rel_path"]
    current_dir = os.path.dirname(current_page) or "."
    adjusted_pages = []
    for page in all_pages:
        target_path = page["rel_path"]
        rel_path = os.path.relpath(target_path, current_dir).replace("\\", "/")  # Normalize to forward slashes
        adjusted_page = page.copy()
        adjusted_page["rel_path"] = rel_path
        adjusted_page["sub_pages"] = [
            {
                **sub,
                "rel_path": os.path.relpath(sub["rel_path"], current_dir).replace("\\", "/")
            }
            for sub in page["sub_pages"]
        ]
        adjusted_pages.append(adjusted_page)
    
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
    try:
        template = env.get_template(TEMPLATE)
    except jinja2.TemplateNotFound:
        print(f"Error: Template '{TEMPLATE}' not found in 'templates/'")
        return
    html_output = template.render(
        title=md_file_info["title"],
        content=html_content,
        lang=LANG,
        pages=adjusted_pages,
        current_page=current_page
    )
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f"Generated: {output_file}")

# Generate folder index page
def generate_folder_index(folder_path, output_dir, all_pages, sub_pages):
    """Generate an index.html for a folder."""
    output_file = output_dir / folder_path / "index.html"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Calculate relative paths for navigation
    current_page = str(folder_path / "index.html" if folder_path.name else "index.html")
    current_dir = os.path.dirname(current_page) or "."
    adjusted_pages = []
    for page in all_pages:
        target_path = page["rel_path"]
        rel_path = os.path.relpath(target_path, current_dir).replace("\\", "/")
        adjusted_page = page.copy()
        adjusted_page["rel_path"] = rel_path
        adjusted_page["sub_pages"] = [
            {
                **sub,
                "rel_path": os.path.relpath(sub["rel_path"], current_dir).replace("\\", "/")
            }
            for sub in page["sub_pages"]
        ]
        adjusted_pages.append(adjusted_page)
    
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
    try:
        template = env.get_template(TEMPLATE)
    except jinja2.TemplateNotFound:
        print(f"Error: Template '{TEMPLATE}' not found in 'templates/'")
        return
    content = f"<h2>{folder_path.name if folder_path.name else 'Home'}</h2><ul>"
    for sub_page in sub_pages:
        content += f"<li><a href='{quote(sub_page['rel_path'])}'>{sub_page['title']}</a></li>"
    content += "</ul>"
    html_output = template.render(
        title=folder_path.name if folder_path.name else "Home",
        content=content,
        lang=LANG,
        pages=adjusted_pages,
        current_page=current_page
    )
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f"Generated: {output_file}")

# Main site generation function
def generate_site():
    global OUTPUT_DIR, SAVE_DIR
    """Generate the static site."""
    if not directory_security_check(OUTPUT_DIR):
        OUTPUT_DIR = Path("docs")
    clean_dir(SAVE_DIR)
    clean_dir(OUTPUT_DIR)
    save_dir = OUTPUT_DIR
    if directory_security_check(SAVE_DIR):
        save_dir = SAVE_DIR
    
    # Check if INCLUDE_PATHS exist
    for path in INCLUDE_PATHS:
        if not path.exists():
            print(f"Error: Source path '{path}' does not exist.")
            return
    
    md_files, pages_hierarchy = scan_markdown_files(INCLUDE_PATHS, EXCLUDE_PATHS)
    if not md_files:
        print('Sources folders empty.')
        return
    
    print("\nCopy MD files.")
    for md_file in md_files:
        base_path = next(bp for bp in INCLUDE_PATHS if md_file["file_path"].is_relative_to(bp))
        save_md_file(md_file["file_path"], save_dir, base_path)
    
    print("\nWrite HTML files.")
    for md_file in md_files:
        base_path = next(bp for bp in INCLUDE_PATHS if md_file["file_path"].is_relative_to(bp))
        convert_md_to_html(md_file, OUTPUT_DIR, pages_hierarchy, base_path)
    
    print("\nGenerate folder indexes.")
    for page in pages_hierarchy:
        folder_path = Path(page["rel_path"]).parent
        generate_folder_index(folder_path, OUTPUT_DIR, pages_hierarchy, page["sub_pages"])

# Security check for directories
def directory_security_check(directory):
    status = False
    if (
        directory != Path("")          # Not empty
        and directory != Path(".")     # Not current dir
        and directory != Path("..")    # Not parent dir
        and not directory.is_absolute()  # Not absolute path
        and directory != Path("/")     # Not root
        and directory != Path("./")    # Not "./"
    ):
        status = True
    return status

# Clean a directory with backup
def clean_dir(directory):
    """Clean a directory with a backup."""
    security_check = directory_security_check(directory)
    if not security_check or str(directory) in [".", ".."]:
        print(f"Error: Attempt to clean invalid directory '{directory}' skipped.")
        return False
    if directory.exists():
        print("Backup the old site.")
        shutil.copytree(directory, f"{directory}.{DATE_TAG}.bak", dirs_exist_ok=True)
        print("Remove old generated files.")
        shutil.rmtree(directory)
    else:
        directory.mkdir(parents=True)
    return True

# Main function.
if __name__ == "__main__":
    generate_site()
