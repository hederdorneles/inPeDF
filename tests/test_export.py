"""Regression tests for headless, transactional batch export."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

import cairo

from inpedf import __version__
from inpedf.export import markdown_text, page_indices, publish_outputs

ROOT = Path(__file__).resolve().parents[1]


def make_pdf(path, count=2):
    path.parent.mkdir(parents=True, exist_ok=True)
    with cairo.PDFSurface(str(path), 300, 400) as surface:
        for number in range(count):
            cr = cairo.Context(surface)
            cr.move_to(20, 50)
            cr.show_text("Português *texto* page " + str(number + 1))
            surface.show_page()


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        self.environment.pop("DISPLAY", None)
        self.environment.pop("WAYLAND_DISPLAY", None)

    def command(self, *arguments):
        return [sys.executable, "-B", str(ROOT / "main.py"), "export", *map(str, arguments)]

    def run_cli(self, *arguments):
        return subprocess.run(self.command(*arguments), env=self.environment,
                              capture_output=True, text=True, timeout=30)

    def test_headless_parallel_collision_and_failure(self):
        first, second = self.root / "a/same.pdf", self.root / "b/same.pdf"
        make_pdf(first)
        make_pdf(second)
        invalid = self.root / "bad.pdf"
        invalid.write_text("not a PDF")
        output = self.root / "output"
        report = self.root / "report.json"
        result = self.run_cli(first, second, invalid, "--format", "md,txt,json",
                              "--jobs", 2, "--output-dir", output, "--report", report)
        self.assertEqual(result.returncode, 1, result.stderr)
        summary = json.loads(report.read_text())
        self.assertEqual((summary["succeeded"], summary["failed"]), (2, 1))
        self.assertEqual(len(list(output.iterdir())), 6)
        for path in output.glob("*.json"):
            data = json.loads(path.read_text())
            self.assertEqual([page["number"] for page in data["pages"]], [1, 2])
            self.assertIn("Português", data["pages"][0]["text"])
        for path in output.glob("*.md"):
            self.assertIn(r"\*texto\*", path.read_text())

    def test_range_and_no_overwrite(self):
        source = self.root / "input.pdf"
        make_pdf(source, 3)
        output = self.root / "output"
        result = self.run_cli(source, "--format", "json", "--pages", "2-3",
                              "--output-dir", output, "--jobs", 1)
        self.assertEqual(result.returncode, 0, result.stderr)
        target = output / "input.json"
        original = target.read_bytes()
        self.assertEqual([page["number"] for page in json.loads(original)["pages"]], [2, 3])
        result = self.run_cli(source, "--format", "json", "--output-dir", output)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(target.read_bytes(), original)
        result = self.run_cli(source, "--format", "json", "--pages", "4",
                              "--output-dir", output, "--overwrite")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(target.read_bytes(), original)
        self.assertFalse(list(output.glob(".inpedf-*")))

    def test_publication_rollback(self):
        stage = self.root / "stage"
        stage.mkdir()
        for fmt in ("md", "json"):
            (stage / ("document." + fmt)).write_text("new")
        md = self.root / "result.md"
        md.write_text("original")
        blocked = self.root / "blocked.json"
        blocked.mkdir()
        with self.assertRaises(FileExistsError):
            publish_outputs(stage, {"md": md, "json": blocked}, overwrite=True)
        self.assertEqual(md.read_text(), "original")
        self.assertTrue(blocked.is_dir())

    def test_cancel_cleans_staging(self):
        source = self.root / "large.pdf"
        make_pdf(source, 1000)
        output = self.root / "output"
        process = subprocess.Popen(
            self.command(source, "--format", "md,txt,json", "--output-dir", output),
            env=self.environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and process.poll() is None:
            if output.exists() and list(output.glob(".inpedf-*")):
                process.send_signal(signal.SIGINT)
                break
            time.sleep(0.01)
        stdout, stderr = process.communicate(timeout=15)
        self.assertEqual(process.returncode, 130, stderr)
        self.assertFalse(list(output.iterdir()))

    def test_worker_crash_does_not_hang(self):
        source = self.root / "input.pdf"
        make_pdf(source)
        output = self.root / "output"
        driver = self.root / "crashing_worker.py"
        driver.write_text(
            "import os, sys\n"
            + "sys.path.insert(0, " + repr(str(ROOT)) + ")\n"
            + "from inpedf import export_cli\n"
            + "def crash(*args):\n    os._exit(9)\n"
            + "if __name__ == '__main__':\n"
            + "    export_cli.convert_worker = crash\n"
            + "    raise SystemExit(export_cli.main(sys.argv[1:]))\n"
        )
        result = subprocess.run(
            [sys.executable, "-B", str(driver), str(source), "--output-dir", str(output)],
            env=self.environment, capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("without a result", result.stderr)
        self.assertFalse(list(output.iterdir()))

    def test_help_does_not_import_gtk(self):
        for arguments in (["--help"], ["--usage"], ["--version"], ["export", "--help"], ["export", "--usage"]):
            with self.subTest(arguments=arguments):
                code = (
                    "import runpy,sys; sys.argv=" + repr(["main.py", *arguments]) + ";\n"
                    "try: runpy.run_path(" + repr(str(ROOT / "main.py")) + ",run_name='__main__')\n"
                    "except SystemExit as error: assert error.code == 0\n"
                    "assert 'gi.repository.Gtk' not in sys.modules\n"
                    "assert 'inpedf.application' not in sys.modules\n"
                )
                result = subprocess.run(
                    [sys.executable, "-B", "-c", code], env=self.environment,
                    capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                if arguments == ["--version"]:
                    self.assertEqual(result.stdout.strip(), f"inPeDF {__version__}")
                else:
                    self.assertIn("usage:", result.stdout)

    def test_quiet_and_verbose(self):
        source = self.root / "input.pdf"
        make_pdf(source)
        report = self.root / "quiet-report.json"
        result = self.run_cli(source, "--quiet", "--output-dir", self.root / "quiet", "--report", report)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(report.read_text())["succeeded"], 1)
        result = self.run_cli(source, "--quiet", "--output-dir", self.root / "quiet")
        self.assertEqual(result.returncode, 1)
        self.assertIn("ERROR", result.stderr)
        self.assertNotIn("Completed:", result.stderr)
        result = self.run_cli(source, "--verbose", "--output-dir", self.root / "verbose")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DETAIL worker PID", result.stderr)
        self.assertIn("DETAIL output:", result.stderr)
        result = self.run_cli(source, "--quiet", "--verbose")
        self.assertEqual(result.returncode, 2)

    def test_selection_and_markdown(self):
        self.assertEqual(page_indices("3,1-2,2", 3), [0, 1, 2])
        with self.assertRaises(ValueError):
            page_indices("0", 3)
        self.assertEqual(markdown_text("*text* [a]"), r"\*text\* \[a\]")


if __name__ == "__main__":
    unittest.main()
