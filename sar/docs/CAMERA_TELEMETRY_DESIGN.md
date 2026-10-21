# Design note: camera / CCTV telemetry (DESIGN ONLY, no code)

**Status: not implemented. Nothing in this repo connects to any camera, doorbell, NVR or ALPR system, and no template contains credential fields for Ring, Arlo, Reolink, Flock or similar.**

## Legal gate (must happen before any code exists)
Footage or telemetry from third-party cameras may be used **only** with one of:
- written **owner consent** (scope, cameras, time window, retention), or
- **legal process**: a warrant, court order or subpoena obtained by the investigating agency, or
- an **agency MOU or data-sharing agreement**, e.g. a police department's registered-camera program.

Vendor portals and ALPR networks (e.g. Flock) are accessed **by the agency under its own account and policy**, not by us. We receive exports from the agency.

## Proposed design (once the gate is met)
1. **Ingest exports only.** Accept files the authorised party exports (MP4 plus vendor metadata CSV/JSON). No live polling, no stored vendor credentials.
2. **Record authority with each item:** consent or warrant reference, who exported it, and when. Ingest is refused without it, the same pattern as `public_records_engine.register(..., authority=...)`.
3. **Chain of custody:** SHA-256 on arrival, append-only manifest, reuse `blue-ocean-sar/evidence` (component 110).
4. **Time normalisation:** camera clock offset recorded against a reference, using a visible clock or a known event.
5. **Output:** timestamped observations (camera id, time window, what was seen) graded with registry 1200 (reliability), e.g. `instrument_record / export_without_hash / documented`.
6. **Retention:** delete per the consent or warrant terms, and log the deletion.

## Open questions for Audrey and the agency
- Which agencies supply exports, and in what formats?
- Retention period, and who holds the master copies (the agency, not us)?
