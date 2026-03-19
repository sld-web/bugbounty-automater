#!/usr/bin/env python3
"""httpx plugin entrypoint."""
import argparse
import json
import subprocess
import sys


def run_httpx(
    target: str,
    screenshots: bool = False,
    technologies: bool = True,
    threads: int = 50,
) -> dict:
    """Run httpx HTTP probing."""
    output_file = "/tmp/httpx_results.jsonl"
    cmd = [
        "httpx",
        "-l", target,
        "-json", "-o", output_file,
        "-threads", str(threads),
    ]

    if screenshots:
        cmd.append("-screenshot")
    if technologies:
        cmd.append("-technologys")

    print(f"Running: {' '.join(cmd)}")

    endpoints = []
    techs = set()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1200,
        )

        if result.returncode in (0, 1) and sys.path.exists(output_file):
            with open(output_file) as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        endpoint = {
                            "url": data.get("url"),
                            "status_code": data.get("status_code"),
                            "content_length": data.get("content_length"),
                            "content_type": data.get("content_type"),
                            "title": data.get("title"),
                            "server": data.get("server"),
                            "webserver": data.get("webserver"),
                        }
                        endpoints.append(endpoint)

                        if "technologies" in data:
                            for tech in data["technologies"]:
                                techs.add(tech)

                    except json.JSONDecodeError:
                        continue

        return {
            "endpoints": endpoints,
            "technologies": list(techs),
            "count": len(endpoints),
            "stdout": result.stdout[:5000],
            "stderr": result.stderr[:2000],
            "exit_code": result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {
            "endpoints": [],
            "technologies": [],
            "error": "httpx timed out",
            "exit_code": -1,
        }
    except Exception as e:
        return {
            "endpoints": [],
            "technologies": [],
            "error": str(e),
            "exit_code": -1,
        }


def main():
    parser = argparse.ArgumentParser(description="httpx HTTP probing")
    parser.add_argument("--target", required=True, help="Target file or URL")
    parser.add_argument("--screenshots", action="store_true", help="Take screenshots")
    parser.add_argument("--technologies", action="store_true", default=True, help="Detect technologies")
    parser.add_argument("--threads", type=int, default=50, help="Number of threads")
    parser.add_argument("--params", help="JSON params")

    args = parser.parse_args()

    params = {}
    if args.params:
        params = json.loads(args.params)

    result = run_httpx(
        target=args.target,
        screenshots=args.screenshots or params.get("screenshots", False),
        technologies=args.technologies or params.get("technologies", True),
        threads=args.threads or params.get("threads", 50),
    )

    print(json.dumps(result, indent=2))
    sys.exit(result.get("exit_code", 0))


if __name__ == "__main__":
    main()
