# Security scanner reports

Generated on 2026-10-19 from the final source tree.

## SAST — Bandit 1.9.4

```bash
bandit -r app -f json -o security/bandit-report.json
```

| Metric | Value |
|--------|-------|
| Lines of code scanned | 303 |
| High severity | 0 |
| Medium severity | 0 |
| Low severity | 0 |
| `# nosec` suppressions | 0 |
| **Total findings** | **0** |

`security/bandit-report.json` is the machine-readable report used by CI. The initial run
found one low-severity false positive (`B105` on the string constant `"Bearer"`); the
constant was renamed to `AUTH_SCHEME` rather than suppressed, and the final run is clean.

## SCA — pip-audit 2.10.1

```bash
pip-audit --path .pylibs -s osv -f json -o security/pip-audit-report.json
```

| Metric | Value |
|--------|-------|
| Packages audited | 44 (full installed tree: runtime + test + scanner dependencies) |
| Known vulnerabilities | **0** |

The CI pipeline runs `pip-audit -r requirements.txt --strict` with CycloneDX output, so
the audit fails the build if any known vulnerability is found in the dependency tree.

## Test suite — pytest 9.1.1

```text
21 passed
```

Covered: valid/invalid login, identical error for unknown user, malformed JSON, password
length, SQL injection in username/password, bcrypt storage, login rate limiting, missing
token, tampered token, expired token, `alg=none`, token signed with another key, token for
a deleted user, per-user data isolation, post validation, stored-XSS escaping, SQL
metacharacters stored literally, and security headers.
