"""Seed script for sample bug bounty programs."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import async_session_maker
from app.models.program import Program
from app.models.target import Target, TargetStatus, TargetType
from app.models.finding import Finding, Severity, FindingStatus


ETERNAL_CONFIG = {
    "name": "Eternal (Zomato/Blinkit)",
    "platform": "hackerone",
    "url": "https://hackerone.com/eternal",
    "scope_domains": [
        "*.zomato.com",
        "*.blinkit.com",
        "*.blinkit.in",
        "*.zomatocom.com",
    ],
    "scope_excluded": [
        "*.slotobucks.slotomania.com",
        "*.test.zomato.com",
        "*.staging.zomato.com",
    ],
    "priority_areas": [
        "subdomain_takeover",
        "public_s3_bucket",
        "api_security",
        "payment_bypass",
    ],
    "out_of_scope": [
        "google_maps_api_key_exposure",
        "denial_of_service",
        "open_redirect_unless_phishing_risk",
    ],
    "severity_mapping": {
        "critical": ["remote_code_execution", "sql_injection_with_pii"],
        "high": ["stored_xss_with_httponly", "broken_authentication"],
        "medium": ["idor", "ssrf", "open_redirect"],
        "low": ["information_disclosure", "missing_security_headers"],
    },
    "reward_tiers": {
        "critical": [5000, 10000],
        "high": [1000, 5000],
        "medium": [500, 1500],
        "low": [100, 500],
    },
    "campaigns": [
        {
            "name": "Cloud Infrastructure",
            "multiplier": 1.5,
            "applies_to": ["cloud_findings"],
            "end_date": "2026-04-07",
        }
    ],
}

X_CONFIG = {
    "name": "X (Twitter)",
    "platform": "bugcrowd",
    "url": "https://bugcrowd.com/x",
    "scope_domains": [
        "*.x.com",
        "*.twitter.com",
        "*.twttr.net",
    ],
    "scope_excluded": [
        "ads.twitter.com",
        "business.twitter.com",
    ],
    "priority_areas": [
        "account_takeover",
        "data_exposure",
        "oauth_vulnerabilities",
        "dm_security",
    ],
    "out_of_scope": [
        "self_xss",
        "tabnapping",
        "minor_ui_bugs",
    ],
    "severity_mapping": {
        "critical": ["account_takeover", "data_breach"],
        "high": ["xss_stored", "csrf_critical"],
        "medium": ["idor_dm", "ssrf_internal"],
        "low": ["open_redirect", "self_xss"],
    },
    "reward_tiers": {
        "critical": [25000, 50000],
        "high": [7500, 25000],
        "medium": [2500, 7500],
        "low": [500, 2500],
    },
}

PAYPAL_CONFIG = {
    "name": "PayPal",
    "platform": "bugcrowd",
    "url": "https://bugcrowd.com/paypal",
    "scope_domains": [
        "*.paypal.com",
        "*.paypal.me",
        "*.braintreeapi.com",
        "*.venmo.com",
    ],
    "scope_excluded": [
        "*.paypal-communication.com",
        "history.paypal.com",
    ],
    "priority_areas": [
        "payment_bypass",
        "account_takeover",
        "xss_stored",
        "oauth_flaws",
    ],
    "out_of_scope": [
        "self_dos",
        "clickjacking_low_impact",
        "missing_csp",
    ],
    "severity_mapping": {
        "critical": ["payment_bypass", "rce"],
        "high": ["sqli", "auth_bypass"],
        "medium": ["xss_stored", "csrf"],
        "low": ["open_redirect", "info_disclosure"],
    },
    "reward_tiers": {
        "critical": [10000, 50000],
        "high": [2500, 10000],
        "medium": [500, 2500],
        "low": [100, 500],
    },
}


async def seed_programs():
    """Seed the database with sample programs."""
    async with async_session_maker() as session:
        existing = await session.execute(
            "SELECT name FROM programs WHERE name IN (:names)",
            {"names": ["Eternal (Zomato/Blinkit)", "X (Twitter)", "PayPal"]}
        )
        if existing.fetchone():
            print("Programs already exist, skipping seed.")
            return

        programs_data = [ETERNAL_CONFIG, X_CONFIG, PAYPAL_CONFIG]

        for data in programs_data:
            campaigns = data.pop("campaigns", [])
            program = Program(**data, campaigns=campaigns)
            session.add(program)

        await session.commit()
        print("Seeded 3 programs: Eternal, X, PayPal")


async def seed_sample_targets():
    """Seed sample targets for testing."""
    async with async_session_maker() as session:
        result = await session.execute(
            "SELECT id, name FROM programs LIMIT 1"
        )
        program = result.fetchone()
        if not program:
            print("No programs found, skipping targets.")
            return

        targets = [
            Target(
                name="zomato.com",
                target_type=TargetType.DOMAIN,
                status=TargetStatus.PENDING,
                program_id=program[0],
                subdomains=["api.zomato.com", "www.zomato.com"],
            ),
            Target(
                name="blinkit.com",
                target_type=TargetType.DOMAIN,
                status=TargetStatus.PENDING,
                program_id=program[0],
                subdomains=["api.blinkit.com"],
            ),
        ]

        for target in targets:
            session.add(target)

        await session.commit()
        print("Seeded 2 sample targets")


async def seed_sample_findings():
    """Seed sample findings for testing."""
    async with async_session_maker() as session:
        result = await session.execute(
            "SELECT id FROM targets LIMIT 1"
        )
        target = result.fetchone()
        if not target:
            print("No targets found, skipping findings.")
            return

        findings = [
            Finding(
                title="Open Redirect in Login Flow",
                description="The login endpoint redirects to arbitrary URLs",
                severity=Severity.MEDIUM,
                status=FindingStatus.NEW,
                target_id=target[0],
                vuln_type="open_redirect",
                affected_url="https://zomato.com/login",
            ),
            Finding(
                title="Missing CSP Header",
                description="Content-Security-Policy header is not set",
                severity=Severity.LOW,
                status=FindingStatus.NEW,
                target_id=target[0],
                vuln_type="missing_csp",
                affected_url="https://www.zomato.com",
            ),
        ]

        for finding in findings:
            session.add(finding)

        await session.commit()
        print("Seeded 2 sample findings")


async def main():
    """Run all seed operations."""
    print("Seeding database...")
    await seed_programs()
    await seed_sample_targets()
    await seed_sample_findings()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
