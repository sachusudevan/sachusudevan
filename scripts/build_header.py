#!/usr/bin/env python3
"""Generate assets/header.svg: binary-art avatar + matrix rain + typing terminal.

Usage: python3 scripts/build_header.py <avatar-image> [output.svg]

The SVG is fully self-contained (photo embedded as base64, CSS animations only,
no JS, no web fonts) because GitHub renders README images through <img>, which
blocks scripts and external resources inside SVGs.
"""
import base64
import io
import random
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageEnhance, ImageOps

W, H = 1000, 320
CX, CY, R = 170, 160, 118          # avatar circle
COLS = 52                          # binary portrait resolution (characters across)
GREEN = "#39ff14"
CYAN = "#36bcf7"
BG = "#0d1117"
MONO = "'Fira Code','JetBrains Mono',Consolas,'Courier New',monospace"

TERMINAL_LINES = [
    ("$ whoami", "Sachu S — Full Stack Developer"),
    ("$ cat stack.txt", "Python · Django · GraphQL · JavaScript · React Native"),
    ("$ echo $FOCUS", "Building scalable backends & APIs"),
]

random.seed(42)  # deterministic output -> clean git diffs on regeneration


def load_avatar(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGB")
    side = min(img.size)
    img = ImageOps.fit(img, (side, side), centering=(0.5, 0.35))
    return img.resize((R * 4, R * 4), Image.LANCZOS)


def photo_data_uri(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def binary_portrait(img: Image.Image) -> str:
    """Render the avatar as 0/1 glyphs whose brightness follows the photo."""
    gray = ImageOps.autocontrast(ImageEnhance.Contrast(img.convert("L")).enhance(1.6))
    cell = (2 * R) / COLS
    rows = int((2 * R) / (cell * 1.25))
    small = gray.resize((COLS, rows), Image.LANCZOS)
    out = []
    for r in range(rows):
        y = CY - R + (r + 0.8) * cell * 1.25
        spans = []
        for c in range(COLS):
            x = CX - R + (c + 0.5) * cell
            if (x - CX) ** 2 + (y - CY) ** 2 > (R - 4) ** 2:
                continue
            lum = (small.getpixel((c, r)) / 255) ** 0.7   # lift mid-tones (dark suit/background)
            level = min(4, int(lum * 5))                   # 5 brightness classes, 0 = faint
            spans.append(f'<tspan x="{x:.1f}" class="l{level}">{random.choice("01")}</tspan>')
        if spans:
            out.append(f'<text y="{y:.1f}">{"".join(spans)}</text>')
    return "\n".join(out)


def matrix_rain() -> str:
    cols = []
    for i in range(34):
        x = 330 + i * 20 + random.randint(-3, 3)
        if 352 < x < 978 and i % 3:  # keep rain sparse behind the terminal
            continue
        digits = "".join(random.choice("01") for _ in range(22))
        dur = random.uniform(6, 13)
        delay = -random.uniform(0, dur)
        chars = "".join(f'<tspan x="{x}" dy="15">{d}</tspan>' for d in digits)
        cols.append(
            f'<text class="rain" y="-330" style="animation-duration:{dur:.1f}s;'
            f'animation-delay:{delay:.1f}s;opacity:{random.uniform(.15, .45):.2f}">{chars}</text>'
        )
    # rain on the far left/right edges around the avatar too
    for x in (12, 28, 312, 984):
        digits = "".join(random.choice("01") for _ in range(22))
        dur = random.uniform(7, 12)
        chars = "".join(f'<tspan x="{x}" dy="15">{d}</tspan>' for d in digits)
        cols.append(
            f'<text class="rain" y="-330" style="animation-duration:{dur:.1f}s;'
            f'animation-delay:-{random.uniform(0, dur):.1f}s;opacity:.3">{chars}</text>'
        )
    return "\n".join(cols)


def terminal() -> str:
    x0, y0, w, h = 360, 40, 610, 240
    parts = [
        f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="10" fill="#010409" fill-opacity=".88" stroke="#30363d"/>',
        f'<rect x="{x0}" y="{y0}" width="{w}" height="30" rx="10" fill="#161b22"/>',
        f'<rect x="{x0}" y="{y0 + 20}" width="{w}" height="10" fill="#161b22"/>',
        *(f'<circle cx="{x0 + 20 + i * 18}" cy="{y0 + 15}" r="5.5" fill="{c}"/>'
          for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f"))),
        f'<text x="{x0 + w / 2}" y="{y0 + 20}" class="title">sachusudevan@github: ~</text>',
    ]
    # each line is revealed by a clip rect whose width animates in steps (typing effect)
    t, y = 0.4, y0 + 66
    char_w = 9.6
    for i, (cmd, result) in enumerate(TERMINAL_LINES):
        for j, (txt, cls) in enumerate(((cmd, "cmd"), (result, "out"))):
            dur = max(0.4, len(txt) * 0.05)
            cid = f"c{i}{j}"
            width = len(txt) * char_w + 4
            parts.append(
                f'<clipPath id="{cid}"><rect x="{x0 + 18}" y="{y - 16}" height="22" width="0">'
                f'<animate attributeName="width" from="0" to="{width:.0f}" begin="{t:.2f}s" '
                f'dur="{dur:.2f}s" fill="freeze" calcMode="discrete" '
                f'values="{";".join(f"{k * char_w:.0f}" for k in range(len(txt) + 1))}"/></rect></clipPath>'
            )
            parts.append(f'<text x="{x0 + 20}" y="{y}" class="{cls}" clip-path="url(#{cid})">{escape(txt)}</text>')
            t += dur + (0.25 if j == 0 else 0.5)
            y += 26 if j == 0 else 34
    parts.append(f'<text x="{x0 + 20}" y="{y}" class="cmd">$ <tspan class="cursor">█</tspan></text>')
    return "\n".join(parts)


def build(avatar_path: Path) -> str:
    img = load_avatar(avatar_path)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Sachu S - Full Stack Developer">
<title>Sachu S - Full Stack Developer</title>
<style>
  text {{ font-family: {MONO}; }}
  .rain {{ fill: {GREEN}; font-size: 13px; animation: fall linear infinite; }}
  @keyframes fall {{ from {{ transform: translateY(0); }} to {{ transform: translateY(660px); }} }}
  .bin text {{ font-size: {2 * R / COLS * 1.25:.1f}px; font-weight: 700; fill: {GREEN}; }}
  .l0 {{ fill-opacity: .1; }} .l1 {{ fill-opacity: .3; }} .l2 {{ fill-opacity: .55; }} .l3 {{ fill-opacity: .75; }} .l4 {{ fill-opacity: 1; }}
  .bin {{ animation: binFade 9s ease-in-out infinite; }}
  .photo {{ animation: photoFade 9s ease-in-out infinite; }}
  @keyframes binFade {{ 0%,30% {{ opacity: 1; }} 45%,85% {{ opacity: 0; }} 100% {{ opacity: 1; }} }}
  @keyframes photoFade {{ 0%,30% {{ opacity: 0; }} 45%,85% {{ opacity: 1; }} 100% {{ opacity: 0; }} }}
  .scan {{ animation: scan 3s linear infinite; }}
  @keyframes scan {{ from {{ transform: translateY(0); }} to {{ transform: translateY({2 * R}px); }} }}
  .ring {{ transform-origin: {CX}px {CY}px; animation: spin 14s linear infinite; }}
  .ring2 {{ transform-origin: {CX}px {CY}px; animation: spin 20s linear infinite reverse; }}
  @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
  .title {{ fill: #8b949e; font-size: 13px; text-anchor: middle; }}
  .cmd {{ fill: {GREEN}; font-size: 16px; }}
  .out {{ fill: {CYAN}; font-size: 16px; }}
  .cursor {{ animation: blink 1s step-end infinite; }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} .photo {{ opacity: 1; }} .bin {{ opacity: 0; }} }}
</style>
<defs>
  <clipPath id="avatar"><circle cx="{CX}" cy="{CY}" r="{R}"/></clipPath>
  <linearGradient id="scanGrad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{GREEN}" stop-opacity="0"/>
    <stop offset="1" stop-color="{GREEN}" stop-opacity=".22"/>
  </linearGradient>
  <filter id="glow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>
<g>{matrix_rain()}</g>
<g clip-path="url(#avatar)">
  <circle cx="{CX}" cy="{CY}" r="{R}" fill="#010409"/>
  <image class="photo" href="{photo_data_uri(img)}" x="{CX - R}" y="{CY - R}" width="{2 * R}" height="{2 * R}"/>
  <g class="bin">{binary_portrait(img)}</g>
  <rect class="scan" x="{CX - R}" y="{CY - R - 16}" width="{2 * R}" height="16" fill="url(#scanGrad)"/>
</g>
<circle class="ring" cx="{CX}" cy="{CY}" r="{R + 8}" fill="none" stroke="{GREEN}" stroke-width="2" stroke-dasharray="40 14 6 14" filter="url(#glow)"/>
<circle class="ring2" cx="{CX}" cy="{CY}" r="{R + 16}" fill="none" stroke="{CYAN}" stroke-opacity=".6" stroke-width="1.5" stroke-dasharray="2 10"/>
<text x="{CX}" y="{CY + R + 34}" fill="{GREEN}" font-size="12" text-anchor="middle" opacity=".8">&lt;/&gt; 01010011 01010011</text>
{terminal()}
</svg>
'''


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent.parent / "assets/header.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(Path(sys.argv[1])), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
