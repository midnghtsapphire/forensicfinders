"""Stdlib validator for the anonymized case-view contract (schema 0.1).

The contract file is JSON Schema draft 2020-12. This module checks the subset
that file uses: $ref, type, const, enum, pattern, minimum, properties,
required, additionalProperties false, oneOf, and if/then/else. Unknown schema
keywords are ignored, matching a standard validator. Instance values that fail
are rejected and left unchanged. A violation is a JSON path plus a fixed code.
"""
import copy
import hashlib
import json
import random
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO / "docs" / "sensecrew" / "bedrock" / "schemas" / "case_view_enums.json"
FIXTURE_PATH = REPO / "sar" / "fixtures" / "case_view_synthetic_1001.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
RECORDS = FIXTURE["records"]

HEX = "0123456789abcdef"
FIXTURE_ID_RE = r"^(sar/)?fixtures/[A-Za-z0-9._-]*synthetic[A-Za-z0-9._-]*$"
FIXTURE_ID_PATTERN = re.compile(FIXTURE_ID_RE)
REAL_EXPORT_BLOCK = (
    "Real exports stay blocked until the Charley Project licence is cleared "
    "and Verity co-signs the re-identification test."
)
SNAKE = re.compile(r"^[a-z][a-z0-9_]*$")

REQUIRED_BANNED = frozenset({
    "name",
    "dob",
    "date_of_birth",
    "exact_address",
    "address",
    "family_contact",
    "family_contacts",
    "photo",
    "photos",
    "alias",
    "aliases",
    "agency_case_number",
    "case_id",
    "cc_id",
    "anon_id",
    "url",
    "urls",
    "source_url",
    "source_urls",
    "lat",
    "lon",
    "lng",
    "latitude",
    "longitude",
    "coordinates",
    "predicted_region_band",
    "predicted_lat",
    "predicted_lon",
    "cell_token",
    "tip",
    "tip_content",
    "tips",
    "free_text",
    "notes",
    "narrative",
})

EXPORT_COLUMN_MAP = {
    "CASE_TOKEN": "case_token",
    "REGION_BAND": "region_band",
    "TERRAIN_CLASS": "terrain_class",
    "ELAPSED_BAND": "elapsed_band",
    "SUBJECT_CATEGORY": "subject_category",
    "CASE_SOURCE": "case_source",
}

REGION_ORDER = [
    "NEW_ENGLAND",
    "MID_ATLANTIC",
    "EAST_NORTH_CENTRAL",
    "WEST_NORTH_CENTRAL",
    "SOUTH_ATLANTIC",
    "EAST_SOUTH_CENTRAL",
    "WEST_SOUTH_CENTRAL",
    "MOUNTAIN",
    "PACIFIC",
    "NORTHEAST",
    "MIDWEST",
    "SOUTH",
    "WEST",
    "NON_US",
    "UNKNOWN",
]


class SchemaError(Exception):
    """The contract file uses a keyword this checker does not implement."""


def _violation(path, code):
    """Path plus a fixed code. The submitted value is not part of the text."""
    return path + ": " + code


def _deref(root, ref):
    if not isinstance(ref, str) or not ref.startswith("#/"):
        raise SchemaError("bad_ref")
    node = root
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or part not in node:
            raise SchemaError("bad_ref")
        node = node[part]
    return node


def _is_type(instance, name):
    if name == "null":
        return instance is None
    if name == "boolean":
        return isinstance(instance, bool)
    if name == "integer":
        # bool is a subclass of int and is not an integer in this contract.
        return isinstance(instance, int) and not isinstance(instance, bool)
    if name == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if name == "string":
        return isinstance(instance, str)
    if name == "object":
        return isinstance(instance, dict)
    if name == "array":
        return isinstance(instance, list)
    raise SchemaError("unsupported_type")


