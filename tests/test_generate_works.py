"""Protect research attribution, CSV coverage, and reproducible publication."""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/content/generate_works.py"
spec = importlib.util.spec_from_file_location("generate_works", SCRIPT)
works = importlib.util.module_from_spec(spec)
spec.loader.exec_module(works)


class WorkPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "maintenance").mkdir()
        (self.root / "maintenance/scene.csv").write_text(
            "Title,Present,Maker\nOriginal title,,\nAlternate filename,,\n"
        )
        self.data = {
            "researched_on": "2026-11-11",
            "source_csv": "maintenance/scene.csv",
            "items": [
                {
                    "id": "work-001",
                    "file": "Example.md",
                    "title": "Example",
                    "status": "official",
                    "source_rows": [1, 2],
                    "sources": [
                        {"label": "Official catalog", "url": "https://example.org/work"}
                    ],
                    "fields": [{"key": "release", "value": "2020-03", "source": 0}],
                    "notes": {"zh": "月份精度。", "en": "Month precision."},
                }
            ],
        }
        self.save()

    def save(self):
        (self.root / "maintenance/works.yaml").write_text(yaml.safe_dump(self.data))

    def command(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_originals_stay_in_research_and_pages_preserve_source_precision(self):
        data, rows = works.load_research(self.root)
        self.assertEqual(data["items"][0]["source_rows"], [1, 2])
        self.assertEqual(rows[0]["Title"], "Original title")
        self.assertEqual(rows[1]["Title"], "Alternate filename")
        pages = works.render(self.root, data, rows)
        for lang in ("zh", "en"):
            page = pages[self.root / "docs" / lang / "作品/单部/Example.md"]
            self.assertNotIn("Original title", page)
            self.assertNotIn("Alternate filename", page)
            self.assertIn("2020-03", page)
            self.assertNotIn("2020-03-01", page)
            self.assertIn("https://example.org/work", page)

    def test_missing_information_does_not_create_placeholder_sections(self):
        item = self.data["items"][0]
        item.update(status="unresolved", fields=[], sources=[])
        self.save()
        data, rows = works.load_research(self.root)
        pages = works.render(self.root, data, rows)
        for lang in ("zh", "en"):
            page = pages[self.root / "docs" / lang / "作品/单部/Example.md"]
            self.assertIn("# Example", page)
            self.assertNotIn("## ", page)
            self.assertNotIn("unresolved", page)
            self.assertNotIn("月份精度", page)
            self.assertNotIn("Month precision", page)

    def test_synopsis_requires_a_source_and_renders_in_both_languages(self):
        item = self.data["items"][0]
        item["synopsis"] = {
            "zh": "两位老友重逢。",
            "en": "Two old friends reunite.",
            "source": 0,
        }
        self.save()
        data, rows = works.load_research(self.root)
        pages = works.render(self.root, data, rows)
        self.assertIn(
            "## 剧情简介\n\n两位老友重逢。",
            pages[self.root / "docs/zh/作品/单部/Example.md"],
        )
        self.assertIn(
            "## Synopsis\n\nTwo old friends reunite.",
            pages[self.root / "docs/en/作品/单部/Example.md"],
        )
        item["synopsis"]["source"] = 1
        self.save()
        with self.assertRaisesRegex(ValueError, "synopsis must have"):
            works.load_research(self.root)

    def test_duplicate_or_missing_csv_mapping_is_rejected(self):
        for mapping in ([1], [1, 1, 2], [1, 3]):
            with self.subTest(mapping=mapping):
                self.data["items"][0]["source_rows"] = mapping
                self.save()
                with self.assertRaisesRegex(ValueError, "every CSV row"):
                    works.load_research(self.root)

    def test_unsupported_metadata_cannot_be_published(self):
        item = self.data["items"][0]
        item["fields"][0]["source"] = 1
        self.save()
        with self.assertRaisesRegex(ValueError, "cite an existing source"):
            works.load_research(self.root)
        item["fields"][0]["source"] = 0
        item["status"] = "unresolved"
        self.save()
        with self.assertRaisesRegex(ValueError, "cannot assert researched metadata"):
            works.load_research(self.root)

    def test_check_detects_drift_and_unmapped_pages(self):
        self.assertEqual(self.command().returncode, 0)
        self.assertEqual(self.command("--check").returncode, 0)
        page = self.root / "docs/en/作品/单部/Example.md"
        original = page.read_text()
        page.write_text(original + "unsupported addition\n")
        self.assertNotEqual(self.command("--check").returncode, 0)
        page.write_text(original)
        (page.parent / "Orphan.md").write_text("# Unmapped\n")
        result = self.command("--check")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unmapped", result.stdout)


if __name__ == "__main__":
    unittest.main()
