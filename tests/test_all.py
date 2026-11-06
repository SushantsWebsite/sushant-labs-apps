import importlib.util
import json
import random
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(rel_path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PomodoroLogic(unittest.TestCase):
    m = load("apps/pomodoro/logic.py", "pomodoro_logic")

    def test_format_time(self):
        self.assertEqual(self.m.format_time(1500), "25:00")
        self.assertEqual(self.m.format_time(65), "01:05")
        self.assertEqual(self.m.format_time(-5), "00:00")

    def test_phase_cycle(self):
        m = self.m
        self.assertEqual(m.next_phase(m.WORK, 1), m.SHORT)
        self.assertEqual(m.next_phase(m.WORK, 3), m.SHORT)
        self.assertEqual(m.next_phase(m.WORK, 4), m.LONG)
        self.assertEqual(m.next_phase(m.WORK, 8), m.LONG)
        self.assertEqual(m.next_phase(m.WORK, 0), m.SHORT)
        self.assertEqual(m.next_phase(m.SHORT, 1), m.WORK)
        self.assertEqual(m.next_phase(m.LONG, 4), m.WORK)


class PasswordLogic(unittest.TestCase):
    m = load("apps/password-gen/logic.py", "password_logic")

    def test_length_and_classes(self):
        for _ in range(200):
            pw = self.m.generate(12)
            self.assertEqual(len(pw), 12)
            self.assertTrue(any(c in self.m.LOWER for c in pw))
            self.assertTrue(any(c in self.m.UPPER for c in pw))
            self.assertTrue(any(c in self.m.DIGITS for c in pw))
            self.assertTrue(any(c in self.m.SYMBOLS for c in pw))

    def test_only_digits(self):
        pw = self.m.generate(20, upper=False, lower=False, symbols=False)
        self.assertTrue(pw.isdigit())

    def test_errors(self):
        with self.assertRaises(ValueError):
            self.m.generate(10, False, False, False, False)
        with self.assertRaises(ValueError):
            self.m.generate(3)

    def test_ambiguous_filter(self):
        for _ in range(100):
            pw = self.m.generate(64, avoid_ambiguous=True)
            self.assertFalse(set(pw) & set(self.m.AMBIGUOUS))

    def test_strength(self):
        self.assertEqual(self.m.strength_label(30), "Weak")
        self.assertEqual(self.m.strength_label(50), "Fair")
        self.assertEqual(self.m.strength_label(70), "Strong")
        self.assertEqual(self.m.strength_label(100), "Excellent")
        self.assertEqual(self.m.entropy_bits(10, 1), 0.0)


class TypingLogic(unittest.TestCase):
    m = load("apps/typing-test/logic.py", "typing_logic")

    def test_make_text(self):
        text = self.m.make_text(60, random.Random(1))
        self.assertEqual(len(text.split()), 60)
        self.assertEqual(text, self.m.make_text(60, random.Random(1)))

    def test_scoring(self):
        self.assertEqual(self.m.correct_chars("abc", "abd"), 2)
        self.assertEqual(self.m.accuracy("abc", "abd"), 66.7)
        self.assertEqual(self.m.accuracy("", "abc"), 0.0)
        self.assertEqual(self.m.wpm(250, 60), 50.0)
        self.assertEqual(self.m.wpm(10, 0), 0.0)

    def test_score_storage(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "scores.json"
            self.assertEqual(self.m.load_scores(path), [])
            self.m.save_score(path, 40.0, 95.0)
            self.m.save_score(path, 55.5, 90.0)
            scores = self.m.load_scores(path)
            self.assertEqual(len(scores), 2)
            self.assertEqual(self.m.best_wpm(scores), 55.5)
            path.write_text("not json", encoding="utf-8")
            self.assertEqual(self.m.load_scores(path), [])
        self.assertIsNone(self.m.best_wpm([]))


class Catalog(unittest.TestCase):
    def test_catalog_is_valid(self):
        validate = load("tools/validate.py", "validate_tool")
        self.assertEqual(validate.check(), [])


class Storefront(unittest.TestCase):
    def test_site_builds(self):
        site = load("tools/build_site.py", "site_tool")
        apps = json.loads((ROOT / "apps.json").read_text(encoding="utf-8"))["apps"]
        apps[0] = dict(apps[0], status="live", version="1.2.3", name="Focus <Timer>")
        cfg = {
            "brand": "Test Labs", "tagline": "Tagline", "github_user": "tester", "repo": "demo",
            "contact_url": "https://example.com/hire", "sponsor_url": "https://github.com/sponsors/tester",
            "kofi_url": "", "store_url": "", "plausible_domain": "",
        }
        with tempfile.TemporaryDirectory() as tmp:
            files = site.build(apps, cfg, Path(tmp), ROOT)
            names = {f.name for f in files}
            self.assertTrue({"index.html", "pomodoro.html", "sitemap.xml", "llms.txt", "robots.txt"} <= names)
            page = (Path(tmp) / "apps" / "pomodoro.html").read_text(encoding="utf-8")
            self.assertIn("releases/download/pomodoro-v1.2.3/pomodoro-Windows.exe", page)
            self.assertIn("Focus &lt;Timer&gt;", page)
            self.assertNotIn("Focus <Timer>", page)
            self.assertIn("SoftwareApplication", page)
            self.assertIn("issues/new?template=custom-build.yml", page)
            self.assertNotIn("YOUR_", page)
            index = (Path(tmp) / "index.html").read_text(encoding="utf-8")
            self.assertIn("sponsors/tester", index)
            self.assertNotIn("buymeacoffee", index.lower())

    def test_placeholder_detection(self):
        site = load("tools/build_site.py", "site_tool2")
        self.assertEqual(site.placeholders({"a": "YOUR_X", "b": "ok", "c": ""}), ["a"])


if __name__ == "__main__":
    unittest.main()