def _pattern_matches(pattern, text):
    """Match the whole string. A schema `$` anchor is end-of-string, not before a newline."""
    if not isinstance(pattern, str) or not isinstance(text, str):
        return False
    body = pattern
    if body.startswith("^"):
        body = "\\A" + body[1:]
    else:
        body = "\\A" + body
    if body.endswith("$") and not body.endswith("\\$"):
        body = body[:-1] + "\\Z"
    elif not body.endswith("\\Z"):
        body = body + "\\Z"
    return re.fullmatch(body, text) is not None


def validate(instance, schema, root=None, path="$"):
    """Return a list of violations. An empty list means the instance matches."""
    if root is None:
        root = schema
    if not isinstance(schema, dict):
        raise SchemaError("bad_schema")
    if "$ref" in schema:
        if set(schema) != {"$ref"}:
            raise SchemaError("bad_ref")
        return validate(instance, _deref(root, schema["$ref"]), root, path)

    errors = []
    if "const" in schema and instance != schema["const"]:
        errors.append(_violation(path, "const"))
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(_violation(path, "enum"))

    if "type" in schema:
        types = schema["type"]
        type_list = [types] if isinstance(types, str) else list(types)
        if not any(_is_type(instance, item) for item in type_list):
            errors.append(_violation(path, "type"))
            return errors

    if "pattern" in schema:
        if not _pattern_matches(schema["pattern"], instance):
            errors.append(_violation(path, "pattern"))

    if "minimum" in schema:
        if not _is_type(instance, "integer") or instance < schema["minimum"]:
            errors.append(_violation(path, "minimum"))

    if "oneOf" in schema:
        matched = 0
        branch_errors = []
        for branch in schema["oneOf"]:
            branch_result = validate(instance, branch, root, path)
            if branch_result:
                branch_errors.extend(branch_result)
            else:
                matched += 1
        if matched != 1:
            errors.append(_violation(path, "one_of"))
            errors.extend(branch_errors)

    if "properties" in schema or "required" in schema or schema.get("type") == "object":
        if not isinstance(instance, dict):
            errors.append(_violation(path, "object"))
            return errors
        props = schema.get("properties", {})
        for key in schema.get("required", ()):
            if key not in instance:
                errors.append(_violation(path + "." + key, "missing_required"))
        additional = schema.get("additionalProperties", True)
        if additional is False:
            if any(key not in props for key in instance):
                errors.append(_violation(path, "additional_property"))
        elif additional is not True:
            raise SchemaError("unsupported_additional")
        for key, sub in props.items():
            if key in instance:
                errors.extend(validate(instance[key], sub, root, path + "." + key))

    if "if" in schema:
        if not validate(instance, schema["if"], root, path):
            if "then" in schema:
                errors.extend(validate(instance, schema["then"], root, path))
        elif "else" in schema:
            errors.extend(validate(instance, schema["else"], root, path))
    return errors


def case_tokens(count, seed):
    """CT- plus 12 lowercase hex draws. The record fields are not inputs."""
    rng = random.Random(seed)
    return ["CT-" + "".join(rng.choice(HEX) for _ in range(12)) for _ in range(count)]


def fixture_violations(records, schema=SCHEMA):
    """API-valid rows still fail here unless every row is synthetic."""
    violations = []
    for index, record in enumerate(records):
        for item in validate(record, schema):
            violations.append("record[%d]: %s" % (index, item))
        if record.get("case_source") != "synthetic":
            violations.append("record[%d].case_source: fixture_source" % index)
    return violations


def _pattern_nodes():
    found = []

    def visit(node, path):
        if "pattern" in node:
            found.append((path, node))

    _walk_schema(SCHEMA, "$", visit)
    return found


def _enum(name):
    node = SCHEMA["$defs"][name]
    assert node["type"] == "string"
    assert "enum" in node
    return list(node["enum"])


def _accepted(record):
    errors = validate(record, SCHEMA)
    assert errors == [], errors


