"""Crop and combine the captured GitHub screenshots for the report."""

from pathlib import Path

from PIL import Image

D = Path(__file__).resolve().parent / "images" / "screenshots"


def crop(name: str, box: tuple[int, int, int, int]) -> Image.Image:
    return Image.open(D / name).crop(box)


def stack(images: list[Image.Image], out: str) -> None:
    width = max(image.width for image in images)
    height = sum(image.height for image in images) + 20 * (len(images) - 1)
    canvas = Image.new("RGB", (width, height), "white")
    y = 0
    for image in images:
        canvas.paste(image, (0, y))
        y += image.height + 20
    canvas.save(D / out)


ci = crop("ci-main.png", (0, 145, 1440, 690))
docker = crop("docker-log.png", (0, 145, 1440, 900))
pwned = crop("pwned.png", (0, 145, 1440, 460))
fixed = crop("fixed-log.png", (0, 145, 1440, 450))

stack([ci, docker], "combined-ci.png")
stack([pwned, fixed], "combined-cve.png")
print("wrote combined-ci.png and combined-cve.png")
