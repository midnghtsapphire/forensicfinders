# Anonymized case view — schema 0.1

Status: **pending-audrey-confirm**. `synthetic_only_until_confirmed` stays true. Schema confirmation alone is not clearance to emit a row as `real_anonymized`. Adopting the real-case policy is not the same as confirming this contract. This public repository carries synthetic fixtures only.

This is the contract Bedrock serves to the Godot game. Players see an anonymized case view. Real rows stay in a private table Secret owns. They do not appear in builds, exports, logs, this repository, or the player view.

The machine file is [`case_view_enums.json`](case_view_enums.json): JSON Schema draft 2020-12. Secret's export validator and Quill's briefing template both validate against that file. A standard validator is enough. Unknown keywords on the schema document (`version`, `status`, `banned_fields`, the policy objects) are annotations. Instance validation uses the core vocabularies only.

## Owners

| Concern | Owner |
|---|---|
| This contract (allowed fields, enums, reject rules) | Bedrock |
| `case_token` semantics (how a token is minted, and that it is never parsed) | Quill |
| Private table and the export that produces this view | Secret |
| Player client | GodotForge |

## Allowed fields

Every key below is required. Names are snake_case. `additionalProperties` is false on every emitted object (the case view and `location`). A string is an enum, the const `predicted`, or a pattern anchored with `^` and `$`. There is no unconstrained string.

| Field | Values | Rule |
|---|---|---|
| `case_token` | pattern `^CT-[0-9a-f]{12}$` | Random and opaque. Never derived from a name, a date, a place, a seed, or another id. Never parsed for those things. Lowercase hex only. A leading extra, a trailing extra, or a newline anywhere in the value is rejected. |
| `region_band` | `NEW_ENGLAND`, `MID_ATLANTIC`, `EAST_NORTH_CENTRAL`, `WEST_NORTH_CENTRAL`, `SOUTH_ATLANTIC`, `EAST_SOUTH_CENTRAL`, `WEST_SOUTH_CENTRAL`, `MOUNTAIN`, `PACIFIC`, `NORTHEAST`, `MIDWEST`, `SOUTH`, `WEST`, `NON_US`, `UNKNOWN` | The four coarse values `NORTHEAST`, `MIDWEST`, `SOUTH`, `WEST` are the fallback when the count in a fine band is `k < 5`. `UNKNOWN` is its own value. A missing or unrecognized band is not stored as `UNKNOWN`. |
| `terrain_class` | `FOREST`, `GRASSLAND_PRAIRIE`, `DESERT_SCRUB`, `MOUNTAIN_ALPINE`, `WETLAND_RIPARIAN`, `AGRICULTURAL`, `SUBURBAN`, `URBAN`, `WATER_COASTAL`, `UNKNOWN` | Terrain for a case comes from the procedural file `dem_synthetic_<seed>.tif`. Never from real geography. |
| `elapsed_band` | `E1` `[1, 5)`, `E2` `[5, 10)`, `E3` `[10, 20)`, `E4` `[20, 40)`, `E5` `[40, +)` years | Half-open: the lower year is included and the upper year is excluded. The wire value is the band id (`E1` … `E5`), not the range text. |
| `subject_category` | `CHILD_0_12`, `YOUTH_13_17`, `ADULT_18_64`, `OLDER_ADULT_65P`, `COGNITIVE_IMPAIRMENT`, `HIKER_OUTDOOR`, `HUNTER`, `WATER_RELATED`, `VEHICLE_RELATED`, `UNKNOWN` | Category code only. |
| `case_source` | `synthetic`, `real_anonymized` | Required. The HUD shows it. |
| `fixture_id` | string or null | When `case_source` is `synthetic`: pattern `^(sar/)?fixtures/[A-Za-z0-9._-]*synthetic[A-Za-z0-9._-]*$` (one path segment after `fixtures/`, no `..`). `fixtures/...` and `sar/fixtures/...` both pass. Any other prefix is rejected. A leading extra, a trailing extra, or a newline is rejected. Otherwise null. |
| `seed` | integer `≥ 0`, or null | When `case_source` is `synthetic`: the procedural DEM seed. Otherwise null. The key is present in both cases. A string, a float, or a bool is rejected and is not coerced. A bool is not an integer. |
| `location.label` | const `predicted` | See below. |

`fixture_id` and `seed` are always present. For `real_anonymized` they are JSON null.

## Predicted label

Any location object the API emits carries `label` with the const value `predicted`. The case view has one `location` object and that object has no other keys.

