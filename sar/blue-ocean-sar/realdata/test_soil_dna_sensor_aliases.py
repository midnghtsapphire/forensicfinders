"""Tests for soil_dna_sensor / soil_dna_sensor_interpret alias modules.

These modules must re-export the qpcr_* APIs (delete nothing; aliases only)
and must not import quarantine modules. Synthetic-only; no network.

Run: python -m unittest test_soil_dna_sensor_aliases
"""

from __future__ import annotations

import ast
import importlib
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

FORBIDDEN_MODULE_PREFIXES = (
    "case",
    "hfmr",
    "dossier",
    "evidence",
    "public_records",
)

ASSAY_EXPORTS = (
    "fit_standard_curve",
    "estimate_lod",
    "estimate_loq",
    "copies_per_gram",
    "classify_sample",
    "main",
    "EFF_RANGE",
    "R2_MIN",
)
INTERPRET_EXPORTS = ("ROLES", "TARGETS", "interpret", "load", "main")


def _imported_names(path: str) -> set[str]:
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=path)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module.split(".")[0])
    return names


class TestSoilDnaSensorAliases(unittest.TestCase):
    def test_soil_dna_sensor_imports_and_mirrors_qpcr_assay(self):
        import qpcr_assay as qa
        import soil_dna_sensor as sds

        for name in ASSAY_EXPORTS:
            self.assertTrue(hasattr(qa, name), f"qpcr_assay missing {name}")
            self.assertTrue(hasattr(sds, name), f"soil_dna_sensor missing {name}")
            self.assertIs(getattr(sds, name), getattr(qa, name))

    def test_soil_dna_sensor_interpret_mirrors_qpcr_interpret(self):
        import qpcr_interpret as qi
        import soil_dna_sensor_interpret as sdsi

        for name in INTERPRET_EXPORTS:
            self.assertTrue(hasattr(qi, name), f"qpcr_interpret missing {name}")
            self.assertTrue(hasattr(sdsi, name), f"soil_dna_sensor_interpret missing {name}")
            self.assertIs(getattr(sdsi, name), getattr(qi, name))

    def test_alias_ast_imports_are_not_quarantine(self):
        for modname in ("soil_dna_sensor", "soil_dna_sensor_interpret"):
            mod = importlib.import_module(modname)
            imported = _imported_names(mod.__file__)
            for bad in FORBIDDEN_MODULE_PREFIXES:
                self.assertNotIn(bad, imported, f"{modname} imports {bad}")
            # Allowed: the qpcr implementation modules only (plus future annotations).
            unexpected = imported - {"qpcr_assay", "qpcr_interpret", "__future__"}
            self.assertEqual(unexpected, set(), f"{modname} unexpected imports: {unexpected}")


if __name__ == "__main__":
    unittest.main()
