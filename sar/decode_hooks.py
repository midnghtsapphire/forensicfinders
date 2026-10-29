# ═══════════════════════════════════════════════════════════════════════════════════════
# DECODE SEAM (decode_hooks)
# Who: Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
# When: 2026-10-24
# Why: Corrections that belong to the sensor (clock/geolocation, radiometry, speckle,
#      polarimetric unmixing) were being applied -- where they were applied at all --
#      scattered across each consumer, after the array had already been handed around.
#      Audrey's design decision is to condition the data once, at the point where bytes
#      become an array, so every downstream consumer inherits the same corrected values
#      and no consumer can quietly skip a correction.
# What: NEW FILE. A registry of decode hooks plus apply(). Nothing registers a hook by
#       default, so apply() is the identity function and behaviour is unchanged until
#       somebody deliberately registers one.
# Notes: This is NOT the NSR injector from the GIS Server Technical Reference (PDF 1.1-1.3).
#        That one conditions raw complex IQ before geocoding. This repository never sees
#        raw IQ -- it fetches Sentinel-1 GRD, Sentinel-2 L2A and discrete-return LAS, all
#        of which are already compressed, geocoded and resampled. This seam is the place
#        such an injector WOULD attach if a raw-product fetch path is added later; it is
#        not a substitute for one, and must not be described as one.
# ═══════════════════════════════════════════════════════════════════════════════════════
"""Single conditioning point for decoded sensor data.

A hook is any callable ``fn(payload, meta) -> payload``:

  payload  whatever the decoder produced -- a numpy array for rasters, a list of
           tuples for point clouds, a list of lists for GPR traces. Hooks may change
           the value and may change its shape (a two-channel IQ array legitimately
           becomes one power channel), but must return something the caller's
           documented return type permits.
  meta     a dict describing where the payload came from (see the callers for the
           keys each one sets). apply() appends the name of every hook it ran to
           ``meta["decode_hooks_applied"]`` so the caller holds a receipt of what
           actually touched the data rather than an assertion that something did.

Why a registry and not a parameter: the point of conditioning at decode is that a
consumer cannot opt out by forgetting to thread an argument through. Registration
happens once, at the top of a run.

Troubleshooting: if results change unexpectedly, call ``registered()`` -- it lists
what is installed, in the order it runs. An empty list means this module changed
nothing and the problem is elsewhere.
"""

# Ordered list of (name, callable, decoders). A list, not a dict, because order is part
# of the contract: a despeckle hook registered after a calibration hook must run after it.
_HOOKS = []

# The decoder names this module knows about. meta["decoder"] is set by each caller before
# it calls apply(); register(decoders=...) is matched against that value. Kept here as a
# plain tuple so a typo in a register() call can be caught instead of silently never
# matching -- a hook that never runs is the quietest failure in this file.
KNOWN_DECODERS = ("read_cog_window", "read_points", "read_gpr_csv")


class DecodeHookError(RuntimeError):
    """A registered hook raised. Carries the hook name so the failure is attributable."""


def register(name, fn, decoders=None):
    """Install a hook under `name`, replacing any hook already using that name.

    `decoders` scopes the hook to particular decode points, by the names in
    KNOWN_DECODERS. THIS MATTERS: the payload type differs per decoder -- a numpy
    array from read_cog_window, a list of (x, y, z, i) tuples from read_points, a list
    of lists from read_gpr_csv. A hook written for one and left unscoped will be handed
    the others and will either crash or, worse, silently do something meaningless to
    them. Scope every hook that assumes a payload type.

    Leaving `decoders` as None runs the hook at every decode point. That is correct for
    type-agnostic hooks only -- provenance stamping, logging, counting -- and wrong for
    anything that touches values.

    Replacing rather than appending is deliberate: registering twice under one name
    (an import that runs more than once, a notebook cell re-executed) would otherwise
    apply the same correction twice and silently double it.
    """
    if not callable(fn):
        raise TypeError(f"decode hook {name!r} is not callable")
    if decoders is not None:
        decoders = frozenset(decoders)
        unknown = decoders - frozenset(KNOWN_DECODERS)
        if unknown:
            raise ValueError(
                f"decode hook {name!r} scoped to unknown decoder(s) {sorted(unknown)}; "
                f"known decoders are {list(KNOWN_DECODERS)}")
    for i, (existing, _, _) in enumerate(_HOOKS):
        if existing == name:
            _HOOKS[i] = (name, fn, decoders)
            return
    _HOOKS.append((name, fn, decoders))


def unregister(name):
    """Remove a hook. Returns True if one was removed, False if it was not installed."""
    before = len(_HOOKS)
    _HOOKS[:] = [h for h in _HOOKS if h[0] != name]
    return len(_HOOKS) != before


def clear():
    """Remove every hook. Tests use this to guarantee a known-empty starting state."""
    _HOOKS.clear()


def registered(decoder=None):
    """Names of installed hooks, in the order apply() will run them.

    Pass a decoder name to list only the hooks that would run at that decode point --
    the quickest way to answer "why did this hook not fire?".
    """
    return [n for n, _, d in _HOOKS if decoder is None or d is None or decoder in d]


def apply(payload, meta=None):
    """Run the hooks registered for this decoder over `payload`, in registration order.

    Which hooks are "due" is decided by meta["decoder"] against each hook's scope (see
    register()). A hook scoped to another decoder is skipped silently and is NOT named in
    the receipt -- the receipt records what ran, not what was installed.

    With no due hooks this returns `payload` unchanged and does not touch `meta`, which
    is what makes installing the seam a no-op until someone opts in.

    A hook that raises aborts the decode -- it is NOT skipped. A skipped correction
    would hand back data that looks conditioned and is not, and the caller has no way
    to tell the difference. Per standards/VERIFY_THE_POSTCONDITION.md an unverifiable
    claim of correctness is worse than a visible failure, so this fails loudly instead.
    What to check first: the DecodeHookError names the hook; run that hook directly on
    the same payload, and use registered() to confirm nothing else is installed ahead
    of it that changed the payload's type before it arrived.
    """
    if not _HOOKS:
        return payload
    if meta is None:
        meta = {}
    decoder = meta.get("decoder")
    due = [(n, f) for n, f, d in _HOOKS if d is None or decoder in d]
    if not due:
        return payload
    applied = meta.setdefault("decode_hooks_applied", [])
    for name, fn in due:
        try:
            payload = fn(payload, meta)
        except Exception as e:
            raise DecodeHookError(f"decode hook {name!r} failed: {type(e).__name__}: {e}") from e
        applied.append(name)
    return payload
