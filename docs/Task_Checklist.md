# Work 1 — Task checklist

Source: *Labs Full Manual HDU IS*, Work 1 "Secure REST API Development with CI/CD and Real
CVE Vulnerability Analysis" (manual pp. 1–5). Status is based on the artifacts in this
folder, not on intention.

| # | Task from the manual | Status | Where it is evidenced |
|---|----------------------|--------|-----------------------|
| 1 | Choose a stack, create a project with a package manager, initialise git and link a remote | Done | Python 3.13 + Flask; `requirements.txt`; public repository <https://github.com/mycbdys/lab1> with `main` history |
| 2 | Implement 3 methods: `POST /auth/login`, `GET /api/data`, one own method | Done | `app/auth.py`, `app/api.py` (`POST /api/posts`); `evidence/api-demo.txt` |
| 3 | Implement SQLi protection, XSS protection, JWT issuance and verification, password hashing | Done | `app/db.py`, `app/security.py`, `app/api.py`; tests `tests/test_auth.py`, `tests/test_api.py` |
| 4 | CI/CD pipeline (GitHub Actions or GitLab CI) with SAST and SCA on every push/PR | Done (local + GitHub) | `.github/workflows/ci.yml`; run <https://github.com/mycbdys/lab1/actions/runs/39194790820>; `security/` reports |
| 5 | Test the API with Postman or curl; capture scanner reports | Done | `scripts/api_demo.ps1`, `evidence/api-demo.txt`, `security/` |
| 6 | Install Docker/Compose, clone Vulhub, choose and study a CVE directory | Partially (Docker absent) | `cve/CVE-2022-29078/` with Vulhub-style Docker files; CVE studied from NVD/OSV/GHSA; see `docs/Environment_Notes.md` |
| 7 | Launch the vulnerable environment, reproduce the attack, record commands/requests | Done | `cve/CVE-2022-29078/run_demo.ps1`; `cve/CVE-2022-29078/evidence/vulnerable-run.txt` |
| 8 | Root-cause analysis of the CVE (logic, input handling, configuration) | Done | `cve/CVE-2022-29078/README.md` §4; report §7.4 |
| 9 | Develop and apply the fix (config, version bump, code), rebuild | Done | `cve/CVE-2022-29078/fixed/`; `docker-compose.fixed.yml`; diff in report §7.5 |
| 10 | Verify the fix; repeat the exploit; regression-test main functionality | Done | `cve/CVE-2022-29078/evidence/fixed-run.txt`; `pytest` 21/21 |
| 11 | Prepare the structured report with title page and all required sections | Done | `docs/Lab1_Report.docx` / `.pdf` |

## "What Students Submit" mapping

| Required submission item | Where |
|--------------------------|-------|
| 1. Link to a public git repository | <https://github.com/mycbdys/lab1> (also on report title page and `README.md` §10) |
| 2. README with project/API description, security measures, scanner screenshots, CVE ID/description, reproduction sequence, root cause, fix, proof of elimination | `README.md`, `security/`, `cve/CVE-2022-29078/README.md`, `evidence/`, report §4–§7 |
| 3. Link to the last successful pipeline run | <https://github.com/mycbdys/lab1/actions/runs/39194790820> (Unit tests, SAST and SCA all green) |
| 4. Folder with fixes (compose/Dockerfile/source changes) | `cve/CVE-2022-29078/fixed/`, `docker-compose.fixed.yml`, `cve/CVE-2022-29078/patches/` |

## Evaluation-criteria self-check (max 10)

| Criterion | Points | Evidence |
|-----------|--------|----------|
| API functionality (auth + data retrieval correct) | 2 | `evidence/api-demo.txt`, 21 tests |
| SQLi protection | 0.5 | parameterised statements; SQLi tests |
| XSS protection | 0.5 | output escaping; stored-XSS test |
| Authentication (JWT + password hashing) | 1 | HS256 with pinned alg/iss/aud; bcrypt cost 12; token tests |
| CI/CD with at least one SAST/SCA tool | 2 | Bandit + pip-audit workflow and reports |
| Successful launch and reproduction of the CVE | 2 | `evidence/vulnerable-run.txt` (local Node; Docker files provided) |
| Depth of root-cause analysis | 1 | `cve/.../README.md` §4, report §7.4 |
| Correctness/effectiveness of fix and verification | 1 | `evidence/fixed-run.txt`, regression checks |

## Known limitations to disclose in the report

- Docker was not installed on the build machine, so the CVE environment was launched with
  the same package versions directly on Node.js 20 instead of through `docker compose`.
  Dockerfiles and compose files are provided and were reviewed, but not executed.
- The manual asks for screenshots. The raw terminal transcripts are in `evidence/`; the
  report reproduces the relevant lines verbatim and can be supplemented with screenshots
  taken from the same runs (`run_demo.ps1`, `api_demo.ps1`).
