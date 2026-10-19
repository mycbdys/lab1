# HDU IS — Laboratory Work 1

**Secure REST API Development with CI/CD and Real CVE Vulnerability Analysis**

[![CI](https://github.com/mycbdys/lab1/actions/workflows/ci.yml/badge.svg)](https://github.com/mycbdys/lab1/actions/workflows/ci.yml)

This repository is the complete submission for Work 1 of the HDU Information Security
laboratory manual. It contains (1) a hardened Flask REST API, (2) an automated CI/CD
pipeline with SAST and SCA scanners, and (3) a controlled reproduction, root-cause
analysis and fix of a real CVE (CVE-2022-29078, EJS template-engine RCE).

> **Ethics / scope.** The vulnerable application is an isolated teaching target running
> on `127.0.0.1`. The exploit only writes the output of `whoami` to a local marker file.
> Never run any of this against systems you do not own or have written permission to test.

---

## 1. What the manual asks for and where it lives

| # | Manual step | Deliverable in this repository |
|---|-------------|--------------------------------|
| 1 | Choose a stack, create a project, initialise git, link a remote | Python 3 + Flask; `.git/` history; remote URL placeholder in §10 |
| 2 | Implement `POST /auth/login`, `GET /api/data` and one own method | `app/auth.py`, `app/api.py` (`POST /api/posts`) |
| 3 | SQLi protection, XSS protection, JWT, password hashing, auth middleware | `app/db.py`, `app/security.py`, `app/api.py` |
| 4 | CI/CD with SAST and SCA on every push/PR | `.github/workflows/ci.yml` (Bandit + pip-audit) |
| 5 | Test with curl/Postman; capture scanner reports | `scripts/api_demo.ps1`, `evidence/api-demo.txt`, `security/` |
| 6 | Prepare a vulnerable environment from Vulhub | `cve/CVE-2022-29078/` (Docker Compose + local Node harness) |
| 7 | Launch it and reproduce the attack | `cve/CVE-2022-29078/run_demo.ps1`, `evidence/vulnerable-run.txt` |
| 8 | Root-cause analysis | `cve/CVE-2022-29078/README.md` §4, report §7 |
| 9 | Apply the fix and rebuild | `cve/CVE-2022-29078/fixed/`, `docker-compose.fixed.yml` |
| 10 | Verify the fix and run regression tests | `evidence/fixed-run.txt`, `pytest` suite |
| 11 | Structured report | `docs/Lab1_Report.docx` / `.pdf` |

Control questions (8) are answered in `docs/Lab1_Control_Questions.docx` (full answers,
4 pages) and `docs/Lab1_Control_Questions_Short.docx` (short answers, 1 page). Markdown
sources are `docs/Control_Questions.md` and `docs/Control_Questions_Short.md`. The main
report only points to these documents and does not duplicate the answers.

---

## 2. Repository layout

```text
lab1/
├── app/                      Flask application
│   ├── __init__.py           application factory, error handlers
│   ├── config.py             environment-driven configuration
│   ├── db.py                 SQLite access (parameterised statements only)
│   ├── schema.sql            users / posts tables
│   ├── security.py           bcrypt, JWT, auth middleware, headers, rate limiter
│   ├── auth.py               POST /auth/login
│   └── api.py                GET /api/data, POST /api/posts
├── tests/                    pytest suite (21 tests)
├── scripts/
│   ├── seed.py               demo users alice / bob
│   └── api_demo.ps1          curl walkthrough that writes evidence/api-demo.txt
├── .github/workflows/ci.yml  tests + Bandit (SAST) + pip-audit (SCA)
├── security/                 Bandit and pip-audit reports
├── cve/CVE-2022-29078/       vulnerable and fixed EJS environments + evidence
├── evidence/                 captured command output used in the report
├── docs/                     report, control-question answers, task checklist
├── requirements.txt          runtime pins
├── requirements-dev.txt      test and scanner pins
├── run.py                    development entry point
└── README.md
```

---

## 3. Quick start

```powershell
# from the lab1 directory
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

python scripts\seed.py          # creates instance/lab1.sqlite3 and demo users
python run.py                   # http://127.0.0.1:5000
```

Linux/macOS:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/seed.py
python run.py
```

Demo accounts: `alice / Alice#2026`, `bob / Bob#2026` (seeded only for the demo).

Configuration is read from environment variables — never commit a real secret:

| Variable | Default | Meaning |
|----------|---------|---------|
| `SECRET_KEY` | random per process | JWT HMAC key (set a long random value in production) |
| `DATABASE` | `instance/lab1.sqlite3` | SQLite file |
| `JWT_TTL_MINUTES` | `15` | access-token lifetime |
| `BCRYPT_ROUNDS` | `12` | bcrypt cost |
| `LOGIN_MAX_ATTEMPTS` / `LOGIN_WINDOW_SECONDS` | `5` / `60` | login rate limit |

---

## 4. API

All request and response bodies are JSON. Protected endpoints require
`Authorization: Bearer <token>`.

### `POST /auth/login`

```bash
curl -s -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"Alice#2026"}'
```

```json
{"access_token":"eyJhbGciOiJIUzI1NiIs...","token_type":"Bearer","expires_in":900}
```

Failure always returns the same message (`Invalid username or password`) with `401`,
whether the user exists or not. More than five attempts per minute per IP+username
return `429` with `Retry-After`.

### `GET /api/data`

Returns only the authenticated user's posts. The text fields are HTML-escaped at output.

```bash
TOKEN="<access_token>"
curl -s http://127.0.0.1:5000/api/data -H "Authorization: Bearer $TOKEN"
```

```json
{"username":"alice","posts":[{"id":1,"title":"Hello","body":"World","created_at":"..."}]}
```

### `POST /api/posts` (own method)

Creates a post owned by the caller. `title` 1–120 chars, `body` 1–2000 chars.

```bash
curl -s -X POST http://127.0.0.1:5000/api/posts \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Hello","body":"World"}'
```

`201 Created` with the escaped post. Validation errors return `400`.

### `GET /health`

Liveness probe: `{"status":"ok"}`.

---

## 5. Security measures (manual step 3)

| Threat | Control | Code |
|--------|---------|------|
| SQL injection (A03) | Every query uses `?` bound parameters; no string concatenation or f-strings in SQL. | `app/db.py`, `app/auth.py`, `app/api.py` |
| Stored/reflected XSS (A03) | Untrusted text is HTML-escaped on output (`html.escape(..., quote=True)`), JSON responses, strict CSP and `nosniff`. | `app/security.py`, `app/api.py`, `app/__init__.py` |
| Broken authentication (A07) | bcrypt (cost 12, per-password salt), generic errors, dummy-hash timing equalisation, 8–72 char passwords, login rate limit. | `app/security.py`, `app/auth.py` |
| JWT flaws | HS256 pinned in `jwt.decode(algorithms=["HS256"])` (rejects `alg=none` and key confusion), `exp`/`iat`/`nbf`, `iss`, `aud`, `jti`, short TTL. | `app/security.py` |
| Broken access control (A01) | Every data query is scoped by `user_id = g.current_user["id"]`; no object id is accepted from the client. | `app/api.py` |
| Information leakage | Debug off, generic 500 handler, no stack traces, `Cache-Control: no-store` on auth/data. | `app/__init__.py`, `app/security.py` |
| Transport / browser hardening | CSP `default-src 'none'`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`, HSTS behind TLS. | `app/security.py` |

Deliberate non-choices: no `eval`, no `pickle`, no shell calls, no wildcard CORS, no
secret in source code, no password or token logging.

---

## 6. CI/CD pipeline (manual step 4)

`.github/workflows/ci.yml` runs on every push and pull request:

1. **test** — `pytest` on Python 3.12.
2. **sast** — Bandit over `app/`, SARIF output, uploaded as an artifact and to GitHub
   code scanning; `-ll` makes the job fail on medium/high findings.
3. **sca** — `pip-audit -r requirements.txt --strict` with a CycloneDX SBOM/report
   artifact; the job fails if any known vulnerable dependency is found.

Local equivalents (used to produce the reports in `security/`):

```bash
bandit -r app -f json -o security/bandit-report.json
pip-audit -r requirements.txt --format json -o security/pip-audit-report.json
```

Latest local results:

| Scanner | Scope | Result |
|---------|-------|--------|
| Bandit 1.9.4 | `app/` (303 LOC) | **0 issues** (0 high, 0 medium, 0 low) |
| pip-audit 2.10.1 | 44 installed packages (full tree) | **0 known vulnerabilities** |
| pytest 9.1.1 | 21 tests | **21 passed** |

---

## 7. CVE case study — CVE-2022-29078

**Vulnerability:** remote code execution in EJS < 3.1.7 through the
`settings[view options][outputFunctionName]` render option.

- Vulnerable environment: `cve/CVE-2022-29078/vulnerable` (EJS 3.1.6, Express 4.21.2).
- Fixed environment: `cve/CVE-2022-29078/fixed` (EJS 3.1.7, allow-listed render data).
- Reproduce: `pwsh cve/CVE-2022-29078/run_demo.ps1 -Mode vulnerable` (or `run_demo.sh`).
- Verify fix: `pwsh cve/CVE-2022-29078/run_demo.ps1 -Mode fixed`.
- Docker: `docker compose -f cve/CVE-2022-29078/docker-compose.yml up --build`; the same
  compose files were executed in real Docker on GitHub Actions
  (<https://github.com/mycbdys/lab1/actions/runs/39195350651>, artifact
  `cve-docker-evidence`, copies in `docs/evidence/docker-ci/`).

Evidence is stored in `cve/CVE-2022-29078/evidence/` and `docs/evidence/docker-ci/`; the
full analysis is in `cve/CVE-2022-29078/README.md` and report §7.

---

## 8. Tests

```bash
pytest -q          # 21 passed
```

Coverage includes: successful login, wrong password, unknown user (same response),
malformed input, short password, SQLi in username/password, bcrypt storage, rate limit,
missing/tampered/expired/`alg=none`/foreign-key tokens, deleted user, missing token,
per-user data isolation, create-post validation, stored-XSS escaping, SQL metacharacters
stored literally, security headers.

---

## 9. Environment note

The Windows host used to build this submission did **not** have Docker Desktop installed
(`docker` was not on `PATH`; installing it requires administrator rights, WSL2 and a
reboot). The CVE was therefore reproduced locally with the same vulnerable package
versions running directly on Node.js 20, and the same `Dockerfile` / `docker-compose.yml`
files were executed in real Docker on the GitHub Actions Ubuntu runner — the vulnerable
container executed `id` as root and the fixed container blocked the attack. Evidence is in
`cve/.../evidence/` and `docs/evidence/docker-ci/`. This does not change the vulnerability,
the exploit, the root cause or the fix.

---

## 10. Submission links

- Student: 李泽涛 (LiZetao) — HDU number 23320332 — group 23320113 — variant: N/A (not assigned)
- Public repository: <https://github.com/mycbdys/lab1>
- Last successful pipeline run: <https://github.com/mycbdys/lab1/actions/runs/39194790820>

The repository is public and the CI workflow runs on every push and pull request. The run
linked above executed all three jobs successfully: **Unit tests**, **SAST (Bandit)** and
**SCA (pip-audit)**.

To update the published repository after a local change:

```bash
git push
```
