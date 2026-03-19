#!/usr/bin/env python3
"""Plugin template entrypoint."""
import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser(description="Plugin template")
    parser.add_argument("--target", required=True, help="Target")
    parser.add_argument("--params", help="JSON params")

    args = parser.parse_args()

    params = {}
    if args.params:
        params = json.loads(args.params)

    result = {
        "target": args.target,
        "param1": params.get("param1", "default"),
        "results": [],
        "exit_code": 0,
    }

    print(json.dumps(result, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