def _rejected(record):
    before = copy.deepcopy(record)
    errors = validate(record, SCHEMA)
    assert errors, "expected rejection"
    assert record == before, "validator changed the instance"


def _walk_schema(node, path, visit):
    if not isinstance(node, dict) or "$ref" in node:
        return
    visit(node, path)
    for key in ("properties", "$defs"):
        for name, sub in node.get(key, {}).items():
            _walk_schema(sub, "%s.%s.%s" % (path, key, name), visit)
    for key in ("items", "if", "then", "else", "not"):
        if key in node:
            _walk_schema(node[key], "%s.%s" % (path, key), visit)
    for key in ("oneOf", "anyOf", "allOf"):
        for index, sub in enumerate(node.get(key, ())):
            _walk_schema(sub, "%s.%s[%d]" % (path, key, index), visit)


def _dem_synthetic_names():
    roots = (
        REPO / "fixtures",
        REPO / "sar" / "fixtures",
        REPO / "sar" / "sensegame",
        REPO / "docs" / "sensecrew" / "bedrock",
    )
    found = []
    for root in roots:
        if not root.is_dir():
            continue
        found.extend(path.name for path in root.rglob("dem_synthetic_*") if path.is_file())
    return sorted(found)


def test_schema_file_identity():
    assert SCHEMA["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert SCHEMA["version"] == "0.1"
    assert SCHEMA["status"] == "pending-audrey-confirm"
    assert "confirmation" not in SCHEMA
    assert SCHEMA["synthetic_only_until_confirmed"] is True
    assert SCHEMA["real_export_block"] == REAL_EXPORT_BLOCK
    assert "secret_export_co_sign" not in SCHEMA_PATH.read_text(encoding="utf-8")
    assert SCHEMA["emission_gate"] == {
        "enforced_by": "exporter",
        "json_schema_enforces_gates": False,
        "real_anonymized_requires_all": [
            "terms_allows_derived_use_yes",
            "identity_status_confirmed_public",
            "no_removal_requested_and_no_resolved_hold",
            "case_token_minted_after_confirmation_and_active",
            "stand_in_location_check_passed",
            "secret_pinned_full_quasi_identifier_k_at_least_5_plus_linkage_and_attribute_inference_review",
            "verity_private_comment_only_cosign_pinned_to_artifact_sha256",
        ],
        "identity_status_emits": "confirmed_public",
        "identity_status_never_emits": "unconfirmed_pending_audrey",
        "tests_run_by": "Secret",
        "cosign_by": "Verity",
        "cosign_kind": "private_comment_only",
        "cosign_pinned_to": "artifact_sha256",
        "expiry_on_any_change": True,
        "expiry_includes": [
            "matcher",
            "test_harness",
            "artifact",
            "schema",
            "code",
            "sources",
            "access",
        ],
        "schema_confirmation_is_clearance": False,
        "primary_control": "closed_allowlist_schema_validation_before_emit",
        "banned_fields_role": "defence_in_depth",
    }
    assert SCHEMA["emission_gate"]["json_schema_enforces_gates"] is False
    assert SCHEMA["emission_gate"]["schema_confirmation_is_clearance"] is False
    assert SCHEMA["emission_gate"]["identity_status_emits"] == "confirmed_public"
    assert SCHEMA["emission_gate"]["identity_status_never_emits"] == "unconfirmed_pending_audrey"
    assert SCHEMA["owners"] == {
        "contract": "Bedrock",
        "token_semantics": "Quill",
        "private_table_and_export": "Secret",
        "consumer": "GodotForge",
    }
    assert SCHEMA["export_column_map"] == EXPORT_COLUMN_MAP
    assert set(EXPORT_COLUMN_MAP.values()) <= set(SCHEMA["properties"])
    assert SCHEMA["case_token_policy"] == {"opaque": True, "derived": False, "parsed": False}
    assert SCHEMA["tips_policy"] == {"recipient": "investigating_agency", "published": False}
    assert SCHEMA["terrain_policy"]["real_geography"] is False
    assert SCHEMA["terrain_policy"]["fixture_template"] == "sar/fixtures/dem_synthetic_<seed>.tif"
    assert SCHEMA["$defs"]["case_token"]["pattern"] == "^CT-[0-9a-f]{12}$"
    assert SCHEMA["$defs"]["synthetic_fixture_id"]["pattern"] == FIXTURE_ID_RE
    pattern_nodes = _pattern_nodes()
    assert pattern_nodes
    for node_path, node in pattern_nodes:
        pattern = node["pattern"]
        assert pattern.startswith("^") and pattern.endswith("$"), node_path


def test_region_and_elapsed_bands_match_the_contract():
    assert _enum("region_band") == REGION_ORDER
    policy = SCHEMA["region_band_policy"]
    assert policy["coarse_fallback_when_k_below"] == 5
    assert policy["coarse_fallback"] == ["NORTHEAST", "MIDWEST", "SOUTH", "WEST"]
    parts = policy["fine"] + policy["coarse_fallback"] + policy["other"]
    assert parts == REGION_ORDER
    assert len(parts) == len(set(parts))

    assert _enum("elapsed_band") == ["E1", "E2", "E3", "E4", "E5"]
    bands = SCHEMA["elapsed_band_years"]
    assert [item["id"] for item in bands] == ["E1", "E2", "E3", "E4", "E5"]
    expected = [(1, 5), (5, 10), (10, 20), (20, 40), (40, None)]
    for item, (low, high) in zip(bands, expected):
        assert item["min_inclusive"] == low
        assert item["max_exclusive"] == high
    for earlier, later in zip(bands, bands[1:]):
        assert earlier["max_exclusive"] == later["min_inclusive"]


def test_property_names_are_snake_case_and_objects_are_closed():
    closed = []
    string_schemas = []

    def visit(node, path):
        if node.get("type") == "object":
            assert node.get("additionalProperties") is False, path
            closed.append(path)
        for name in node.get("properties", {}):
            assert SNAKE.fullmatch(name), name
            assert name not in SCHEMA["banned_fields"]
        types = node.get("type")
        type_list = [types] if isinstance(types, str) else list(types or [])
        if "string" in type_list:
            string_schemas.append((path, node))

    _walk_schema(SCHEMA, "$", visit)
    assert len(closed) >= 2
    assert string_schemas, "the free-text walk saw no string schemas"


def test_schema_has_no_free_text_fields():
    problems = []

    def visit(node, path):
        types = node.get("type")
        type_list = [types] if isinstance(types, str) else list(types or [])
        if "string" in type_list and not any(key in node for key in ("enum", "const", "pattern")):
            problems.append(path)
        pattern = node.get("pattern")
        if isinstance(pattern, str) and pattern in {".*", ".+", "^.*$", "^.*", ".*$", "^.+$", ".+"}:
            problems.append("%s loose pattern %s" % (path, pattern))
        for name, sub in node.get("properties", {}).items():
            if sub == {} or sub is True:
                problems.append("%s.%s unconstrained" % (path, name))

    _walk_schema(SCHEMA, "$", visit)
    assert problems == []
    assert REQUIRED_BANNED <= set(SCHEMA["banned_fields"])
    for name in SCHEMA["banned_fields"]:
        assert SNAKE.fullmatch(name), name


def test_fixture_records_match_the_schema_and_are_synthetic():
    assert FIXTURE["version"] == "0.1"
    assert FIXTURE["status"] == "pending-audrey-confirm"
    assert FIXTURE["synthetic_only_until_confirmed"] is True
    assert FIXTURE["token_seed"] == 1001
    assert len(RECORDS) >= 3
    assert fixture_violations(RECORDS) == []
    present = _dem_synthetic_names()
    for record in RECORDS:
        assert record["case_source"] == "synthetic"
        assert record["location"] == {"label": "predicted"}
        expected_id = "sar/fixtures/dem_synthetic_%s.tif" % record["seed"]
        assert record["fixture_id"] == expected_id
        assert FIXTURE_ID_PATTERN.search(record["fixture_id"])
        if present:
            assert Path(record["fixture_id"]).name in present


def test_tokens_come_from_the_fixed_seed_only():
    issued = case_tokens(len(RECORDS), FIXTURE["token_seed"])
    assert issued == case_tokens(len(RECORDS), 1001)
    assert [record["case_token"] for record in RECORDS] == issued
    for record in RECORDS:
        padded = "%012x" % record["seed"]
        assert padded not in record["case_token"]
        assert record["region_band"].lower() not in record["case_token"].lower()
        assert record["case_token"] != "CT-" + padded


def test_fixture_strings_are_tokens_enums_or_synthetic_paths():
    allowed = {
        FIXTURE["version"],
        FIXTURE["status"],
        "predicted",
        "synthetic",
    }
    for name in ("region_band", "terrain_class", "elapsed_band", "subject_category", "case_source"):
        allowed.update(_enum(name))
    allowed.update(record["case_token"] for record in RECORDS)
    allowed.update(record["fixture_id"] for record in RECORDS)

    def walk(value):
        if isinstance(value, str):
            assert value in allowed, value
        elif isinstance(value, dict):
            for key, item in value.items():
                assert key not in SCHEMA["banned_fields"]
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, bool) or value is None:
            return
        else:
            assert isinstance(value, int) and not isinstance(value, bool)

    walk(FIXTURE)