The case view has no coordinates of any kind and no fuzzed-coordinate substitutes. These names are not fields: `predicted_region_band`, `predicted_lat`, `predicted_lon`, cell tokens, latitude, longitude. The region is the enum `region_band` only.

## Reject unknown

A value outside an enum is invalid. Validators reject it. They do not coerce it to `UNKNOWN`, to a coarse region, to another spelling, or to a default. The same rule applies to a `case_token` that fails the pattern, a `location.label` other than `predicted`, and a key that is not in the table above.

`k < 5` is an export-time choice Secret makes by emitting one of the four coarse `region_band` values. It is not a coercion step inside the validator.

## Emission

`version` is `0.1`. `status` is `pending-audrey-confirm`. `synthetic_only_until_confirmed` is true.

Schema confirmation alone is not clearance. Adopting the real-case policy is not the same as confirming this contract.

A row is emitted as `real_anonymized` only if all of the following hold:

1. Every source for that case has `terms_allows_derived_use=yes`.
2. `identity_status=confirmed_public` for every case. `unconfirmed_pending_audrey` never emits.
3. The case has no `removal_requested` and no resolved hold.
4. Its `CASE_TOKEN` was freshly minted after confirmation and is active, not retired.
5. Its stand-in location check passed.
6. Secret has run the pinned full-quasi-identifier `k>=5` test plus the linkage and attribute-inference review.
7. Verity has co-signed the re-identification test as a private, comment-only review. The co-sign is pinned to all of `artifact_sha256`, `schema_commit`, `harness_commit`, `reference_snapshot`, `quasi_identifier_list`, `threshold` (`k>=5`), and `sanitized_pass_fail_counts`.

Secret runs the tests. Verity is the co-signer. If any check fails, the row is not emitted. Any change expires the co-sign. That includes any change to the matcher, the test harness, the artifact, the schema, the code, the sources, or the access. The exporter enforces these gates. JSON Schema does not.

Emission is a closed allowlist. Every row is validated against this schema before it is emitted. A row that fails validation is not emitted. `additionalProperties` is false on every emitted object, so `geometry`, `geohash`, `bbox`, `lat`, `lon`, `date`, `last_seen_date`, and any other key outside the allowlist are rejected at the root and inside nested objects, including `location`.

A rejection is a JSON path plus a fixed error code. The code does not include the submitted value, and it does not include a hash of an identifier. Patterns in the schema are anchored with `^` and `$`. The stdlib checker matches the whole string, so a trailing newline is rejected rather than treated as the end of the value.

The API schema allows `case_source = real_anonymized` so the HUD can show that source after the gate above. A fixture file in this repository is a stricter gate: every row is `synthetic`, with a `fixtures/*synthetic*` or `sar/fixtures/*synthetic*` id and a seed. A `real_anonymized` row in a fixture is rejected even when it would pass the API schema.

Checked-in fixture: `sar/fixtures/case_view_synthetic_1001.json`. Its `case_token` values are draws from `random.Random(1001)` (12 lowercase hex digits, prefixed with `CT-`). No `dem_synthetic_*.tif` ships in this tree; each row stores the repo-relative procedural path `sar/fixtures/dem_synthetic_<seed>.tif`.

## Banned

`banned_fields` is defence in depth only. It is not the primary control. The primary control is the closed allowlist and schema validation of every row before emission. The names below are keys Secret's exporter also drops. They do not appear on the case view, in fixtures, in logs of this API, or in the player client:

- name
- dob and date of birth
- exact addresses
- family contacts
- photos
- aliases
- agency case numbers
- `case_id` and `CC-*` ids
- `anon_id` internals
- urls and source urls
- lat, lon, geometry, geohash, bbox, and any coordinates, including predicted or cell-token substitutes
- dates, including `date` and `last_seen_date`
- tip content
- free text (notes, narrative, description)
- any other PII

## Export columns

Secret's export spells the columns in the header. The case-view keys are the snake_case names.

| Export column | Case-view key |
|---|---|
| `CASE_TOKEN` | `case_token` |
| `REGION_BAND` | `region_band` |
| `TERRAIN_CLASS` | `terrain_class` |
| `ELAPSED_BAND` | `elapsed_band` |
| `SUBJECT_CATEGORY` | `subject_category` |
| `CASE_SOURCE` | `case_source` |

## Tips

Tips go to the investigating agency. They are never published, never stored on the case view, and never sent to the game.
