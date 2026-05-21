#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

INCLUDE_SUFFIXES = {
    ".java",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".py",
    ".xml",
    ".yml",
    ".yaml",
    ".json",
    ".env",
    ".properties",
}

SKIP_DIRS = {
    ".git",
    ".idea",
    ".next",
    ".nuxt",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "target",
    "coverage",
    "__pycache__",
}


@dataclass
class Finding:
    rule_id: str
    title: str
    severity: str
    category: str
    file_path: str
    line_number: int
    evidence: str
    rationale: str
    remediation: str


RULES = [
    {
        "rule_id": "SEC-001",
        "title": "Possible hardcoded secret",
        "severity": "high",
        "category": "secrets",
        "pattern": re.compile(r"(?i)(api[_-]?key|secret|token|password|private[_-]?key).{0,20}[:=].{0,4}['\"][^'\"]{8,}['\"]"),
        "rationale": "Hardcoded credentials or tokens may leak through source code or logs.",
        "remediation": "Move secrets to environment variables or a secret manager.",
    },
    {
        "rule_id": "SEC-002",
        "title": "Weak hash or encryption algorithm",
        "severity": "medium",
        "category": "crypto",
        "pattern": re.compile(r"(?i)\b(md5|sha1|des|rc4)\b"),
        "rationale": "Weak algorithms are vulnerable to brute-force or cryptographic attacks.",
        "remediation": "Use modern hashes and ciphers such as bcrypt, scrypt, Argon2, or AES-GCM.",
    },
    {
        "rule_id": "SEC-003",
        "title": "Weak random source",
        "severity": "medium",
        "category": "crypto",
        "pattern": re.compile(r"(?i)\b(Math\.random|new Random\(|random\.random\()"),
        "rationale": "Weak randomness is unsafe for tokens, passwords, or security-sensitive IDs.",
        "remediation": "Use a cryptographically secure random generator.",
    },
    {
        "rule_id": "SEC-004",
        "title": "Possible command execution",
        "severity": "high",
        "category": "input-output",
        "pattern": re.compile(r"(?i)\b(exec\(|system\(|Runtime\.getRuntime\(|subprocess\.(run|Popen)|child_process\.)"),
        "rationale": "Command execution becomes dangerous when user input reaches the shell.",
        "remediation": "Avoid shell execution or strictly sanitize and allowlist inputs.",
    },
    {
        "rule_id": "SEC-005",
        "title": "Possible unsafe deserialization or parsing",
        "severity": "high",
        "category": "input-output",
        "pattern": re.compile(r"(?i)\b(pickle\.load|yaml\.load\(|ObjectInputStream|DocumentBuilderFactory)"),
        "rationale": "Unsafe parsers may lead to code execution or XML entity expansion issues.",
        "remediation": "Use safe loaders and hardened parser settings.",
    },
    {
        "rule_id": "SEC-006",
        "title": "Possible path traversal or unsafe file access",
        "severity": "high",
        "category": "file-handling",
        "pattern": re.compile(r"(?i)\b(open\(|Path\(|File\(|send_file\(|res\.download\(|readFileSync\()"),
        "rationale": "User-controlled file paths may lead to path traversal or unauthorized downloads.",
        "remediation": "Normalize paths and restrict access to allowlisted directories or IDs.",
    },
    {
        "rule_id": "SEC-007",
        "title": "Possible SQL string concatenation",
        "severity": "high",
        "category": "input-output",
        "pattern": re.compile(r"(?i)(SELECT |INSERT |UPDATE |DELETE ).*(\+|f\"|f'|%s|format\()"),
        "rationale": "Dynamic SQL construction often leads to injection risk.",
        "remediation": "Use parameterized queries or ORM-bound parameters.",
    },
    {
        "rule_id": "SEC-008",
        "title": "Possible external URL fetch",
        "severity": "medium",
        "category": "external-calls",
        "pattern": re.compile(r"(?i)\b(requests\.(get|post)|axios\.|fetch\(|httpx\.|urllib\.request)"),
        "rationale": "External requests should be reviewed for SSRF and trust-boundary issues.",
        "remediation": "Validate destination hosts and isolate sensitive networks.",
    },
    {
        "rule_id": "SEC-009",
        "title": "Possible sensitive logging",
        "severity": "medium",
        "category": "logging",
        "pattern": re.compile(r"(?i)\b(log|logger|print|console\.log).*(password|token|secret|cookie|authorization)"),
        "rationale": "Sensitive data written to logs can create long-term exposure.",
        "remediation": "Mask or avoid logging secrets and tokens.",
    },
]

MANUAL_REVIEW_ITEMS = [
    "TLS / ingress / WAF configuration",
    "MFA enforcement",
    "Account lockout thresholds",
    "Secret-manager or KMS integration",
    "Runtime port exposure",
    "Object storage and file-server permissions",
]


def iter_files(root: Path):
    for path in root.rglob("*"):
        if path.is_dir() and path.name in SKIP_DIRS:
            continue
        if path.is_file() and path.suffix in INCLUDE_SUFFIXES and not any(part in SKIP_DIRS for part in path.parts):
            yield path


def scan_file(path: Path, project_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return findings

    for line_no, line in enumerate(lines, start=1):
        for rule in RULES:
            if rule["pattern"].search(line):
                findings.append(
                    Finding(
                        rule_id=rule["rule_id"],
                        title=rule["title"],
                        severity=rule["severity"],
                        category=rule["category"],
                        file_path=str(path.relative_to(project_root)),
                        line_number=line_no,
                        evidence=line.strip()[:240],
                        rationale=rule["rationale"],
                        remediation=rule["remediation"],
                    )
                )
    return findings


def render_markdown(findings: list[Finding], root: Path) -> str:
    by_severity = {"high": [], "medium": [], "low": []}
    for finding in findings:
        by_severity.setdefault(finding.severity, []).append(finding)

    lines = [
        "# Secure Code Review Pre-Scan",
        "",
        f"- project: `{root}`",
        f"- finding_count: `{len(findings)}`",
        "",
        "## Findings",
        "",
    ]

    if not findings:
        lines.extend(
            [
                "No strong signals were found by the pre-scan.",
                "",
                "This does not prove the code is secure. Continue with manual semantic review.",
            ]
        )
    else:
        for severity in ("high", "medium", "low"):
            bucket = by_severity.get(severity, [])
            if not bucket:
                continue
            lines.extend([f"## {severity.title()}", ""])
            for item in bucket:
                lines.extend(
                    [
                        f"- `{item.rule_id}` {item.title}",
                        f"  - file: `{item.file_path}:{item.line_number}`",
                        f"  - category: `{item.category}`",
                        f"  - evidence: `{item.evidence}`",
                        f"  - rationale: {item.rationale}",
                        f"  - remediation: {item.remediation}",
                    ]
                )
            lines.append("")

    lines.extend(["## Needs Manual Review", ""])
    for item in MANUAL_REVIEW_ITEMS:
        lines.append(f"- {item}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generic multi-language secure code pre-scan.")
    parser.add_argument("project", help="Project root path")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--output", help="Optional output file")
    args = parser.parse_args()

    root = Path(args.project).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"Project path does not exist: {root}")

    findings: list[Finding] = []
    for file_path in iter_files(root):
        findings.extend(scan_file(file_path, root))

    if args.format == "json":
        output = json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2)
    else:
        output = render_markdown(findings, root)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