def test_every_declared_enum_value_is_accepted():
    base = copy.deepcopy(RECORDS[0])
    for name in ("region_band", "terrain_class", "elapsed_band", "subject_category"):
        for value in _enum(name):
            record = copy.deepcopy(base)
            record[name] = value
            _accepted(record)
    _accepted(base)


def test_unknown_enum_values_are_rejected_and_not_coerced():
    base = copy.deepcopy(RECORDS[0])
    samples = {
        "region_band": ["EUROPE", "northeast", "NEW_ENGLAND ", "", "unknown"],
        "terrain_class": ["WOODS", "forest", "UNKNOWN "],
        "elapsed_band": ["E6", "e1", "E1 [1,5)", "E0"],
        "subject_category": ["CHILD", "adult", "HIKER"],
        "case_source": ["real", "SYNTHETIC", "synthetic ", "anonymized"],
    }
    for field, values in samples.items():
        for value in values:
            record = copy.deepcopy(base)
            record[field] = value
            _rejected(record)
            assert record[field] == value
    missing = copy.deepcopy(base)
    del missing["region_band"]
    _rejected(missing)
    assert "region_band" not in missing


def test_bad_case_tokens_are_rejected():
    base = RECORDS[0]["case_token"]
    assert re.fullmatch(r"CT-[0-9a-f]{12}", base)
    bad = [
        base.upper(),
        base[:-1],
        base + "a",
        "ct-" + base[3:],
        "CC-" + base[3:],
        "CT-" + base[3:-1] + "g",
        "CT-" + base[3:].upper(),
        "",
        base + " ",
        " " + base,
    ]
    for token in bad:
        record = copy.deepcopy(RECORDS[0])
        record["case_token"] = token
        _rejected(record)


