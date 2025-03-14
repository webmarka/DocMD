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
<html lang="{{ lang }}" data-bs-theme="{{ theme_mode }}>
<head>
    <meta charset="UTF-8">
    <title>{{ title }} - DocMD</title>
    <!-- Favicons -->
    <link rel="apple-touch-icon" sizes="57x57" href="{{ assets_path }}/img/favicon-57x57.png" type="image/png" />
    <link rel="apple-touch-icon" sizes="60x60" href="{{ assets_path }}/img/favicon-60x60.png" type="image/png" />
    <link rel="apple-touch-icon" sizes="72x72" href="{{ assets_path }}/img/favicon-72x72.png" type="image/png" />
    <link rel="apple-touch-icon" sizes="114x114" href="{{ assets_path }}/img/favicon-114x114.png" type="image/png" />
    <link rel="apple-touch-icon" sizes="120x120" href="{{ assets_path }}/img/favicon-120x120.png" type="image/png" />
    <link rel="apple-touch-icon" sizes="144x144" href="{{ assets_path }}/img/favicon-144x144.png" type="image/png" />
    <link rel="apple-touch-icon" sizes="152x152" href="{{ assets_path }}/img/favicon-152x152.png" type="image/png" />
    <link rel="apple-touch-icon" sizes="180x180" href="{{ assets_path }}/img/favicon-180x180.png" type="image/png" />
    <link rel="icon" sizes="16x16" href="{{ assets_path }}/img/favicon-16x16.png" type="image/png" />
    <link rel="icon" sizes="32x32" href="{{ assets_path }}/img/favicon-32x32.png" type="image/png" />
    <link rel="icon" sizes="96x96" href="{{ assets_path }}/img/favicon-96x96.png" type="image/png" />
    <link rel="icon" sizes="192x192" href="{{ assets_path }}/img/favicon-192x192.png" type="image/png" />
    <link rel="icon" sizes="512x512" href="{{ assets_path }}/img/favicon-512x512.png" type="image/png" />
    <!--<link rel="icon" href="{{ assets_path }}/img/favicon.svg"  type="image/svg+xml" />-->
    <link rel="manifest" href="{{ assets_path }}/img/manifest.json" />
    <meta name="theme-color" content="#FFFFFF" />
    <meta name="msapplication-TileColor" content="#FFFFFF" />
    <meta name="msapplication-TileImage" content="{{ assets_path }}/img/favicon-512x512.png" />
    <!-- Styles -->
    <link rel="stylesheet" href="{{ bs_css_path }}">
    <link rel="stylesheet" href="{{ css_path }}">
    <link rel="stylesheet" href="{{ theme_css_path }}">
    <style>
    </style>
</head>
<body>
  <main>
    <div class="sidebar">
        <h4 class="px-3">{{ nav_title }}</h4>
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
  </main>
  <footer>
    <small>{{ footer }}</small>
  </footer>
    <script type="text/javascript">
    </script>
    <script type="text/javascript" src="{{ assets_path }}/js/script.js?v={{ app_version }}"></script>
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
                css_path = docmd.get_relative_path(docmd.CSS_PATH, self.test_dir)
                theme_css_path = docmd.get_theme_css_path(self.test_dir)
                assets_path = docmd.get_relative_path(docmd.ASSETS_PATH, self.test_dir)
                bs_css_path = docmd.get_relative_path(docmd.BS_CSS_PATH, self.test_dir)
                bs_css_path = docmd.BS_CSS_URL if docmd.USE_EXTERNAL_ASSETS != 'False' else bs_css_path
                
                # Instead of checking file existence, verify the render call
                mock_template.render.assert_called_once_with(
                    title="doc",
                    content="<h1>Doc in module1</h1>",
                    lang=docmd.LANG,
                    pages=[],
                    current_page="module1/doc.html",
                    css_path=css_path,
                    theme_css_path=theme_css_path,
                    theme_mode=docmd.THEME_MODE,
                    assets_path=assets_path,
                    footer=docmd.FOOTER,
                    app_name=docmd.APP_NAME,
                    nav_title=docmd.NAV_TITLE,
                    bs_css_path=bs_css_path,
                    app_version=docmd.APP_VERSION
                )

if __name__ == "__main__":
    unittest.main()
