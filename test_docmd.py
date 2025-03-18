import os
import shutil
from pathlib import Path
import unittest
from unittest.mock import patch, mock_open
import sys
from jinja2 import Environment, FileSystemLoader
import html

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
    
    return [
        {"path": str(src1), "name": "Source1", "excludes": []},
        {"path": str(src2), "name": "Source2", "excludes": []}
    ]

def check_generated_files(output_dir):
    """Check the presence and validity of generated files."""
    output_dir = Path(output_dir)
    expected_files = [
        "index.html",
        "Source1/index.html",
        "readme.html",
        "module1/index.html",
        "module1/doc.html",
        "module2/index.html",
        "module2/Sujet/index.html",
        "module2/Sujet/Sous-sujet/index.html",
        "module2/Sujet/Sous-sujet/deep.html",
        "module4/index.html",
        "module4/Special d.html",
        "Source2/index.html",
        "extra.html"
    ]
    missing = [f for f in expected_files if not (output_dir / f).exists()]
    return missing

class TestDocMD(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_temp")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.output_dir = self.test_dir / "docs"
        self.include_paths = create_test_tree(self.test_dir)
        docmd.INCLUDE_PATHS = self.include_paths
        docmd.OUTPUT_DIR = self.output_dir
        docmd.SAVE_DIR = self.output_dir
        docmd.TEMPLATE_DIR = str(self.test_dir / "../tests/templates")
        docmd.TEMPLATE = "test_default.html"  # Utilise le template synchronisé
        env = Environment(loader=FileSystemLoader(docmd.TEMPLATE_DIR))
        docmd.JINJA_ENV = env

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_generate_site(self):
        """Test the full site generation."""
        docmd.generate_site()
        missing_files = check_generated_files(self.output_dir)
        self.assertEqual(len(missing_files), 0, f"Missing files: {missing_files}")
        
        with open(self.output_dir / "index.html", "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn('<strong>Source1</strong>', content)
            self.assertIn('href="module1/index.html"', content)
            self.assertIn('href="module4/Special%20d.html"', content)
            self.assertIn('href="extra.html"', content)

        with open(self.output_dir / "module1/index.html", "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn('href="../index.html"', content)
            self.assertIn('href="doc.html"', content)
            self.assertIn('href="../module4/Special%20d.html"', content)

        with open(self.output_dir / "module2/Sujet/Sous-sujet/index.html", "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn('href="../../../index.html"', content)
            self.assertIn('href="deep.html"', content)
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
            with patch('docmd.JINJA_ENV') as mock_jinja_env:
                mock_template = mock_jinja_env.get_template.return_value
                mock_template.render.return_value = "<html>Test</html>"
                docmd.convert_md_to_html(md_file_info, self.output_dir, [], self.include_paths[0]["path"])
                css_path = docmd.get_relative_path(docmd.CSS_PATH, "module1")
                theme_css_path = docmd.get_theme_css_path("module1")
                assets_path = docmd.get_relative_path(docmd.ASSETS_PATH, "module1")
                bs_css_path = docmd.get_relative_path(docmd.BS_CSS_PATH, "module1")
                bs_css_path = docmd.BS_CSS_URL if docmd.USE_EXTERNAL_ASSETS != 'False' else bs_css_path
                current_page = "module1/doc.html"
                page_id = docmd.format_alias(current_page, "_")
                body_class = docmd.get_body_class(current_page)
                file_hash = None
                file_size = os.path.getsize(md_file_info["file_path"])
                
                mock_template.render.assert_called_once_with(
                    title="doc",
                    content="<h1>Doc in module1</h1>",
                    lang=docmd.LANG,
                    pages=[],
                    current_page=current_page,
                    page_id=page_id,
                    body_class=body_class,
                    css_path=css_path,
                    theme_css_path=theme_css_path,
                    theme_mode=docmd.THEME_MODE,
                    assets_path=assets_path,
                    footer=docmd.FOOTER,
                    date_tag_human=docmd.DATE_TAG_HUMAN,
                    file_hash=file_hash,
                    file_size=file_size,
                    bs_css_path=bs_css_path,
                    nav_title=docmd.NAV_TITLE,
                    app_name=docmd.APP_NAME,
                    app_author=docmd.APP_AUTHOR,
                    app_version=docmd.APP_VERSION,
                    app_description=docmd.APP_DESCRIPTION
                )

    def test_navigation_active_state(self):
        docmd.generate_site()
        # Test root page (readme.html from src1)
        with open(self.output_dir / "readme.html", "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn('class="nav-link active current" href="readme.html"', content)
            self.assertIn('class="nav-link active" href="Source1/index.html"', content)
            self.assertNotIn('class="nav-link current" href="Source1/index.html"', content)

        # Test nested page (module1/doc.html from src1)
        with open(self.output_dir / "module1/doc.html", "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn('class="nav-link active current" href="doc.html"', content)
            self.assertIn('class="nav-link active" href="index.html"', content)  # module1/index.html
            # On ne s’attend PAS à ce que Source1/index.html soit active
            self.assertNotIn('class="nav-link active" href="../Source1/index.html"', content)

        # Test deep nested page (module2/Sujet/Sous-sujet/deep.html from src1)
        with open(self.output_dir / "module2/Sujet/Sous-sujet/deep.html", "r", encoding="utf-8") as f:
            content = f.read()
            self.assertNotIn('class="nav-link active" href="../../../Source1/index.html"', content)  # Pas active
            #self.assertIn('class="nav-link active" href="../../index.html"', content)  # module2
            #self.assertIn('class="nav-link active" href="../index.html"', content)    # Sujet
            self.assertIn('class="nav-link active" href="index.html"', content)       # Sous-sujet
            self.assertIn('class="nav-link active current" href="deep.html"', content)

        # Test page from src2 (extra.html)
        with open(self.output_dir / "extra.html", "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn('class="nav-link active current" href="extra.html"', content)
            self.assertIn('class="nav-link active" href="Source2/index.html"', content)

if __name__ == "__main__":
    unittest.main()
