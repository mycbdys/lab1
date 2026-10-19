# CVE-2022-29078 — Docker Compose run on GitHub Actions

Local Docker Desktop was not available on the lab machine, so the submitted Compose
environment was executed on GitHub Actions' Ubuntu runner, which provides a real Docker
Engine and Docker Compose.

- Workflow: `.github/workflows/cve-docker.yml`
- Successful run: <https://github.com/mycbdys/lab1/actions/runs/39195350651>
- Artifact: `cve-docker-evidence` (downloaded copies in this folder)

## What the run did

1. `docker compose up -d --build` in `cve/CVE-2022-29078` (vulnerable EJS 3.1.6).
2. Waited for `http://127.0.0.1:3000/health`.
3. Sent the `settings[view options][outputFunctionName]` payload with
   `execSync("id > pwned.txt")` and received HTTP 200.
4. Read `pwned.txt` from inside the vulnerable container — it contains
   `uid=0(root) gid=0(root) ...`, proving command execution as root.
5. Stopped the vulnerable stack, started the fixed stack (EJS 3.1.7) and sent the same
   request to port 3001.
6. Verified that the page still renders `Hello, guest!` and that `pwned.txt` does not
   exist in the fixed container.

## Files

| File | Meaning |
|------|---------|
| `pwned.txt` | output of `id` written inside the vulnerable container |
| `vulnerable-response.html` | HTTP response of the exploited request (200, normal page) |
| `fixed-response.html` | response of the fixed app to the same request |
| `fixed.log` | fixed container log showing EJS 3.1.7 |

This is the Docker execution of the same environment that was also run locally with
Node.js 20; the local run is documented in `cve/CVE-2022-29078/evidence/`.
