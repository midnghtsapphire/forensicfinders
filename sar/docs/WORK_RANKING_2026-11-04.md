# Work ranking, 2026-11-04 — confidence scale for what to do next

**Who:** Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
**When:** 2026-11-04
**Why:** Audrey delegated the ordering decision ("create a confidence scale on what to
work on next and follow it silently") and asked that the reasoning live in the repo
rather than in a chat, so the ranking is auditable after the fact.
**What:** NEW FILE, additive. No code is changed by this document. It records (1) the
result of a search for prior work orders covering the decode seam, (2) the ranking I
worked to, with the confidence in each item and why, and (3) what I deliberately did
not touch and what each of those needs before it can move.

---

## 1. Prior-work search: is there an existing WR or PR that was supposed to do this?

Asked before building, so an existing attempt could be used as the reference rather
than duplicated. Searched: all open and closed PRs in `midnghtsapphire/forensicfinders`;
both repositories for a `#CODE_THE_DECODER` marker; both for `WR`-numbered items; and
`revvel-standards` for a WR register or index.

**Found — and it is already merged.**

| | |
|---|---|
| PR | #4 `feat(sar): decode seam (850) and ASF HyP3 InSAR connector (980)` |
| Branch | `feat/decode-seam-hyp3-insar` |
| Merged | 2026-10-29 |
| Registry ID | 850 `decode_hooks` |

How far it got: **all the way.** `sar/decode_hooks.py` is complete — `register()`,
`unregister()`, `clear()`, `registered()`, `apply()`, per-decoder scoping against
`KNOWN_DECODERS`, `DecodeHookError` carrying the failing hook's name, and a
`meta["decode_hooks_applied"]` receipt recording what actually ran rather than what was
installed. It is wired into all three decode points it claims:

```
geo_connectors/stac.py:168               read_cog_window -> decode_hooks.apply(band, meta)
instrument_input/instrument_input.py:88  read_points     -> decode_hooks.apply(points, meta)
instrument_input/instrument_input.py:121 read_gpr_csv    -> decode_hooks.apply(traces, meta)
```

Tests, measured 2026-11-04 on Python 3.14.3: `test_decode_hooks.py` 17 tests, OK.
`instrument_input/test_decode_seam.py` and `geo_connectors/test_geo_connectors.py`
additionally assert the returned **values** through the real decoders, not that the
source mentions the module — including that a hook scoped to one decoder does not fire
on another, and that both callers import the same module object.

Does its approach differ from a seam proposed later? No. It is the same design decision
recorded in the registry entry — condition once where bytes become an array, so no
consumer can skip a correction by forgetting an argument.
`sar/docs/DECODE_INJECTION_DESIGN.md` carries the design note.

**No WR number exists for it.** forensicfinders has no `wr/memory/` and no WR register.
The WR register in `revvel-standards` (`docs/wr/`, `artifacts/wrs/`,
`compliance/wr-15279/`, `mcp-servers/wr-control-plane/`) covers other products —
finishers, photon bench, title studio — and contains nothing matching "decode". No
`#CODE_THE_DECODER` marker exists in either repository.

### What this means for "which decode seam to build first"

That question has no remaining build in it. The seam is finished, wired and tested, and
`apply()` is the identity function until a hook is registered. What is left is not a
seam — it is **the content of the first hook**, i.e. which correction to actually apply
to the data. That is a judgement about the sensors and the cases, not a coding choice,
so it is listed in section 3 as needing Audrey, not ranked as work. `decode_hooks.py`
says plainly what the seam is *not*: not the NSR injector from the GIS Server Technical
Reference, because this repository never sees raw complex IQ.

---

## 2. The ranking I worked to

Confidence here means confidence that **doing the item is correct and that I can prove
it worked** — not how easy it is. An item ranks high when the defect is measurable
before the change, the fix has one obvious form, and the postcondition can be asserted
by something that fails if the fix is reverted (RVS-VERIFY-001). It ranks low when
"done" depends on a decision that is Audrey's, however small the diff would be.

| # | Item | Confidence | Why it sits here |
|---|---|---|---|
| 1 | `multi_proxy` tests import and run under component 100 | **Highest** | Red main. `GREEN_MAIN_STANDARD.md` makes it a fleet emergency outranking feature work. Defect reproduced before the change, measured after, guard mutation-tested. Nothing judgement-shaped in it. |
| 2 | `forensic_pipeline/tests/test_snow_wells_pipes.py` has never run | **High** | Same defect class as 1, found by the same audit. Measurable: the file errors on collection today. One obvious fix shape. Its own absence of a registry entry is the bug, so the postcondition is checkable. |
| 3 | Orphan detection for test files no component runs | **High** | This is item 2's regression test, not separate work. `GREEN_MAIN_STANDARD.md` requires a regression test per fix, and the failure mode being guarded is precisely "a test file exists that nothing executes". Shipped with 2. |
| 4 | Port `anti-scaffolding-enforcer.yml` / `no-root-junk.yml` as a pre-commit hook | **Medium** | Clearly useful — §1 and §5 drifted because forensicfinders inherits the standards by convention and enforces none of them. Dropped below 2 because Actions cannot run on this account (billing lock), so the honest form is a local hook, and a hook that blocks her own commits is a working-habit change I should not impose silently. |
| 5 | Conventional Commits going forward | **Medium-high, but not a task** | 9 of the last 10 commits fail `AGENTS.md`. Nothing to build; it is applied by doing it. Every commit I have made follows it. |
| 6 | Finish or remove the 7 `multi_proxy` scaffolding instances | **Low** | `loader.py` raises `NotImplementedError` on every call, so the module cannot be used as committed, and `VISITING_AGENTS.md` §1 forbids shipping it. But "remove" is forbidden outright by the never-delete rule, and "finish" means choosing rasterio/laspy read paths, band ordering and nodata handling for real products — inventing those would be exactly the failure Audrey warned about. Needs her, see section 3. |
| 7 | Fill the `WR:` field in the REVVEL-DISABLED headers | **Low** | Seven headers read `WR: UNASSIGNED`. A numbering scheme is a fleet-wide governance convention, not a local choice, and `revvel-standards` already has a numeric register for other products. Picking one here would fork it. Needs her. |

Worked in order. 1 shipped as PR #5. 2 and 3 shipped together as the PR this document
accompanies. 4 through 7 left, with 6 and 7 blocked on decisions that are hers.

---

## 3. Deliberately left, and what each needs

- **The first decode hook.** The seam is finished; nothing registers a hook. Which
  correction to apply — clock/geolocation, radiometry, speckle, polarimetric unmixing —
  is a statement about the sensors and the cases. I did not pick one. `KNOWN_DECODERS`
  and `register(decoders=...)` are the whole API needed once the answer exists.
- **`multi_proxy/loader.py`.** Raises `NotImplementedError` on every call. Finishing it
  needs the real read paths; removing it is not allowed. Left exactly as committed.
- **`WR:` numbering.** Left as `UNASSIGNED` in all seven headers rather than invented.
- **The 25 remaining component-100 failures.** All Windows-platform: openssl/TSA
  configuration, POSIX `0600` and directory-private checks, symlinks, TLS. Untouched,
  and the reason `SELF_HOSTED_CI.md` says to run the suite on Linux.
- **Merging anything.** Governance does not name a merge authority for this repository,
  so PRs are handed back as drafts, ready, and she merges.

## 4. Standing caveat on every "green" claim in this repository

The suite has never executed on Linux anywhere — not in CI, not in a container. GitHub
Actions is blocked account-wide by the billing lock, so no PR here carries check
results. Every measurement in this document and in the PRs it covers was taken on
Windows with Python 3.14.3. Treat the first green Linux run as new information rather
than as confirmation.
