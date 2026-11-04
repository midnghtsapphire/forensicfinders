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
**Updated later the same day, after PR #8 shipped item 6.** The update reconciles this
document rather than appending a correction elsewhere, per `GREEN_MAIN_STANDARD.md` §4.
Superseded text is struck through rather than deleted, so a wrong call stays legible next
to what replaced it — item 6 was ranked three places too low, and reading why is the only
thing that makes the scale worth keeping.

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
| 4 | Port `anti-scaffolding-enforcer.yml` / `no-root-junk.yml` as a pre-commit hook | **Medium, then blocked** | Clearly useful — §1 and §5 drifted because forensicfinders inherits the standards by convention and enforces none of them. Ranked below 2 because Actions cannot run on this account (billing lock), so the honest form is a local hook, and a hook that blocks her own commits is a working-habit change I should not impose silently. **Attempting it then showed it is blocked by item 6, not merely lower priority** — see section 3. |
| 5 | Conventional Commits going forward | **Medium-high, but not a task** | 9 of the last 10 commits fail `AGENTS.md`. Nothing to build; it is applied by doing it. Every commit I have made follows it. |
| 6 | Finish or remove the 7 `multi_proxy` scaffolding instances | **Ranked Low. That was wrong — shipped as PR #8** | The reasoning below is kept because it was the reasoning, and it was mistaken. What it missed: `loader.py` and `data_fetcher.fetch_sentinel2` were unfinished *clones* of capability this repository already ships, finished and tested, in `sar/geo_connectors/stac.py`. Finishing them therefore needed no read paths invented and no band ordering chosen — `VISITING_AGENTS.md` §2 ("Extend them; don't clone them under a new name") settled it. ~~`loader.py` raises `NotImplementedError` on every call, so the module cannot be used as committed, and `VISITING_AGENTS.md` §1 forbids shipping it. But "remove" is forbidden outright by the never-delete rule, and "finish" means choosing rasterio/laspy read paths, band ordering and nodata handling for real products — inventing those would be exactly the failure Audrey warned about. Needs her, see section 3.~~ |
| 7 | Fill the `WR:` field in the REVVEL-DISABLED headers | **Low** | Seven headers read `WR: UNASSIGNED`. A numbering scheme is a fleet-wide governance convention, not a local choice, and `revvel-standards` already has a numeric register for other products. Picking one here would fork it. Needs her. |

Worked in order. 1 shipped as PR #5. 2 and 3 shipped together as PR #7. 4 was attempted
and turned out to be blocked by 6 rather than merely lower-priority, so the real order is
6 then 4. 5 is not a task. **6 shipped as PR #8, and the ranking was wrong about it** — I
had it as a decision that was Audrey's, and it was not one; see the row above and section
3. 7 is still hers.

Where this ranking held up and where it did not, stated plainly because the scale is only
useful if its misses are visible: items 1, 2 and 3 were ranked correctly and shipped in
the order given. Item 6 was ranked three places too low, and for the wrong reason — I
judged it by what finishing the code would require from scratch instead of first checking
whether the repository already contained it. The lesson is cheap to state and was
expensive to find: before ranking an unfinished module as "needs a product decision",
grep for the capability elsewhere in the repository. Item 4's position was right but its
status was wrong: blocked, not deprioritised.

---

## 3. Deliberately left, and what each needs

- **The first decode hook.** The seam is finished; nothing registers a hook. Which
  correction to apply — clock/geolocation, radiometry, speckle, polarimetric unmixing —
  is a statement about the sensors and the cases. I did not pick one. `KNOWN_DECODERS`
  and `register(decoders=...)` are the whole API needed once the answer exists.
- ~~**`multi_proxy/loader.py`.** Raises `NotImplementedError` on every call. Finishing it
  needs the real read paths; removing it is not allowed. Left exactly as committed.~~
  **No longer left — PR #8.** `load_geotiff` delegates to
  `geo_connectors/stac.py:read_cog_window`, so it needed no read path of its own and adds
  no name to `decode_hooks.KNOWN_DECODERS`. `load_geotiff_stub` is kept, as the
  never-delete rule requires, and now forwards and works. `fetch_sentinel2` went the same
  way, to `stac.search` against Element84 Earth Search, which removes the Copernicus
  account the original asked for rather than implementing it. `twi.py` was comment-only:
  zero executable lines changed.
- **`multi_proxy/README.md`'s `run_one_tile`.** The README documents
  `run_one_tile(dem_path=..., spectral_path=..., synthetic=False)` and no such function
  exists anywhere in the repository. Writing it means deciding how a tile is orchestrated
  end to end — which engines run in what order, what a tile's output record looks like —
  and that is a judgement about the cases. PR #8 left it alone and flagged it. Its import
  paths are also unresolvable (`sar.blue_ocean_sar...`: `sar/` is the directory components
  run *from*, not a package, and the directory uses hyphens), which is a transcription fix
  worth doing with whatever `run_one_tile` turns out to be rather than before it.
- **The scaffolding gate (item 4), because item 6 blocks it.** This came out of trying
  it, not out of ranking it, so it is worth stating plainly. A scaffolding check added
  as a registry component today has only two possible outcomes, and both are
  unacceptable: it fails, which makes main red for a defect it was added to *report*
  rather than one it introduced; or it ships with the seven known instances in an
  allowlist, which converts a violation into a blessed exception and is the "append
  rather than reconcile" pattern `GREEN_MAIN_STANDARD.md` §4 was written about. So the
  gate cannot land clean until the scaffolding it would catch is resolved, and that
  resolution is item 6, which is yours. The order is therefore 6 then 4, not 4 then 6.

  **Updated 2026-11-04, after PR #8.** Item 6 is no longer the blocker and was never
  yours. The blocker is now counted rather than guessed. Measured on `aea7020`, the
  enforcer's own word list hits **22 lines across 10 files** under `sar/` outside
  `multi_proxy`:

  | | | | |
  |---|---|---|---|
  | `opendata/` | 11 | `sar_person_finder_v3.py` | 2 |
  | `opendata` tests | 5 | `sar_dual_comms_publisher.py` | 1 |
  | `realdata/` | 2 | `coldtrace` | 1 |

  PR #8 ships a scan of `multi_proxy/` only, for exactly the §4 reason above — widening it
  today makes main red for defects it reports rather than introduces. So the order is now
  **those 10 files, then the repository-wide gate**. Each of those 22 lines needs the same
  question PR #8 answered for `multi_proxy`: is this an unfinished clone of something the
  repository already has, or does finishing it need a decision? That is answerable file by
  file and does not need you until a file turns out to be the second kind.
- **`.github/workflows/sar-tests-selfhosted.yml` and `sar/docs/SELF_HOSTED_CI.md`.**
  Both are finished and both are still untracked in the main checkout, dated
  2026-10-24. They are not mine — they predate this session — and a side session
  commits only files it changed itself, so I did not commit them. Flagging them rather
  than quietly adopting them: they are ready whenever you want them in.
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
