"""Tests for pi_radar_logger (811)."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import pi_radar_logger as log


class PiLogger(unittest.TestCase):
    def test_synthetic_session_layout(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = log.run_synthetic_session(Path(d))
            self.assertTrue((path / "meta.json").is_file())
            self.assertTrue((path / "gps.jsonl").is_file())
            self.assertTrue((path / "preview" / "last.json").is_file())
            radar = list((path / "radar").iterdir())
            self.assertEqual(len(radar), 1)
            meta = json.loads((path / "meta.json").read_text())
            self.assertEqual(meta["registry_id"], "811")
            gps_line = (path / "gps.jsonl").read_text().strip().splitlines()[0]
            fix = json.loads(gps_line)
            self.assertIn("lat", fix)
            self.assertEqual(fix["fix_quality"], 3)

    def test_capture_dir_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            when = datetime(2026, 10, 21, 12, 0, 0, tzinfo=timezone.utc)
            log.capture_dir(root, when=when)
            with self.assertRaises(FileExistsError):
                log.capture_dir(root, when=when)


if __name__ == "__main__":
    unittest.main()
