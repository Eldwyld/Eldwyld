"""Shared setup for the River scripts: find the API key, build a client.

Every script here imports `get_client()` from this module so there is exactly
one place that knows how the key is loaded.
"""

import os
import sys
from pathlib import Path

import river_client as river

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv is optional; env vars still work without it.
    load_dotenv = None


def get_api_key() -> str:
    """Read RIVER_API_KEY from the environment, falling back to a local .env file.

    Exits with a readable message instead of a traceback if the key is missing.
    """
    if load_dotenv is not None:
        load_dotenv(Path(__file__).parent / ".env")

    key = os.environ.get("RIVER_API_KEY", "").strip()
    if not key:
        sys.exit(
            "RIVER_API_KEY is not set.\n\n"
            "Set it one of two ways:\n"
            "  1. export RIVER_API_KEY='rv_...'\n"
            "  2. cp .env.example .env  and paste your key into it\n"
        )
    if not key.startswith("rv_"):
        print(
            f"warning: RIVER_API_KEY does not start with 'rv_' (starts with "
            f"{key[:3]!r}) — double-check you copied the whole key.",
            file=sys.stderr,
        )
    return key


def get_client() -> river.Client:
    return river.Client(api_key=get_api_key())


def explain(exc: river.RiverConnectionError) -> str:
    """Turn a gRPC-shaped error into a next step."""
    hints = {
        "UNAUTHENTICATED":
            "The server rejected your key. Check it on the API Keys page of the\n"
            "console — make sure you copied the whole thing, including the 'rv_' prefix.",
        "PERMISSION_DENIED":
            "Your key is valid but lacks access here. Ask about it at support@river.ai.",
        "UNAVAILABLE":
            "Could not reach api.river.ai. Check your network connection or proxy.",
        "DEADLINE_EXCEEDED":
            "The request timed out. The server may be busy — try again shortly.",
    }
    hint = hints.get(exc.status_code or "", "")
    return f"{exc}\n\n{hint}" if hint else str(exc)


def pick_base_model(client: river.Client, preferred: str | None = None) -> str:
    """Return a base model this key can actually use.

    `get_capabilities()` is scoped to your account, so hard-coding a model name
    can fail even when the name is valid in the public catalog. Prefer the
    requested model if it is available, otherwise fall back to the first one.
    """
    try:
        available = list(client.get_capabilities())
    except river.RiverConnectionError as exc:
        sys.exit(explain(exc))

    if not available:
        sys.exit("This API key has no models enabled. Contact support@river.ai.")

    if preferred and preferred in available:
        return preferred
    if preferred:
        print(
            f"note: {preferred!r} is not enabled for this key; "
            f"using {available[0]!r} instead.",
            file=sys.stderr,
        )
    return available[0]
