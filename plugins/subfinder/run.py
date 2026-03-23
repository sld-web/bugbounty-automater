#!/usr/bin/env python3
"""Subfinder plugin entrypoint."""
import argparse
import json
import os
import subprocess
import sys
import socket


FREE_SOURCES = ["alienvault", "anubis", "bufferover", "certspotter", "commoncrawl", "crtsh", "digitorus", "dnsdumpster", "hackertarget", "rapiddns", "sitedossier", "waybackarchive"]


def run_subfinder(
    target: str,
    sources: list[str] | None = None,
    use_all: bool = False,
) -> dict:
    """Run Subfinder subdomain discovery."""
    output_file = "/tmp/subfinder_results.txt"
    cmd = [
        "subfinder",
        "-d", target,
        "-o", output_file,
        "-silent",
    ]

    if use_all:
        cmd.append("-all")
    elif sources:
        cmd.extend(["-sources", ",".join(sources)])
    else:
        cmd.extend(["-sources", ",".join(FREE_SOURCES)])

    print(f"Running: {' '.join(cmd)}")
    sys.stdout.flush()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )

        subdomains = []
        if result.returncode == 0:
            if os.path.exists(output_file):
                with open(output_file) as f:
                    subdomains = [line.strip() for line in f if line.strip()]
            elif result.stdout.strip():
                subdomains = [line.strip() for line in result.stdout.split('\n') if line.strip()]

        return {
            "subdomains": list(set(subdomains)),
            "count": len(subdomains),
            "raw_output": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "sources_used": sources or FREE_SOURCES,
        }

    except subprocess.TimeoutExpired:
        return {
            "subdomains": [],
            "error": "Subfinder timed out after 300 seconds",
            "exit_code": -1,
        }
    except Exception as e:
        return {
            "subdomains": [],
            "error": str(e),
            "exit_code": -1,
        }


def resolve_subdomains(subdomains: list[str]) -> dict:
    """Resolve subdomains to IP addresses."""
    resolved = {}
    for subdomain in subdomains:
        try:
            ip = socket.gethostbyname(subdomain)
            resolved[subdomain] = ip
        except socket.gaierror:
            pass
    return resolved


def main():
    parser = argparse.ArgumentParser(description="Subfinder subdomain discovery")
    parser.add_argument("--target", required=True, help="Target domain")
    parser.add_argument("--sources", nargs="+", help="Specific sources")
    parser.add_argument("--all", action="store_true", default=False, help="Use all sources")
    parser.add_argument("--params", help="JSON params")

    args = parser.parse_args()

    params = {}
    if args.params:
        params = json.loads(args.params)

    result = run_subfinder(
        target=args.target,
        sources=args.sources or params.get("sources"),
        use_all=args.all or params.get("all", False),
    )
    
    if result.get("subdomains"):
        result["resolved"] = resolve_subdomains(result["subdomains"])
        result["resolved_count"] = len(result.get("resolved", {}))

    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("subdomains") else 1)


if __name__ == "__main__":
    main()
