"""Verify the River setup end to end: key -> connection -> models -> a sample.

Run this first. If it prints a completion at the bottom, everything works.

    uv run --project river river/check_setup.py
"""

import sys

import river_client as river

from _bootstrap import explain, get_api_key

PREFERRED = "Qwen/Qwen3.6-35B-A3B-FP8"


def main() -> int:
    key = get_api_key()
    print(f"1. API key found (ends in ...{key[-4:]})")

    client = river.Client(api_key=key)

    # health_check() only proves the server is reachable — it does not
    # validate the key. get_capabilities() below is what actually authenticates.
    try:
        healthy = client.health_check()
    except river.RiverConnectionError as exc:
        print(f"\n   {explain(exc)}")
        return 1
    print(f"2. Server reachable, healthy: {healthy}")

    try:
        models = list(client.get_capabilities())
    except river.RiverConnectionError as exc:
        print(f"\n   {explain(exc)}")
        return 1

    if not models:
        print("\n   Key is valid, but no models are enabled for it.")
        print("   Request access at support@river.ai or on Discord.")
        return 1

    print(f"3. Key accepted. Models enabled for it ({len(models)}):")
    for name in models:
        print(f"      {name}")

    base = PREFERRED if PREFERRED in models else models[0]
    print(f"\n4. Sampling from {base} ...")
    try:
        samples = client.sample(
            "What is 2 + 2? Answer briefly.", base_model=base, max_tokens=24
        )
    except river.RiverConnectionError as exc:
        print(f"\n   {explain(exc)}")
        return 1
    print(f"   -> {samples[0].text!r}")

    print("\nSetup is working.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
