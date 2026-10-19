# Environment and limitations

## Build machine

| Item | Value |
|------|-------|
| OS | Windows 11 (x64) |
| Python | 3.13.3 |
| Flask | 3.1.3 |
| Node.js | v20.18.0 |
| npm | 10.8.2 |
| Git | 2.54.0 |
| Docker | **not installed** (no `docker` / `docker compose` on `PATH`) |

## What this changed

### CVE environment

The manual's step 6 assumes Docker and `docker compose`. Docker was not available, so the
vulnerable and fixed EJS applications were launched directly with Node.js 20 using the
same package versions (`ejs@3.1.6` and `ejs@3.1.7`, `express@4.21.2`). This changes only
the isolation layer, not the vulnerability, the request, the root cause or the fix.

Vulhub-style artifacts are still delivered so the same environment can be started on a
machine with Docker:

```bash
cd cve/CVE-2022-29078
docker compose up --build
docker compose -f docker-compose.fixed.yml up --build
```

The Dockerfiles and compose files were reviewed but could not be executed on this
machine; that is stated in the report instead of claiming a Docker run that did not
happen.

### Payload stdio option

The captured payload uses
`execSync("cmd /c whoami > pwned.txt", {stdio: "ignore"})`. The hardened build shell of
this environment denies a child process that captures output through pipes, so the
explicit `stdio: "ignore"` avoids that pipe. On a normal machine the canonical payload
without the option also works; the vulnerability itself is unaffected. The command still
executes and writes its result to a file, which is the proof of code execution.

### Git remote and pipeline run

No GitHub/GitLab credentials were available, so the repository could not be pushed and
the pipeline could not be executed on GitHub Actions. The workflow is committed and was
validated locally: `pytest` (21 passed), Bandit (0 issues) and pip-audit (0 known
vulnerabilities) were run with the same commands the workflow uses. Two placeholders must
be replaced before submission:

1. `README.md` §10 — public repository URL.
2. `README.md` §10 — URL of the last successful pipeline run.

The title page now uses the student's data: 李泽涛 (LiZetao), HDU number 23320332,
group 23320113; no variant was assigned, so it is marked N/A. Only the public repository
URL and the pipeline-run URL remain as placeholders.

## Commands used to produce the evidence

```powershell
# tests + scanners
pytest -q
bandit -r app -f json -o security/bandit-report.json
pip-audit --path .pylibs -s osv -f json -o security/pip-audit-report.json

# API walkthrough
.\scripts\api_demo.ps1

# CVE reproduction / fix verification
.\cve\CVE-2022-29078\run_demo.ps1 -Mode vulnerable
.\cve\CVE-2022-29078\run_demo.ps1 -Mode fixed
```
