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
| Docker | **not installed locally**; Compose executed on GitHub Actions (see below) |

## What this changed

### CVE environment

The manual's step 6 assumes Docker and `docker compose`. Docker Desktop was not installed
on the Windows host: installing it requires administrator rights, WSL2/Virtual Machine
Platform and a reboot, none of which was available in this session. The vulnerable and
fixed EJS applications were therefore first launched directly with Node.js 20 using the
same package versions (`ejs@3.1.6` and `ejs@3.1.7`, `express@4.21.2`).

The same compose files were then executed in real Docker on the GitHub Actions
`ubuntu-latest` runner (workflow `.github/workflows/cve-docker.yml`):

<https://github.com/mycbdys/lab1/actions/runs/39195350651>

The vulnerable container returned HTTP 200 and `pwned.txt` inside it contained
`uid=0(root) gid=0(root)`; the fixed container rendered the normal page and had no
`pwned.txt`. Copies are in `docs/evidence/docker-ci/`. The Docker/Vulhub path is therefore
verified in Docker, not merely described; only a local Docker Desktop run on the Windows
host is missing.

### Payload stdio option

The captured payload uses
`execSync("cmd /c whoami > pwned.txt", {stdio: "ignore"})`. The hardened build shell of
this environment denies a child process that captures output through pipes, so the
explicit `stdio: "ignore"` avoids that pipe. On a normal machine the canonical payload
without the option also works; the vulnerability itself is unaffected. The command still
executes and writes its result to a file, which is the proof of code execution.

### Git remote and pipeline run

The repository is public at <https://github.com/mycbdys/lab1>. The push triggered GitHub
Actions, and all three jobs (`Unit tests`, `SAST (Bandit)`, `SCA (pip-audit)`) completed
successfully:

<https://github.com/mycbdys/lab1/actions/runs/39194790820>

The same checks also pass locally: `pytest` 21 passed, Bandit 0 issues, pip-audit 0 known
vulnerabilities. The title page uses the student's data: 李泽涛 (LiZetao), HDU number
23320332, group 23320113; no variant was assigned, so it is marked N/A. Both submission
links are filled.

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