def test_fixture_id_accepts_both_prefixes_and_rejects_others():
    base = copy.deepcopy(RECORDS[0])
    accepted = (
        "fixtures/dem_synthetic_1001.tif",
        "sar/fixtures/dem_synthetic_1001.tif",
        "fixtures/case_view_synthetic_1001.json",
        "sar/fixtures/case_view_synthetic_1001.json",
    )
    for path in accepted:
        record = copy.deepcopy(base)
        record["fixture_id"] = path
        assert FIXTURE_ID_PATTERN.fullmatch(path)
        _accepted(record)
    rejected = (
        "docs/fixtures/dem_synthetic_1001.tif",
        "blue-ocean-sar/fixtures/dem_synthetic_1001.tif",
        "sar/sar/fixtures/dem_synthetic_1001.tif",
        "/fixtures/dem_synthetic_1001.tif",
        "/sar/fixtures/dem_synthetic_1001.tif",
        "sar/fixtures/../dem_synthetic_1001.tif",
        "fixtures/../dem_synthetic_1001.tif",
        "./fixtures/dem_synthetic_1001.tif",
        "SAR/fixtures/dem_synthetic_1001.tif",
        "sar/other/dem_synthetic_1001.tif",
        "fixtures/dem_1001.tif",
    )
    for path in rejected:
        record = copy.deepcopy(base)
        record["fixture_id"] = path
        assert FIXTURE_ID_PATTERN.fullmatch(path) is None
        _rejected(record)


