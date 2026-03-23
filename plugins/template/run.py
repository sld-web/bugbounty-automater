#!/usr/bin/env python3
"""Example authenticated plugin using the SDK."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sdk import BasePlugin, run_plugin


class AuthenticatedNucleiPlugin(BasePlugin):
    """Example plugin that uses credentials for authenticated scanning."""

    def get_name(self) -> str:
        return "authenticated-nuclei"

    def get_version(self) -> str:
        return "1.0.0"

    def get_inputs(self) -> dict:
        return {
            "target": {"type": "string", "required": True},
            "credential_id": {"type": "string", "required": False},
            "templates": {"type": "string", "required": False},
        }

    def get_outputs(self) -> dict:
        return {
            "findings": {"type": "array"},
            "authenticated": {"type": "boolean"},
        }

    def run(self, target: str, params: dict) -> dict:
        import subprocess
        import json

        credential_id = params.get("credential_id")
        templates = params.get("templates", "templates")
        
        cmd = [
            "nuclei",
            "-u", target,
            "-json",
            "-o", "/tmp/nuclei_results.jsonl",
        ]

        authenticated = False
        if credential_id:
            cred = self.get_credential(
                credential_id=credential_id,
                target_id=target,
                purpose="Authenticated vulnerability scanning",
            )
            
            if cred and cred.get("api_key"):
                os.environ["NUCLEI_API_KEY"] = cred["api_key"]
                authenticated = True

        print(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,
            )

            findings = []
            if result.returncode in (0, 1):
                try:
                    with open("/tmp/nuclei_results.jsonl") as f:
                        for line in f:
                            findings.append(json.loads(line.strip()))
                except Exception:
                    pass

            return {
                "findings": findings,
                "authenticated": authenticated,
                "exit_code": result.returncode,
            }
        except Exception as e:
            return {
                "findings": [],
                "authenticated": authenticated,
                "error": str(e),
            }


if __name__ == "__main__":
    run_plugin(AuthenticatedNucleiPlugin)
