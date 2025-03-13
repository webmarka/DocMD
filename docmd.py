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

# Environment.
debug = False
load_dotenv()
ENV = os.environ.get("ENV", "prod")
if ENV == "prod":
    load_dotenv(".env.prod")
elif ENV == "dev":
    load_dotenv(".env.dev")
    debug = True

# Takes a comma separated string and turn it into a paths array.
def get_paths(string):
    PATHS = []
    for base_path in get_config_array(string):
        PATHS.append(Path(base_path))
    return PATHS

# Takes a comma separated string and turn it into a list.
def get_config_array(string):
    return list(map(str.strip, string.split(',')))

# Configuration.
LANG = os.environ.get("LANG", "fr")
INCLUDE_PATHS = get_paths(os.environ.get("INCLUDE_PATHS", "src"))
EXCLUDE_PATHS = get_paths(os.environ.get("EXCLUDE_PATHS", ".git,.hg"))
SAVE_DIR = Path(os.environ.get("SAVE_DIR", "docs"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "docs"))
TEMPLATE = os.environ.get("TEMPLATE", "default.html")
DATE_TAG = datetime.now().strftime('%Y%m%d%H%M%S')

# Paths to exclude.
def should_exclude(file_path, exclude_paths):
    """Checks if a file or folder should be excluded."""
    return any(excluded in file_path.parents or file_path == excluded for excluded in exclude_paths)

# Scan markdown files.
def scan_markdown_files(include_paths, exclude_paths):
    """Scans folders for Markdown files and returns their metadata."""
    markdown_files = []
    for base_path in include_paths:
        for root, _, files in os.walk(base_path):
            root_path = Path(root)
            for file in files:
                if file.endswith(".md"):
                    file_path = root_path / file
                    if not should_exclude(file_path, exclude_paths):
                        # Chemin relatif par rapport à OUTPUT_DIR
                        rel_path = file_path.relative_to(base_path).with_suffix(".html")
                        markdown_files.append({
                            "file_path": file_path,
                            "rel_path": str(rel_path),
                            "title": file_path.stem,
                            "parent": str(file_path.parent.relative_to(base_path)) if file_path.parent != base_path else None
                        })
    # Organiser en hiérarchie
    hierarchy = {}
    for file in markdown_files:
        if file["parent"] is None:
            hierarchy[file["rel_path"]] = {"title": file["title"], "rel_path": file["rel_path"], "sub_pages": []}
        else:
            parent_key = str(Path(file["parent"]).with_suffix(".html"))
            if parent_key not in hierarchy:
                hierarchy[parent_key] = {"title": file["parent"].split('/')[-1], "rel_path": parent_key, "sub_pages": []}
            hierarchy[parent_key]["sub_pages"].append({"title": file["title"], "rel_path": file["rel_path"]})
    return markdown_files, list(hierarchy.values())

# Save Markdown file.
def save_md_file(md_file, save_dir):
    """Save Markdown files to a folder."""
    # Relative path and output folder
    relative_path = md_file.parent.relative_to(md_file.parents[-2])
    save_subdir = save_dir / relative_path
    save_subdir.mkdir(parents=True, exist_ok=True)
    # HTML file name based on Markdown file.
    save_file = save_subdir / (md_file.stem + ".md")
    # Copy the MD file.
    shutil.copyfile(md_file, save_file)
    print(f"Saved: {save_file}")

# Convert Markdown to HTML static tree.
def convert_md_to_html(md_file_info, output_dir, all_pages):
    """Converts a Markdown file to HTML and places it in the tree."""
    md_file = md_file_info["file_path"]
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()
    
    # Markdown -> HTML conversion.
    html_content = markdown.markdown(md_content)
    
    # Relative path and output folder
    relative_path = md_file.parent.relative_to(md_file.parents[-2])
    output_subdir = output_dir / relative_path
    output_subdir.mkdir(parents=True, exist_ok=True)
    output_file = output_subdir / (md_file.stem + ".html")
    
    # Render template.
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
    try:
        template = env.get_template(TEMPLATE)
    except jinja2.TemplateNotFound:
        print(f"Erreur : Template '{TEMPLATE}' introuvable dans 'templates/'")
        return
    html_output = template.render(
        title=md_file_info["title"],
        content=html_content,
        lang=LANG,
        pages=all_pages,
        current_page=md_file_info["rel_path"]
    )
    
    # Writing the HTML file.
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f"Generated: {output_file}")

# Generate index page.
def generate_index(output_dir, all_pages):
    """Generate an index.html with a summary."""
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
    try:
        template = env.get_template(TEMPLATE)
    except jinja2.TemplateNotFound:
        print(f"Erreur : Template '{TEMPLATE}' introuvable dans 'templates/'")
        return
    content = "<h2>Tableau des matières</h2><ul>"
    for page in all_pages:
        content += f"<li><a href='{page['rel_path']}'>{page['title']}</a></li>"
        for sub_page in page.get("sub_pages", []):
            content += f"<li style='margin-left: 20px;'><a href='{sub_page['rel_path']}'>{sub_page['title']}</a></li>"
    content += "</ul>"
    html_output = template.render(
        title="Accueil",
        content=content,
        lang=LANG,
        pages=all_pages,
        current_page="index.html"
    )
    with open(output_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f"Generated: {output_dir / 'index.html'}")

# Generate site.
def generate_site():
    global OUTPUT_DIR, SAVE_DIR
    """Generate the static site."""
    # Validate path.
    if not directory_security_check(OUTPUT_DIR):
        OUTPUT_DIR = Path("docs")
    # Cleaning save and output folders.
    clean_dir(SAVE_DIR)
    clean_dir(OUTPUT_DIR)
    # Scan and convert.
    save_dir = OUTPUT_DIR
    # Use a custom save folder if not empty.
    if directory_security_check(SAVE_DIR):
        save_dir = SAVE_DIR
    # List all files recursively.
    md_files, pages_hierarchy = scan_markdown_files(INCLUDE_PATHS, EXCLUDE_PATHS)
    if not md_files:
        print('Sources folders empty.')
        return
    # Copy MD files.
    print("\nCopy MD files.")
    for md_file in md_files:
        save_md_file(md_file["file_path"], save_dir)
    # Write HTML files.
    print("\nWrite HTML files.")
    for md_file in md_files:
        convert_md_to_html(md_file, OUTPUT_DIR, pages_hierarchy)
    # Generate index.
    generate_index(OUTPUT_DIR, pages_hierarchy)

# Directory security check.
def directory_security_check(DIRECTORY):
    status = False
    if (
        DIRECTORY != Path("")          # Pas vide
        and DIRECTORY != Path(".")     # Pas le dossier courant
        and DIRECTORY != Path("..")    # Pas le dossier parent
        and not DIRECTORY.is_absolute()  # Pas un chemin absolu
        and DIRECTORY != Path("/")     # Pas la racine
        and DIRECTORY != Path("./")    # Pas "./"
    ):
        status = True
    return status

# Cleaning a folder.
def clean_dir(DIRECTORY):
    # Security check.
    security_check = directory_security_check(DIRECTORY)
    if not security_check:
        return False
    # Cleaning the DIRECTORY folder.
    if DIRECTORY.exists():
        # Backup folder.
        print("Backup the old site.")
        shutil.copytree(DIRECTORY, f"{DIRECTORY}.{DATE_TAG}.bak", dirs_exist_ok=True)
        # Clean folder.
        print("Remove old generated files.")
        shutil.rmtree(DIRECTORY)
    else:
        DIRECTORY.mkdir(parents=True)

# Main function.
if __name__ == "__main__":
    generate_site()