def test_synthetic_seed_and_fixture_id_are_tied_to_case_source():
    synthetic_null_id = copy.deepcopy(RECORDS[0])
    synthetic_null_id["fixture_id"] = None
    _rejected(synthetic_null_id)

    synthetic_null_seed = copy.deepcopy(RECORDS[0])
    synthetic_null_seed["seed"] = None
    _rejected(synthetic_null_seed)

    negative = copy.deepcopy(RECORDS[0])
    negative["seed"] = -1
    _rejected(negative)

    boolean_seed = copy.deepcopy(RECORDS[0])
    boolean_seed["seed"] = True
    _rejected(boolean_seed)

    outside = copy.deepcopy(RECORDS[0])
    outside["fixture_id"] = "fixtures/../dem_synthetic_1001.tif"
    _rejected(outside)

    unsuffixed = copy.deepcopy(RECORDS[0])
    unsuffixed["fixture_id"] = "fixtures/dem_1001.tif"
    _rejected(unsuffixed)

    real = copy.deepcopy(RECORDS[0])
    real["case_source"] = "real_anonymized"
    real["fixture_id"] = None
    real["seed"] = None
    _accepted(real)
    assert fixture_violations([real])

    real_with_seed = copy.deepcopy(real)
    real_with_seed["seed"] = 1001
    _rejected(real_with_seed)

    real_with_path = copy.deepcopy(real)
    real_with_path["fixture_id"] = "fixtures/dem_synthetic_1001.tif"
    _rejected(real_with_path)


def test_extra_and_banned_keys_are_rejected():
    extra = copy.deepcopy(RECORDS[0])
    extra["comment"] = "synthetic"
    _rejected(extra)
    for key in sorted(SCHEMA["banned_fields"]):
        record = copy.deepcopy(RECORDS[0])
        record[key] = "not-a-coordinate"
        _rejected(record)
        nested = copy.deepcopy(RECORDS[0])
        nested["location"][key] = "not-a-coordinate"
        _rejected(nested)


def test_location_must_carry_the_predicted_label():
    missing_label = copy.deepcopy(RECORDS[0])
    del missing_label["location"]["label"]
    _rejected(missing_label)

    observed = copy.deepcopy(RECORDS[0])
    observed["location"]["label"] = "observed"
    _rejected(observed)

    wrong_case = copy.deepcopy(RECORDS[0])
    wrong_case["location"]["label"] = "PREDICTED"
    _rejected(wrong_case)

    absent = copy.deepcopy(RECORDS[0])
    del absent["location"]
    _rejected(absent)

    empty = copy.deepcopy(RECORDS[0])
    empty["location"] = None
    _rejected(empty)

    with_band = copy.deepcopy(RECORDS[0])
    with_band["location"]["region_band"] = "PACIFIC"
    _rejected(with_band)


