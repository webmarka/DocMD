import os
import shutil
from pathlib import Path
import unittest
from unittest.mock import patch, mock_open
import sys

sys.path.append(os.path.dirname(__file__))
import docmd

def create_test_tree(base_dir):
    """Create a test directory structure with Markdown files."""
    base_dir = Path(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    
    src1 = base_dir / "src1"
    src1.mkdir(parents=True, exist_ok=True)
    (src1 / "readme.md").write_text("# README at root")
    (src1 / "module1").mkdir(parents=True, exist_ok=True)
    (src1 / "module1" / "doc.md").write_text("# Doc in module1")
    (src1 / "module2").mkdir(parents=True, exist_ok=True)
    (src1 / "module2" / "Sujet").mkdir(parents=True, exist_ok=True)
    (src1 / "module2" / "Sujet" / "Sous-sujet").mkdir(parents=True, exist_ok=True)
    (src1 / "module2" / "Sujet" / "Sous-sujet" / "deep.md").write_text("# Deep doc")
    (src1 / "module3").mkdir(parents=True, exist_ok=True)  # Empty folder
    (src1 / "module4").mkdir(parents=True, exist_ok=True)
    (src1 / "module4" / "Special d.md").write_text("# File with spaces")
    
    src2 = base_dir / "src2"
    src2.mkdir(parents=True, exist_ok=True)
    (src2 / "extra.md").write_text("# Extra doc")
    
    (base_dir / "templates").mkdir(parents=True, exist_ok=True)
    (base_dir / "templates" / "default.html").write_text("""
<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
    <meta charset="UTF-8">
    <title>{{ title }} - DocMD</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <style>
        .sidebar { height: 100vh; position: fixed; top: 0; left: 0; width: 250px; padding-top: 20px; background-color: #f8f9fa; border-right: 1px solid #dee2e6; overflow-y: auto; }
        .content { margin-left: 270px; padding: 20px; }
        .nav-nested { margin-left: 20px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h4 class="px-3">Documentation</h4>
        <ul class="nav flex-column">
            {% for page in pages %}
                <li class="nav-item">
                    <a class="nav-link{% if page.rel_path == current_page %} active{% endif %}" href="{{ page.rel_path | urlencode }}">
                        {% if page.is_folder %}<strong>{{ page.title }}</strong>{% else %}{{ page.title }}{% endif %}
                    </a>
                    {% if page.sub_pages %}
                        <ul class="nav flex-column nav-nested">
                            {% for sub_page in page.sub_pages %}
                                <li class="nav-item">
                                    <a class="nav-link{% if sub_page.rel_path == current_page %} active{% endif %}" href="{{ sub_page.rel_path | urlencode }}">
                                        {% if sub_page.is_folder %}<strong>{{ sub_page.title }}</strong>{% else %}{{ sub_page.title }}{% endif %}
                                    </a>
                                </li>
                            {% endfor %}
                        </ul>
                    {% endif %}
                </li>
            {% endfor %}
        </ul>
    </div>
    <div class="content">
        <h1>{{ title }}</h1>
        {{ content | safe }}
    </div>
</body>
</html>
    """)
    
    return [src1, src2]

def check_generated_files(output_dir):
    """Check the presence and validity of generated files."""
    output_dir = Path(output_dir)
    expected_files = [
        "index.html",
        "module1/index.html",
        "module1/doc.html",
        "module2/Sujet/Sous-sujet/index.html",
        "module2/Sujet/Sous-sujet/deep.html",
        "module2/Sujet/index.html",
        "module2/index.html",
        "module4/Special d.html",  # Unencoded on disk
        "module4/index.html",
        "extra.html"
    ]
    missing = []
    for file in expected_files:
        if not (output_dir / file).exists():
            missing.append(file)
    return missing

class TestDocMD(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_temp")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)  # Ensure clean slate
        self.output_dir = self.test_dir / "docs"
        self.include_paths = create_test_tree(self.test_dir)
        docmd.INCLUDE_PATHS = self.include_paths
        docmd.OUTPUT_DIR = self.output_dir
        docmd.SAVE_DIR = self.output_dir
        docmd.TEMPLATE = "default.html"

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_generate_site(self):
        """Test the full site generation."""
        docmd.generate_site()
        missing_files = check_generated_files(self.output_dir)
        self.assertEqual(len(missing_files), 0, f"Missing files: {missing_files}")
        
        # Check index.html (root level)
        with open(self.output_dir / "index.html", "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn('<strong>Home</strong>', content)
            self.assertIn('href="module1/index.html"', content)  # Root level
            self.assertIn('href="module4/Special%20d.html"', content)
            self.assertIn('href="extra.html"', content)

        # Check module1/index.html (1 level deep)
        with open(self.output_dir / "module1/index.html", "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn('href="../index.html"', content)  # Go up to root
            self.assertIn('href="doc.html"', content)  # Same level
            self.assertIn('href="../module4/Special%20d.html"', content)

        # Check module2/Sujet/Sous-sujet/index.html (3 levels deep)
        with open(self.output_dir / "module2/Sujet/Sous-sujet/index.html", "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn('href="../../../index.html"', content)  # Go up 3 levels
            self.assertIn('href="deep.html"', content)  # Same level
            self.assertIn('href="../../../module1/index.html"', content)

    def test_scan_markdown_files(self):
        """Test the scan_markdown_files function."""
        md_files, hierarchy = docmd.scan_markdown_files(self.include_paths, docmd.EXCLUDE_PATHS)
        
        expected_rel_paths = [
            "readme.html",
            "module1/doc.html",
            "module2/Sujet/Sous-sujet/deep.html",
            "module4/Special d.html",
            "extra.html"
        ]
        found_rel_paths = [f["rel_path"] for f in md_files]
        self.assertEqual(sorted(found_rel_paths), sorted(expected_rel_paths))
        
        hierarchy_paths = [p["rel_path"] for p in hierarchy]
        self.assertIn("index.html", hierarchy_paths)
        self.assertIn("module1/index.html", hierarchy_paths)
        self.assertNotIn("module3/index.html", hierarchy_paths)

    def test_convert_md_to_html(self):
        """Test the conversion of a Markdown file to HTML."""
        md_file_info = {
            "file_path": self.test_dir / "src1/module1/doc.md",
            "rel_path": "module1/doc.html",
            "title": "doc",
            "parent": "module1"
        }
        with patch('builtins.open', mock_open(read_data="# Doc in module1")):
            with patch('jinja2.Environment') as mock_jinja_env:
                mock_template = mock_jinja_env.return_value.get_template.return_value
                mock_template.render.return_value = "<html>Test</html>"
                docmd.convert_md_to_html(md_file_info, self.output_dir, [], self.include_paths[0])
                # Instead of checking file existence, verify the render call
                mock_template.render.assert_called_once_with(
                    title="doc",
                    content="<h1>Doc in module1</h1>",
                    lang=docmd.LANG,
                    pages=[],
                    current_page="module1/doc.html"
                )

if __name__ == "__main__":
    unittest.main()
