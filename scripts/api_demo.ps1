<#
.SYNOPSIS
    End-to-end cURL walkthrough of the secure API, saved as evidence.

.DESCRIPTION
    Seeds the demo database, starts the API on 127.0.0.1:5055, exercises login,
    the unauthenticated 401, post creation, output encoding and SQL-injection
    attempts, and writes the transcript to evidence/api-demo.txt.
#>
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

$evidenceDir = Join-Path $root "evidence"
New-Item -ItemType Directory -Force $evidenceDir | Out-Null
$logPath = Join-Path $evidenceDir "api-demo.txt"
Set-Content -Path $logPath -Value "" -Encoding utf8

function Write-Log([string]$message) {
    Write-Host $message
    Add-Content -Path $logPath -Value $message -Encoding utf8
}

function Invoke-Curl([string[]]$arguments) {
    $output = & curl.exe @arguments 2>&1
    return ($output | Out-String).Trim()
}

function Write-Body([string]$name, [string]$json) {
    $path = Join-Path $evidenceDir $name
    Set-Content -Path $path -Value $json -Encoding ASCII
    return "@$path"
}

$python = (Get-Command python).Source
$port = 5055
$base = "http://127.0.0.1:$port"
$env:PORT = "$port"
$dbPath = Join-Path $root "instance\lab1.sqlite3"
Remove-Item $dbPath -ErrorAction SilentlyContinue
$serverOut = Join-Path $evidenceDir "api-server.log"
$serverErr = Join-Path $evidenceDir "api-server.err"

Write-Log "HDU IS Lab 1 - API acceptance walkthrough"
Write-Log "timestamp: $(Get-Date -Format o)"
Write-Log "python: $(& $python --version 2>&1)"
Write-Log "base_url: $base"
Write-Log "database: $dbPath"
Write-Log ""

Write-Log "== 1. Seed demo users =="
Write-Log ((& $python "scripts\seed.py") 2>&1 | Out-String).Trim()

$server = Start-Process -FilePath $python -ArgumentList "run.py" -WorkingDirectory $root `
    -RedirectStandardOutput $serverOut -RedirectStandardError $serverErr -PassThru -WindowStyle Hidden
try {
    $healthy = $false
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Milliseconds 500
        $healthCode = Invoke-Curl @("-s", "-o", "NUL", "-w", "%{http_code}", "$base/health")
        if ($healthCode -eq "200") { $healthy = $true; break }
    }
    if (-not $healthy) { throw "API did not start on port $port." }

    Write-Log ""
    Write-Log "== 2. POST /auth/login (valid credentials) =="
    $loginRef = Write-Body "login.json" '{"username":"alice","password":"Alice#2026"}'
    $login = Invoke-Curl @("-s", "-X", "POST", "$base/auth/login", "-H", "Content-Type: application/json", "-d", $loginRef)
    $loginJson = $login | ConvertFrom-Json
    Write-Log ($loginJson | Select-Object token_type, expires_in | ConvertTo-Json -Compress)
    $token = $loginJson.access_token
    if (-not $token) { throw "Login did not return a token." }
    Write-Log "access_token: $($token.Substring(0, 24))... (redacted)"
    $auth = @("-H", "Authorization: Bearer $token")

    Write-Log ""
    Write-Log "== 3. GET /api/data without a token =="
    $status = Invoke-Curl (@("-s", "-o", "NUL", "-w", "%{http_code}", "$base/api/data"))
    Write-Log "HTTP $status (expected 401)"

    Write-Log ""
    Write-Log "== 4. POST /api/posts with a stored-XSS payload =="
    $xssRef = Write-Body "xss.json" '{"title":"<script>alert(1)</script>","body":"XSS test"}'
    $created = Invoke-Curl (@("-s", "-w", "`nHTTP %{http_code}", "-X", "POST", "$base/api/posts", "-H", "Content-Type: application/json") + $auth + @("-d", $xssRef))
    Write-Log $created

    Write-Log ""
    Write-Log "== 5. GET /api/data (escaped output) =="
    $data = Invoke-Curl (@("-s", "$base/api/data") + $auth)
    Write-Log $data

    Write-Log ""
    Write-Log "== 6. SQL injection attempts =="
    $sqli1Ref = Write-Body "sqli-username.json" '{"username":"alice'' OR ''1''=''1","password":"whatever#2026"}'
    $sqli1 = Invoke-Curl (@("-s", "-w", "`nHTTP %{http_code}", "-X", "POST", "$base/auth/login", "-H", "Content-Type: application/json", "-d", $sqli1Ref))
    Write-Log "username payload -> $sqli1"

    $sqli2Ref = Write-Body "sqli-password.json" '{"username":"bob","password":"'' OR ''1''=''1'' --"}'
    $sqli2 = Invoke-Curl (@("-s", "-w", "`nHTTP %{http_code}", "-X", "POST", "$base/auth/login", "-H", "Content-Type: application/json", "-d", $sqli2Ref))
    Write-Log "password payload -> $sqli2"

    Write-Log ""
    Write-Log "== 7. Security headers on /health =="
    $headers = Invoke-Curl @("-s", "-D", "-", "-o", "NUL", "$base/health")
    Write-Log $headers

    Write-Log ""
    Write-Log "RESULT: API walkthrough completed."
}
finally {
    if ($server -and -not $server.HasExited) {
        Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
    }
}
