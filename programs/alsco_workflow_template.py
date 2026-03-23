"""
ALSCO Bug Bounty - AI Workflow Generator Prompt

Program: ALSCO Bug Bounty
Platform: Manual (internal program)
Test Environment: sandbox.securegateway.com, sandbox-royal.securegateway.com

CRITICAL REQUIREMENTS:
1. Full hack scenario REQUIRED - edit index page OR download database
2. Video PoC REQUIRED for all submissions
3. No low-impact findings accepted
4. Business logic errors are out of scope

IN-SCOPE TESTING TARGETS:

Target 1: sandbox.securegateway.com (Secure Gateway)
├── Priority: CRITICAL
├── Authentication: Required (2FA via Secure Gateway mobile app)
└── Testing Focus:
    ├── 2FA Bypass - Test authentication without receiving code
    │   ├── Try brute force the OTP code
    │   ├── Bypass rate limits
    │   ├── Token prediction/fixation
    │   └── Race condition attacks
    ├── File Upload Bypass
    │   ├── Extensions OUTSIDE allowed list:
    │   │   jpg, jpeg, png, gif, jfif, mp4, doc, docx, pdf, xls, xlsx, 
    │   │   ppsx, ppt, pptx, flv, rar, zip, htm, html
    │   ├── Test extensions: .php, .phtml, .asp, .aspx, .jsp, .js, .svg, .xml
    │   └── File MUST execute in browser when accessed
    └── Upload Detector Bypass
        ├── Upload .jpg with malicious content (e.g., php_uname)
        ├── Polyglot files
        └── Content-type/extension mismatch

Target 2: sandbox-royal.securegateway.com (Royal CMS)
├── Priority: CRITICAL  
├── Authentication: Not required initially
└── Testing Focus:
    ├── Injection Testing
    │   ├── XSS Injection (Reflected, Stored, DOM)
    │   ├── SQL Injection (Boolean, Time-based, Union, Error-based)
    │   ├── OS Injection / Command Injection
    │   ├── URL Injection
    │   └── Remote Code Execution (RCE)
    ├── Authentication Testing
    │   ├── Brute force login
    │   ├── Credential stuffing
    │   ├── Session hijacking
    │   └── Privilege escalation
    └── CMS-Specific
        ├── Admin panel access
        ├── Plugin vulnerabilities
        ├── Theme vulnerabilities
        └── Database extraction

PRIORITY HUNTING ORDER:
1. RCE on Royal CMS (critical)
2. SQL Injection with data extraction (critical)
3. File upload leading to code execution (critical)
4. Full account takeover via 2FA bypass (high)
5. Stored XSS with session hijacking (high)
6. IDOR leading to sensitive data access (high)

OUT OF SCOPE (DO NOT TEST):
- *.checksw.com subdomain takeovers
- firewallgateway.com (redirect page only)
- Clickjacking, CSRF on non-sensitive forms
- DoS attacks
- Social engineering
- MITM/physical access attacks
- Missing best practices (CSP, SPF, etc.)
- Secure Gateway bypasses (marked Informative only)
- SaaS apps under Secure Gateway

REQUIRED EVIDENCE:
- Video recording showing full attack
- Step-by-step reproduction
- Impact demonstration
- Before/after state comparison

REWARD CRITERIA:
- Based on CVSS severity
- Full scenario impact required
- Must affect production OR prove production impact
- Previous bounties don't set precedent
"""

