#!/usr/bin/env python3
"""Generate the local .env file for the secrets demo."""

import argparse
import os
import sys
from pathlib import Path

DEFAULT_CLIENT_SECRET = "foobar"
ENV_PATH = Path(__file__).resolve().parent / ".env"


def main():
    parser = argparse.ArgumentParser(
        description="Generate .env for the my-collection-secrets Bruno demo."
    )
    parser.add_argument(
        "--client-secret",
        help=(
            "OAuth client secret. Defaults to $OAUTH_CLIENT_SECRET, "
            f"then to the demo value {DEFAULT_CLIENT_SECRET!r}."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite .env if it already exists.",
    )
    args = parser.parse_args()

    if args.client_secret is not None:
        secret = args.client_secret
        source = "--client-secret"
    elif os.environ.get("OAUTH_CLIENT_SECRET"):
        secret = os.environ["OAUTH_CLIENT_SECRET"]
        source = "OAUTH_CLIENT_SECRET"
    else:
        secret = DEFAULT_CLIENT_SECRET
        source = "built-in demo default"

    secret = secret.strip()
    if not secret:
        parser.error("the client secret cannot be empty")
    if "\n" in secret or "\r" in secret:
        parser.error("the client secret cannot contain a newline")

    if ENV_PATH.exists() and not args.force:
        print(f"{ENV_PATH} already exists. Use --force to overwrite it.", file=sys.stderr)
        return 1

    ENV_PATH.write_text(f"OAUTH_CLIENT_SECRET={secret}\n", encoding="utf-8")
    try:
        ENV_PATH.chmod(0o600)
    except OSError:
        pass

    print(f"Wrote {ENV_PATH} using {source}.")
    print("Select the dotenv environment in Bruno.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
