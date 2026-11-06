"""Stdlib validator for the anonymized case-view contract (schema 0.1).

The contract file is JSON Schema draft 2020-12. This module checks the subset
that file uses: $ref, type, const, enum, pattern, minimum, properties,
required, additionalProperties false, oneOf, and if/then/else. Unknown schema
keywords are ignored, matching a standard validator. Instance values that fail
an enum or a pattern are rejected and left unchanged.
"""
import copy
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
FIXTURE_ID_PATTERN = re.compile(r"^fixtures/[A-Za-z0-9._-]*synthetic[A-Za-z0-9._-]*$")
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


def _deref(root, ref):
    if not isinstance(ref, str) or not ref.startswith("#/"):
        raise SchemaError("unsupported $ref: %r" % (ref,))
    node = root
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or part not in node:
            raise SchemaError("unresolved $ref %s" % ref)
        node = node[part]
    return node


def _is_type(instance, name):
    if name == "null":
        return instance is None
    if name == "boolean":
        return isinstance(instance, bool)
    if name == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if name == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if name == "string":
        return isinstance(instance, str)
    if name == "object":
        return isinstance(instance, dict)
    if name == "array":
        return isinstance(instance, list)
    raise SchemaError("unsupported type %r" % (name,))


def validate(instance, schema, root=None, path="$"):
    """Return a list of violations. An empty list means the instance matches."""
    if root is None:
        root = schema
    if not isinstance(schema, dict):
        raise SchemaError("schema node at %s is not an object" % path)
    if "$ref" in schema:
        if set(schema) != {"$ref"}:
            raise SchemaError("$ref siblings are not used (%s)" % path)
        return validate(instance, _deref(root, schema["$ref"]), root, path)

    errors = []
    if "const" in schema and instance != schema["const"]:
        errors.append("%s: expected const %r" % (path, schema["const"]))
    if "enum" in schema and instance not in schema["enum"]:
        errors.append("%s: %r is not an allowed value" % (path, instance))

    if "type" in schema:
        types = schema["type"]
        type_list = [types] if isinstance(types, str) else list(types)
        if not any(_is_type(instance, item) for item in type_list):
            errors.append("%s: type %s is not %s" % (path, type(instance).__name__, types))
            return errors

    if "pattern" in schema:
        pattern = schema["pattern"]
        if not isinstance(instance, str) or re.search(pattern, instance) is None:
            errors.append("%s: does not match %s" % (path, pattern))

    if "minimum" in schema:
        if not _is_type(instance, "integer") or instance < schema["minimum"]:
            errors.append("%s: below minimum %r" % (path, schema["minimum"]))

    if "oneOf" in schema:
        matched = 0
        branch_errors = []
        for index, branch in enumerate(schema["oneOf"]):
            branch_result = validate(instance, branch, root, "%s oneOf[%d]" % (path, index))
            if branch_result:
                branch_errors.extend(branch_result)
            else:
                matched += 1
        if matched != 1:
            errors.append("%s: oneOf matched %d" % (path, matched))
            errors.extend(branch_errors)

    if "properties" in schema or "required" in schema or schema.get("type") == "object":
        if not isinstance(instance, dict):
            errors.append("%s: expected an object" % path)
            return errors
        props = schema.get("properties", {})
        for key in schema.get("required", ()):
            if key not in instance:
                errors.append("%s: missing required %s" % (path, key))
        additional = schema.get("additionalProperties", True)
        if additional is False:
            for key in instance:
                if key not in props:
                    errors.append("%s: additional property %r" % (path, key))
        elif additional is not True:
            raise SchemaError("additionalProperties schemas are not used")
        for key, sub in props.items():
            if key in instance:
                errors.extend(validate(instance[key], sub, root, "%s.%s" % (path, key)))

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
            violations.append(
                "record[%d]: fixture case_source must be synthetic, got %r"
                % (index, record.get("case_source"))
            )
    return violations


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
    assert SCHEMA["synthetic_only_until_confirmed"] is True
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
    assert SCHEMA["terrain_policy"]["fixture_template"] == "fixtures/dem_synthetic_<seed>.tif"
    assert SCHEMA["$defs"]["case_token"]["pattern"] == "^CT-[0-9a-f]{12}$"


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
        expected_id = "fixtures/dem_synthetic_%s.tif" % record["seed"]
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
