"""Generate the two diagrams used in the report (Pillow only)."""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "images")
os.makedirs(OUT, exist_ok=True)

BLUE = (31, 78, 121)
LIGHT = (232, 241, 248)
RED = (176, 42, 55)
RED_LIGHT = (252, 235, 235)
GREY = (90, 90, 90)
DARK = (33, 37, 41)


def font(size: int, bold: bool = False, mono: bool = False):
    name = "consola.ttf" if mono else ("arialbd.ttf" if bold else "arial.ttf")
    return ImageFont.truetype(os.path.join("C:\\Windows\\Fonts", name), size)


def box(draw, xy, fill, outline, width=3, radius=14):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def centered(draw, xy, text, f, fill=DARK):
    x0, y0, x1, y1 = xy
    draw.multiline_text(
        ((x0 + x1) / 2, (y0 + y1) / 2),
        text,
        font=f,
        fill=fill,
        anchor="mm",
        align="center",
        spacing=6,
    )


def arrow(draw, start, end, color=BLUE, width=4):
    draw.line([start, end], fill=color, width=width)
    x, y = end
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = max((dx * dx + dy * dy) ** 0.5, 1)
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    size = 14
    draw.polygon(
        [
            (x, y),
            (x - ux * size + px * size * 0.55, y - uy * size + py * size * 0.55),
            (x - ux * size - px * size * 0.55, y - uy * size - py * size * 0.55),
        ],
        fill=color,
    )


def architecture():
    image = Image.new("RGB", (1500, 850), "white")
    draw = ImageDraw.Draw(image)

    draw.text((60, 40), "Secure REST API - architecture and trust boundaries", font=font(34, True), fill=BLUE)

    box(draw, (60, 150, 330, 300), LIGHT, BLUE)
    centered(draw, (60, 150, 330, 300), "Client\ncurl / Postman", font(22))

    box(draw, (430, 120, 1000, 560), (250, 250, 250), BLUE)
    draw.text((450, 140), "Flask application", font=font(24, True), fill=BLUE)

    routes = [
        ("POST /auth/login\nbcrypt + JWT (HS256, 15 min)\nrate limit 5/min", (455, 190, 975, 265)),
        ("GET /api/data\nJWT middleware -> user_id scope\noutput encoding (HTML escape)", (455, 285, 975, 370)),
        ("POST /api/posts\nvalidation + parameterised INSERT\nownership enforced by g.current_user", (455, 390, 975, 475)),
    ]
    for text, xy in routes:
        box(draw, xy, "white", (120, 150, 180), width=2, radius=8)
        centered(draw, xy, text, font(17))

    box(draw, (430, 610, 1000, 710), (240, 248, 240), (60, 120, 70))
    centered(draw, (430, 610, 1000, 710), "Security headers | CSP default-src 'none' | no-store | no debug", font(17))

    box(draw, (1120, 250, 1430, 430), LIGHT, BLUE)
    centered(draw, (1120, 250, 1430, 430), "SQLite\nusers / posts\n\nPRAGMA foreign_keys\nWAL", font(20))

    box(draw, (1120, 500, 1430, 650), (255, 250, 235), (150, 110, 30))
    centered(draw, (1120, 500, 1430, 650), "CI pipeline\npytest | Bandit SAST\npip-audit SCA", font(19))

    arrow(draw, (330, 225), (430, 225))
    draw.text((336, 188), "JSON/HTTPS", font=font(13), fill=GREY)
    arrow(draw, (1000, 320), (1120, 320))
    draw.text((1005, 285), "bound params", font=font(13), fill=GREY)

    draw.text(
        (60, 780),
        "Every data query is scoped by the authenticated user id; no object id is accepted from the client.",
        font=font(17),
        fill=GREY,
    )
    image.save(os.path.join(OUT, "architecture.png"))


def cve_flow():
    image = Image.new("RGB", (1600, 1060), "white")
    draw = ImageDraw.Draw(image)
    draw.text((60, 36), "CVE-2022-29078 - from query parameter to code execution", font=font(32, True), fill=RED)

    steps = [
        ("1. Attacker request", "GET /?settings[view options]\n[outputFunctionName]=x;<payload>;s", RED_LIGHT),
        ("2. Express route", "res.render('index', req.query)\nwhole query object becomes options", LIGHT),
        ("3. EJS renderFile", "shallowCopy(opts, data.settings['view options'])\ninternal compiler options overwritten", LIGHT),
        ("4. Template compile", "prepended += 'var ' + outputFunctionName + ' = __append;'", LIGHT),
        ("5. new Function(src)", "var x; <payload>; s = __append;", RED_LIGHT),
        ("6. Impact", "execSync('whoami > pwned.txt')\nRCE during compilation, HTTP still 200", RED_LIGHT),
    ]
    y = 110
    boxes = []
    for title, code, fill in steps:
        xy = (120, y, 1480, y + 110)
        box(draw, xy, fill, RED if fill is RED_LIGHT else BLUE, width=2, radius=10)
        draw.text((145, y + 18), title, font=font(21, True), fill=RED if fill is RED_LIGHT else BLUE)
        draw.multiline_text((145, y + 52), code, font=font(18, mono=True), fill=DARK, spacing=4)
        boxes.append(xy)
        y += 145

    for i in range(len(boxes) - 1):
        arrow(draw, (800, boxes[i][3]), (800, boxes[i + 1][1]), color=GREY, width=3)

    draw.text(
        (120, 1005),
        "Fix: EJS 3.1.7 validates the identifier (^[A-Za-z_$][A-Za-z0-9_$]*$) + app passes only scalar data.",
        font=font(18),
        fill=GREY,
    )
    image.save(os.path.join(OUT, "cve-flow.png"))


if __name__ == "__main__":
    architecture()
    cve_flow()
    print("figures written to", OUT)
