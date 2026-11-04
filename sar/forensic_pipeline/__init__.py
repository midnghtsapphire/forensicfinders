# ══════════════════════════════════════════════════════════════════════════════════════════
# Who:  Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
# When: 2026-11-04
# Why:  forensic_pipeline/ and forensic_pipeline/tests/ were committed with no __init__.py
#       anywhere, so neither was a package. Combined with registry.json having no entry for
#       this directory, the result was that tests/test_snow_wells_pipes.py had never once
#       executed -- written, committed, and never run. Its own imports could not resolve
#       either (`from sar.forensic_pipeline...` with nothing putting a `sar` package on
#       sys.path), so even a direct invocation failed.
# What: NEW FILE, empty package marker. Makes forensic_pipeline importable as
#       `forensic_pipeline` from sar/, which is the cwd every registry component uses as
#       its root (test_cwd "." means sar/, see registry.json components 200, 700, 850, 900).
# Notes: Deliberately empty. Nothing is re-exported here, because snow_wells_pipes.py is
#       pure array-in/array-out functions with no package-level state to set up, and an
#       __init__ that imports numpy/scipy would make the package unimportable on a runner
#       that only wants to read the module list.
# ══════════════════════════════════════════════════════════════════════════════════════════
