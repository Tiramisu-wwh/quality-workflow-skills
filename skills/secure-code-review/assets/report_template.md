# Secure Code Review Report

## 1. Scope

- Project / module:
- Review date:
- Input:
  - source path
  - main language
  - architecture notes / API docs / deployment notes if any
- Covered areas:
- Excluded or sampled areas:

## 2. Summary

- Decision: `pass` / `conditional_pass` / `fail`
- Why:
  - whether `critical` / `high` findings exist
  - whether unresolved `needs_manual_review` items affect release confidence
- Risk summary:

## 3. Confirmed Findings

For each finding, include:

- title
- severity
- file and line
- risk path or exploit idea
- code evidence
- fix suggestion

## 4. Control Matrix

Recommended columns:

| Category | Control | Status | Evidence | Notes |
| --- | --- | --- | --- | --- |

Status values:

- `pass`
- `fail`
- `needs_manual_review`
- `not_applicable`

Recommended categories:

- secrets and sensitive data
- input validation and output handling
- auth and access control
- session and token handling
- file upload and download
- logging and exception handling
- crypto and randomness
- external calls and redirects

## 5. Positive Controls

List controls that can be proven directly from source code, for example:

- parameterized queries or safe ORM binding
- strong random token generation
- upload type and size allowlists
- centralized exception handling
- resource-level authorization checks

## 6. Needs Manual Review

List items that cannot be proven from source code alone, for example:

- TLS / WAF / network policy
- MFA enforcement
- account lockout thresholds
- KMS or secret management platform
- runtime port exposure
- object storage or file server permissions

## 7. Fix Priority

- fix now:
- fix before release:
- later hardening:

## 8. Residual Risk

- not covered:
- deployment-dependent risks:
- suggested follow-up checks:
