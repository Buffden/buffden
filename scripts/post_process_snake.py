#!/usr/bin/env python3
"""
Post-processes Platane/snk snake SVGs to add glitter and wiggle animations.
Run after snk generates the files, before deploying to the output branch.
"""
import re
import sys
from pathlib import Path


EXTRA_CSS = """\

  /* --- glitter & wiggle --- */
  @keyframes wiggle {
    0%,100% { transform: translateX(0) translateY(0) rotate(0deg); }
    15%      { transform: translateX(1.2px) translateY(-0.4px) rotate(0.15deg); }
    30%      { transform: translateX(-0.8px) translateY(0.6px) rotate(-0.1deg); }
    45%      { transform: translateX(0.9px) translateY(0.3px) rotate(0.12deg); }
    60%      { transform: translateX(-1.1px) translateY(-0.5px) rotate(-0.08deg); }
    75%      { transform: translateX(0.6px) translateY(0.4px) rotate(0.06deg); }
  }
  @keyframes glitter {
    0%,100% { opacity: 0; transform: scale(0) rotate(0deg); }
    50%      { opacity: 0.9; transform: scale(1) rotate(45deg); }
  }
  .snk-wiggle  { animation: wiggle 5s ease-in-out infinite; transform-origin: center; }
  .snk-sparkle { animation: glitter ease-in-out infinite; }
"""


def make_sparkles(width: float, height: float) -> str:
    """Scatter 4-pointed star sparkles across the SVG area."""
    positions = [
        (0.08, 0.35), (0.15, 0.70), (0.22, 0.45), (0.30, 0.20), (0.38, 0.60),
        (0.45, 0.35), (0.52, 0.75), (0.60, 0.25), (0.68, 0.55), (0.75, 0.40),
        (0.82, 0.65), (0.90, 0.30), (0.12, 0.55), (0.35, 0.80), (0.55, 0.15),
        (0.70, 0.70), (0.85, 0.45), (0.25, 0.30), (0.48, 0.55), (0.63, 0.40),
    ]
    delays    = [0.0, 0.4, 0.8, 1.2, 1.6, 2.0, 2.4, 0.2, 0.6, 1.0,
                 1.4, 1.8, 2.2, 0.3, 0.7, 1.1, 1.5, 1.9, 2.3, 0.5]
    durations = [1.2, 1.5, 1.8, 1.3, 1.6, 2.0, 1.4, 1.7, 1.9, 1.2,
                 1.5, 1.8, 1.3, 1.6, 2.0, 1.4, 1.7, 1.1, 1.8, 1.3]
    colors    = ["#fff", "#a3f7c5", "#39d353", "#fff", "#a3f7c5",
                 "#fff", "#39d353", "#a3f7c5", "#fff", "#39d353",
                 "#fff", "#a3f7c5", "#fff", "#39d353", "#a3f7c5",
                 "#fff", "#39d353", "#fff", "#a3f7c5", "#fff"]

    lines = ['  <g class="snk-sparkles">']
    for i, (px, py) in enumerate(positions):
        x = round(px * width, 1)
        y = round(py * height, 1)
        delay = delays[i % len(delays)]
        dur   = durations[i % len(durations)]
        color = colors[i % len(colors)]
        s  = 2.5 if i % 3 == 0 else 1.8        # arm length
        sd = round(s * 0.6, 1)                  # diagonal arm length
        lines.append(
            f'    <g class="snk-sparkle"'
            f' style="animation-delay:{delay}s;animation-duration:{dur}s"'
            f' transform="translate({x},{y})">'
            f'<line x1="-{s}" y1="0" x2="{s}" y2="0"'
            f' stroke="{color}" stroke-width="0.8" stroke-linecap="round"/>'
            f'<line x1="0" y1="-{s}" x2="0" y2="{s}"'
            f' stroke="{color}" stroke-width="0.8" stroke-linecap="round"/>'
            f'<line x1="-{sd}" y1="-{sd}" x2="{sd}" y2="{sd}"'
            f' stroke="{color}" stroke-width="0.5" stroke-linecap="round"/>'
            f'<line x1="{sd}" y1="-{sd}" x2="-{sd}" y2="{sd}"'
            f' stroke="{color}" stroke-width="0.5" stroke-linecap="round"/>'
            f'</g>'
        )
    lines.append('  </g>')
    return '\n'.join(lines)


def inject_animations(svg_text: str) -> str:
    # 1. Inject CSS into existing <style> block, or insert a new one after <svg ...>
    if '</style>' in svg_text:
        svg_text = svg_text.replace('</style>', EXTRA_CSS + '  </style>', 1)
    else:
        svg_text = re.sub(
            r'(<svg[^>]*>)',
            r'\1\n  <style>' + EXTRA_CSS + '  </style>',
            svg_text, count=1,
        )

    # 2. Extract dimensions for sparkle placement
    width, height = 890.0, 200.0
    m = re.search(r'viewBox=["\']0 0 ([\d.]+) ([\d.]+)["\']', svg_text)
    if m:
        width, height = float(m.group(1)), float(m.group(2))
    else:
        mw = re.search(r'<svg[^>]+width=["\'](\d+)["\']', svg_text)
        mh = re.search(r'<svg[^>]+height=["\'](\d+)["\']', svg_text)
        if mw:
            width = float(mw.group(1))
        if mh:
            height = float(mh.group(1))

    # 3. Add wiggle class to the first <g> that isn't already tagged
    svg_text = re.sub(r'<g(?!\s+class="snk)', '<g class="snk-wiggle"', svg_text, count=1)

    # 4. Inject sparkle overlay just before </svg>
    sparkles = make_sparkles(width, height)
    svg_text = svg_text.replace('</svg>', sparkles + '\n</svg>', 1)

    return svg_text


def process_file(path: Path) -> None:
    text = path.read_text(encoding='utf-8')
    path.write_text(inject_animations(text), encoding='utf-8')
    print(f"Injected glitter + wiggle → {path}", file=sys.stderr)


if __name__ == '__main__':
    targets = [
        Path('dist/github-snake.svg'),
        Path('dist/github-snake-dark.svg'),
    ]
    for t in targets:
        if t.exists():
            process_file(t)
        else:
            print(f"Skipping (not found): {t}", file=sys.stderr)
