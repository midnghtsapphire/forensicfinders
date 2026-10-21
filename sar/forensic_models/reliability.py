"""Deterministic source-reliability / information-credibility grading (NATO Admiralty code, A-F / 1-6).
Rubric (documented in reliability_rubric.json) is a lookup table, not keyword guessing:
  reliability letter = TABLE[source_type][provenance], then capped by chain of custody
  credibility number = from independent corroboration count and contradiction flag
Rubric reference: NATO AJP-2.1 / STANAG 2511 (source reliability A-F, information credibility 1-6);
the specific mapping of source types to letters is Audrey's documented house rubric, versioned in the JSON."""
import json
from pathlib import Path

RUBRIC = json.loads(Path(__file__).with_name("reliability_rubric.json").read_text())
ORDER = "ABCDEF"


def grade(source_type, provenance, custody, corroborations, contradicted=False, consistent=None, rubric=RUBRIC):
    """consistent: True/False/None = information consistent with established facts / not / not assessed."""
    st = rubric["source_types"].get(source_type)
    if st is None:
        raise KeyError(f"unknown source_type {source_type!r}; one of {sorted(rubric['source_types'])}")
    if provenance not in st:
        raise KeyError(f"unknown provenance {provenance!r} for {source_type}; one of {sorted(st)}")
    if custody not in rubric["custody_cap"]:
        raise KeyError(f"unknown custody {custody!r}; one of {sorted(rubric['custody_cap'])}")
    n = int(corroborations)
    if n < 0:
        raise ValueError("corroborations must be >= 0")
    letter = max(st[provenance], rubric["custody_cap"][custody], key=ORDER.index)  # custody can only lower
    c = rubric["credibility_rules"]
    if contradicted:
        number = c["contradicted"]
    elif n >= c["confirmed_min_independent"]:
        number = 1
    elif n >= 1:
        number = 2
    else:
        number = {True: 3, False: 4, None: 6}[consistent]
    return {"grade": f"{letter}{number}", "reliability": letter, "credibility": number,
            "reliability_label": rubric["labels"]["reliability"][letter],
            "credibility_label": rubric["labels"]["credibility"][str(number)],
            "rubric_version": rubric["version"]}