PRIORITY_PHASES = {
    "phase_1_recon": {
        "order": 1,
        "name": "Reconnaissance",
        "risk_level": "SAFE",
        "auto_approve": True,
        "steps": [
            {
                "name": "Subdomain enumeration",
                "tool": "subfinder",
                "command": "subfinder -d securegateway.com -o subdomains.txt",
                "rationale": "Find all in-scope subdomains"
            },
            {
                "name": "Screenshot all endpoints",
                "tool": "gowitness",
                "command": "gowitness scan -f subdomains.txt",
                "rationale": "Visual reconnaissance"
            },
            {
                "name": "Port scanning",
                "tool": "nmap",
                "command": "nmap -sV -sC -p- sandbox.securegateway.com",
                "rationale": "Service enumeration"
            }
        ]
    },
    "phase_2_auth_test": {
        "order": 2,
        "name": "2FA Authentication Testing",
        "risk_level": "HIGH",
        "auto_approve": False,
        "requires_approval": True,
        "approval_rationale": "Direct authentication testing",
        "steps": [
            {
                "name": "2FA code enumeration",
                "tool": "custom",
                "command": "Python script to brute force 6-digit OTP",
                "rationale": "Test rate limiting on 2FA codes",
                "requires_account": True
            },
            {
                "name": "2FA bypass techniques",
                "tool": "custom",
                "command": "Test OTP reuse, race conditions, token manipulation",
                "rationale": "Multiple bypass vectors",
                "requires_account": True
            }
        ]
    },
    "phase_3_upload_bypass": {
        "order": 3,
        "name": "File Upload Security Testing",
        "risk_level": "CRITICAL",
        "auto_approve": False,
        "requires_approval": True,
        "approval_rationale": "Code execution potential",
        "steps": [
            {
                "name": "Extension fuzzing",
                "tool": "custom",
                "command": "Upload various extensions (.php, .phtml, .asp, etc.)",
                "rationale": "Find executable extensions outside whitelist",
                "requires_auth": True
            },
            {
                "name": "Content-type bypass",
                "tool": "custom",
                "command": "Test MIME type manipulation",
                "rationale": "Bypass server-side checks"
            },
            {
                "name": "Polyglot files",
                "tool": "custom",
                "command": "Create polyglot files (JPG+PHP, PDF+JS, etc.)",
                "rationale": "Bypass content detection"
            },
            {
                "name": "Extension blacklist testing",
                "tool": "custom",
                "command": "Double extensions, null bytes, case variation",
                "rationale": "Common bypass techniques"
            }
        ]
    },
    "phase_4_cms_testing": {
        "order": 4,
        "name": "Royal CMS Testing",
        "risk_level": "CRITICAL",
        "auto_approve": False,
        "requires_approval": True,
        "approval_rationale": "RCE and database access potential",
        "steps": [
            {
                "name": "CMS fingerprinting",
                "tool": "whatweb",
                "command": "whatweb -a 3 sandbox-royal.securegateway.com",
                "rationale": "Identify Royal CMS version"
            },
            {
                "name": "SQL Injection scan",
                "tool": "sqlmap",
                "command": "sqlmap -u 'URL' --batch --level=5 --risk=3",
                "rationale": "Comprehensive SQLi testing",
                "requires_auth": False
            },
            {
                "name": "XSS testing",
                "tool": "xsstrike",
                "command": "xsstrike -u 'TARGET_URL'",
                "rationale": "Find XSS vulnerabilities"
            },
            {
                "name": "Command injection testing",
                "tool": "custom",
                "command": "Test ping, curl, wget endpoints for OS command injection",
                "rationale": "RCE via command injection"
            },
            {
                "name": "Admin panel enumeration",
                "tool": "dirsearch",
                "command": "dirsearch -u TARGET -w admin-panels.txt",
                "rationale": "Find admin access points"
            },
            {
                "name": "RCE via upload",
                "tool": "custom",
                "command": "Upload web shell if upload bypass found",
                "rationale": "Confirm code execution",
                "requires_auth": True
            }
        ]
    },
    "phase_5_exploitation": {
        "order": 5,
        "name": "Full Scenario Exploitation",
        "risk_level": "CRITICAL",
        "auto_approve": False,
        "requires_approval": True,
        "approval_rationale": "Must demonstrate full impact - edit index OR dump database",
        "steps": [
            {
                "name": "Database enumeration",
                "tool": "custom",
                "command": "If SQLi found: enumerate and extract database",
                "rationale": "CRITICAL: Database extraction required for bounty",
                "requires_auth": False
            },
            {
                "name": "Index page modification",
                "tool": "custom",
                "command": "If RCE found: modify index page as proof",
                "rationale": "CRITICAL: Page modification required for bounty",
                "requires_auth": True
            },
            {
                "name": "Video documentation",
                "tool": "custom",
                "command": "Record full attack scenario",
                "rationale": "Video PoC REQUIRED for submission",
                "is_required": True
            }
        ]
    }
}

CRITICAL_REMINDERS = [
    "ONLY accept findings with FULL IMPACT (RCE, data breach, page modification)",
    "Video PoC REQUIRED for all submissions",
    "Do NOT test DoS, social engineering, or physical attacks",
    "Business logic errors are out of scope",
    "Secure Gateway bypasses will be marked Informative only",
    "Get permission before extended testing on Royal CMS"
]
