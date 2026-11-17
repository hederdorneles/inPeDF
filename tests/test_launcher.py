"""Regression checks for the actual Python entry point's desktop startup."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LauncherTests(unittest.TestCase):
    def test_python_entry_detaches_gui_and_logs_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entry = root / "main.py"
            entry.write_text((ROOT / "main.py").read_text())
            package = root / "inpedf"
            package.mkdir()
            (package / "__init__.py").write_text("")
            (package / "application.py").write_text(
                "import json,os,time\n"
                "from pathlib import Path\n"
                "class InPeDFApplication:\n"
                "    def run(self,argv):\n"
                "        print('desktop output',flush=True)\n"
                "        Path(os.environ['PROBE_RESULT']).write_text(json.dumps("
                "{'pid':os.getpid(),'args':argv[1:],'internal_marker':os.environ.get('_INPEDF_GUI_CHILD')}))\n"
                "        time.sleep(10)\n"
                "        return 0\n"
            )
            result_file = root / "result.json"
            environment = {**os.environ, "XDG_STATE_HOME": str(root / "state"),
                           "PROBE_RESULT": str(result_file)}
            environment.pop("_INPEDF_GUI_CHILD", None)
            result = subprocess.run(
                [sys.executable, "-B", str(entry), "a file.pdf"], env=environment,
                capture_output=True, text=True, timeout=5,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")
            deadline = time.monotonic() + 5
            while not result_file.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            data = json.loads(result_file.read_text())
            try:
                self.assertEqual(data["args"], ["a file.pdf"])
                self.assertEqual(os.getsid(data["pid"]), data["pid"])
                self.assertIsNone(data["internal_marker"])
                self.assertIn("desktop output", (root / "state/inpedf/inpedf.log").read_text())
            finally:
                os.kill(data["pid"], signal.SIGTERM)

    def test_log_failure_is_reported_to_terminal(self):
        with tempfile.TemporaryDirectory() as directory:
            invalid_state = Path(directory) / "not-a-directory"
            invalid_state.write_text("file")
            environment = {**os.environ, "XDG_STATE_HOME": str(invalid_state)}
            environment.pop("_INPEDF_GUI_CHILD", None)
            result = subprocess.run(
                [sys.executable, "-B", str(ROOT / "main.py")],
                env=environment, capture_output=True, text=True, timeout=5,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("Unable to start inPeDF", result.stderr)


if __name__ == "__main__":
    unittest.main()
