from __future__ import annotations

import argparse
import json
import sys
from urllib.error import URLError
from urllib.request import urlopen


def _fetch_json(url: str) -> dict:
    with urlopen(url, timeout=10) as response:  # nosec B310
        payload = response.read().decode("utf-8")
        return json.loads(payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Arc Reactor smoke test")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL for the deployment",
    )
    args = parser.parse_args()

    try:
        health = _fetch_json(f"{args.base_url}/health")
        ready = _fetch_json(f"{args.base_url}/ready")
    except URLError as exc:
        print(f"Request failed: {exc}")
        return 1

    print("Health:", health)
    print("Ready:", ready)

    if not ready.get("healthy"):
        print("Readiness check failed")
        return 1

    if ready.get("degraded"):
        print("Warning: service is degraded")

    return 0


if __name__ == "__main__":
    sys.exit(main())