SENTINEL = "ZZ_SENTINEL_7f3a"
CLOSED_KEYS = ("geometry", "geohash", "bbox", "lat", "lon", "date", "last_seen_date")
ERROR_TEXT = re.compile(r"^[^:\n]+: [a-z_]+$")


def _object_paths(value, prefix=()):
    found = []
    if isinstance(value, dict):
        found.append(prefix)
        for key, item in value.items():
            found.extend(_object_paths(item, prefix + (key,)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_object_paths(item, prefix + (index,)))
    return found


def _at(record, path):
    cursor = record
    for part in path:
        cursor = cursor[part]
    return cursor


def test_closed_allowlist_rejects_geo_and_date_keys_on_every_object():
    paths = _object_paths(RECORDS[0])
    assert len(paths) >= 2
    for key in CLOSED_KEYS:
        assert key not in SCHEMA["properties"]
        assert key not in SCHEMA["$defs"]["predicted_location"]["properties"]
        for path in paths:
            record = copy.deepcopy(RECORDS[0])
            _at(record, path)[key] = True
            _rejected(record)


def test_seed_string_float_and_bool_are_rejected_not_coerced():
    samples = ("1001", 1001.0, 1001.5, True, False)
    for value in samples:
        record = copy.deepcopy(RECORDS[0])
        record["seed"] = value
        _rejected(record)
        assert record["seed"] == value
        assert type(record["seed"]) is type(value)


def test_pattern_anchors_reject_affixes_and_newlines():
    token = RECORDS[0]["case_token"]
    fixture_id = RECORDS[0]["fixture_id"]
    samples = (
        ("case_token", "x" + token),
        ("case_token", token + "x"),
        ("case_token", token + "a"),
        ("case_token", token + "\n"),
        ("case_token", "\n" + token),
        ("case_token", token[:6] + "\n" + token[6:]),
        ("fixture_id", "x" + fixture_id),
        ("fixture_id", fixture_id + "/"),
        ("fixture_id", fixture_id + " "),
        ("fixture_id", fixture_id + "\n"),
        ("fixture_id", "\n" + fixture_id),
        ("fixture_id", fixture_id[:8] + "\n" + fixture_id[8:]),
    )
    for field, value in samples:
        record = copy.deepcopy(RECORDS[0])
        record[field] = value
        errors = validate(record, SCHEMA)
        assert errors
        blob = "\n".join(errors)
        assert value not in blob
        assert record[field] == value
        for line in errors:
            assert ERROR_TEXT.fullmatch(line)


def test_errors_do_not_echo_a_sentinel_value():
    digest = hashlib.sha256(SENTINEL.encode("utf-8")).hexdigest()
    mutations = []
    for field in (
        "case_token",
        "region_band",
        "terrain_class",
        "elapsed_band",
        "subject_category",
        "case_source",
        "fixture_id",
        "seed",
    ):
        record = copy.deepcopy(RECORDS[0])
        record[field] = SENTINEL
        mutations.append(record)
    labelled = copy.deepcopy(RECORDS[0])
    labelled["location"]["label"] = SENTINEL
    mutations.append(labelled)
    for key_path in ((), ("location",)):
        record = copy.deepcopy(RECORDS[0])
        _at(record, key_path)[SENTINEL] = True
        mutations.append(record)
        record = copy.deepcopy(RECORDS[0])
        _at(record, key_path)["geometry"] = SENTINEL
        mutations.append(record)

    seen = 0
    for record in mutations:
        try:
            errors = validate(record, SCHEMA)
            violations = fixture_violations([record])
        except Exception as exc:
            text = str(exc)
            assert SENTINEL not in text
            assert digest not in text
            raise
        blob = "\n".join(errors + violations)
        assert errors
        assert SENTINEL not in blob
        assert digest not in blob
        for line in errors:
            assert ERROR_TEXT.fullmatch(line)
        seen += 1
    assert seen == len(mutations)
