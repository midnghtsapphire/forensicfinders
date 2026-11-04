# ══════════════════════════════════════════════════════════════════════════════════════════
# Who:  Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
# When: 2026-11-04
# Why:  See forensic_pipeline/__init__.py. This directory also needed to be a package so
#       that the test module resolves as `forensic_pipeline.tests.test_snow_wells_pipes`
#       and the sibling import of `forensic_pipeline.snow_wells_pipes` resolves with sar/
#       on sys.path rather than this directory.
# What: NEW FILE, empty package marker.
# Notes: Empty on purpose -- no shared fixtures live here. If fixtures are ever added, note
#       that this suite runs under pytest (registry component 990), not unittest, because
#       test_snow_wells_pipes.py is written pytest-style and uses pytest.approx.
# ══════════════════════════════════════════════════════════════════════════════════════════
