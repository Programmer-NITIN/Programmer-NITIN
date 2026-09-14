#!/usr/bin/env python3
"""
isocalendar.py - generate a real, animated 3D isometric GitHub contribution calendar.
Stdlib only. Supports live scraping or GraphQL API, customizable building animations,
height adjustments, and themes.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

PALETTES = {
    "github": {
        "empty": "#ebedf0",
        "L1": "#9be9a8",
        "L2": "#40c463",
        "L3": "#30a14e",
        "L4": "#216e39",
    },
    "emerald": {
        "empty": "#161b22",
        "L1": "#0e4429",
        "L2": "#006d32",
        "L3": "#26a641",
        "L4": "#39d353",
    },
    "halloween": {
        "empty": "#ebedf0",
        "L1": "#ffee4a",
        "L2": "#ffc501",
        "L3": "#fe9600",
        "L4": "#03001c",
    },
    "winter": {
        "empty": "#ebedf0",
        "L1": "#b6e3ff",
        "L2": "#54aeff",
        "L3": "#0969da",
        "L4": "#0a3069",
    },
    "cyberpunk": {
        "empty": "#161b22",
        "L1": "#005577",
        "L2": "#00a8cc",
        "L3": "#00f0ff",
        "L4": "#ff007f",
    },
}


def fetch_contributions_html(username: str) -> tuple[list[dict], int]:
    """Scrapes public GitHub contribution calendar HTML."""
    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8")

    total_m = re.search(
        r"([0-9,]+)\s+contributions?\s+in\s+(?:the\s+last\s+year|\d{4})", html
    )
    total_contribs = int(total_m.group(1).replace(",", "")) if total_m else 0

    # Extract all td elements
    # Format: id="contribution-day-component-C-R" data-date="YYYY-MM-DD" data-level="L"
    pattern = (
        r'id="contribution-day-component-(\d+)-(\d+)"[^>]*'
        r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d+)"'
    )
    matches = re.findall(pattern, html)
    if not matches:
        pattern = (
            r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*'
            r'id="contribution-day-component-(\d+)-(\d+)"[^>]*data-level="(\d+)"'
        )
        alt = re.findall(pattern, html)
        matches = [(m[1], m[2], m[0], m[3]) for m in alt]

    # Map tooltips: id="contribution-day-component-C-R-tool-tip">N contribution(s) on ...
    tooltip_pat = r'id="contribution-day-component-(\d+)-(\d+)-tool-tip"[^>]*>([^<]+)'
    tooltip_matches = re.findall(tooltip_pat, html)
    counts_map = {}
    for col, row, tip in tooltip_matches:
        m = re.search(r"^(\d+)\s+contribution", tip.strip())
        counts_map[(int(col), int(row))] = int(m.group(1)) if m else 0

    days = []
    for col_str, row_str, date_str, level_str in matches:
        c, r = int(col_str), int(row_str)
        lvl = int(level_str)
        cnt = counts_map.get((c, r), lvl * 2 if lvl > 0 else 0)
        days.append(
            {
                "col": c,
                "row": r,
                "date": date_str,
                "level": lvl,
                "count": cnt,
            }
        )

    # Sort in temporal order (by col, then by row)
    days.sort(key=lambda d: (d["col"], d["row"]))
    return days, total_contribs


def compute_streaks(days: list[dict]) -> tuple[int, int, int, float]:
    """Returns (current_streak, best_streak, highest_day, avg_per_day)."""
    if not days:
        return 0, 0, 0, 0.0

    current_streak = 0
    best_streak = 0
    running = 0
    highest = 0
    total_count = sum(d["count"] for d in days)

    for d in days:
        cnt = d["count"]
        if cnt > highest:
            highest = cnt
        if cnt > 0:
            running += 1
            if running > best_streak:
                best_streak = running
        else:
            running = 0

    # Calculate current streak ending today/yesterday
    # Scan backwards
    rev = list(reversed(days))
    # If latest day is 0, allow yesterday to be the current streak end
    idx = 0
    if rev and rev[0]["count"] == 0:
        idx = 1
    while idx < len(rev) and rev[idx]["count"] > 0:
        current_streak += 1
        idx += 1

    avg_per_day = total_count / max(len(days), 1)
    return current_streak, best_streak, highest, avg_per_day


def generate_isocalendar_svg(
    days: list[dict],
    stats: dict,
    palette_name: str = "github",
    height_mult: float = 1.5,
    max_height: float = 24.0,
    animate: bool = True,
    duration: float = 1.2,
    stagger: float = 0.02,
    loop: bool = False,
) -> str:
    """Generates the full animated 3D isometric contribution calendar SVG."""
    palette = PALETTES.get(palette_name, PALETTES["github"])
    level_colors = {
        0: palette["empty"],
        1: palette["L1"],
        2: palette["L2"],
        3: palette["L3"],
        4: palette["L4"],
    }

    # Group days by column (week)
    weeks: dict[int, list[dict]] = {}
    for d in days:
        weeks.setdefault(d["col"], []).append(d)

    num_weeks = max(weeks.keys()) + 1 if weeks else 53

    # CSS for building animation
    css_rules = []
    if animate:
        anim_fill = "both"
        iteration = "infinite alternate" if loop else "both"
        css_rules.append(
            f"@keyframes buildUp {{"
            f"  0% {{ transform: scaleY(0); opacity: 0.15; }}"
            f"  65% {{ opacity: 1; }}"
            f"  100% {{ transform: scaleY(1); opacity: 1; }}"
            f"}}"
        )
        css_rules.append(
            f".bldg {{ animation: buildUp {duration:.2f}s cubic-bezier(0.16, 1, 0.3, 1) {iteration}; }}"
        )
        for w in range(num_weeks):
            delay = w * stagger
            css_rules.append(f".w{w} {{ animation-delay: {delay:.3f}s; }}")

    style_block = f"<style>{''.join(css_rules)}</style>" if css_rules else ""

    svg_parts = []
    svg_parts.append(
        '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="330" class="">'
    )
    svg_parts.append("    <defs>")
    svg_parts.append(style_block)
    svg_parts.append("    </defs>")
    svg_parts.append(
        """    <style>
svg { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; color: #777; }
h2, h3 { margin: 8px 0 2px; padding: 0; color: #0366d6; font-weight: 400; }
h2 svg, h3 svg { fill: currentColor; }
h2 { font-size: 16px; }
h3, svg { font-size: 14px; }
section > .field { margin-left: 5px; margin-right: 5px; }
.field { display: flex; align-items: center; margin-bottom: 2px; white-space: nowrap; }
.field svg { margin: 0 8px; fill: #959da5; flex-shrink: 0; }
.row { display: flex; flex-wrap: wrap; }
.row section { flex: 1 1 0; }
</style>"""
    )
    svg_parts.append('    <foreignObject x="0" y="0" width="100%" height="100%">')
    svg_parts.append(
        '        <div xmlns="http://www.w3.org/1999/xhtml" class="items-wrapper">'
    )
    svg_parts.append("            <section>")
    svg_parts.append('                <h2 class="field">')
    svg_parts.append(
        '                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16">'
    )
    svg_parts.append(
        '                        <path fill-rule="evenodd" d="M4.75 0a.75.75 0 01.75.75V2h5V.75a.75.75 0 011.5 0V2h1.25c.966 0 1.75.784 1.75 1.75v10.5A1.75 1.75 0 0113.25 16H2.75A1.75 1.75 0 011 14.25V3.75C1 2.784 1.784 2 2.75 2H4V.75A.75.75 0 014.75 0zm0 3.5h8.5a.25.25 0 01.25.25V6h-11V3.75a.25.25 0 01.25-.25h2zm-2.25 4v6.75c0 .138.112.25.25.25h10.5a.25.25 0 00.25-.25V7.5h-11z"/>'
    )
    svg_parts.append("                    </svg>")
    svg_parts.append("                    Contributions calendar")
    svg_parts.append("                </h2>")
    svg_parts.append('                <div class="row">')
    svg_parts.append("                    <section></section>")
    svg_parts.append("                    <section>")
    svg_parts.append('                        <h3 class="field">')
    svg_parts.append(
        '                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16">'
    )
    svg_parts.append(
        '                                <path fill-rule="evenodd" d="M7.75 14A1.75 1.75 0 016 12.25v-8.5C6 2.784 6.784 2 7.75 2h6.5c.966 0 1.75.784 1.75 1.75v8.5A1.75 1.75 0 0114.25 14h-6.5zm-.25-1.75c0 .138.112.25.25.25h6.5a.25.25 0 00.25-.25v-8.5a.25.25 0 00-.25-.25h-6.5a.25.25 0 00-.25.25v8.5zM4.9 3.508a.75.75 0 01-.274 1.025.25.25 0 00-.126.217v6.5a.25.25 0 00.126.217.75.75 0 01-.752 1.298A1.75 1.75 0 013 11.25v-6.5c0-.649.353-1.214.874-1.516a.75.75 0 011.025.274zM1.625 5.533a.75.75 0 10-.752-1.299A1.75 1.75 0 000 5.75v4.5c0 .649.353 1.214.874 1.515a.75.75 0 10.752-1.298.25.25 0 01-.126-.217v-4.5a.25.25 0 01.126-.217z"/>'
    )
    svg_parts.append("                            </svg>")
    svg_parts.append("                            Commits streaks")
    svg_parts.append("                        </h3>")
    svg_parts.append('                        <div class="field">')
    svg_parts.append(
        '                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16">'
    )
    svg_parts.append(
        '                                <path fill-rule="evenodd" d="M7.998 14.5c2.832 0 5-1.98 5-4.5 0-1.463-.68-2.19-1.879-3.383l-.036-.037c-1.013-1.008-2.3-2.29-2.834-4.434-.322.256-.63.579-.864.953-.432.696-.621 1.58-.046 2.73.473.947.67 2.284-.278 3.232-.61.61-1.545.84-2.403.633a2.788 2.788 0 01-1.436-.874A3.21 3.21 0 003 10c0 2.53 2.164 4.5 4.998 4.5zM9.533.753C9.496.34 9.16.009 8.77.146 7.035.75 4.34 3.187 5.997 6.5c.344.689.285 1.218.003 1.5-.419.419-1.54.487-2.04-.832-.173-.454-.659-.762-1.035-.454C2.036 7.44 1.5 8.702 1.5 10c0 3.512 2.998 6 6.498 6s6.5-2.5 6.5-6c0-2.137-1.128-3.26-2.312-4.438-1.19-1.184-2.436-2.425-2.653-4.81z"/>'
    )
    svg_parts.append("                            </svg>")
    svg_parts.append(
        f'                            Current streak {stats["current_streak"]} days'
    )
    svg_parts.append("                        </div>")
    svg_parts.append('                        <div class="field">')
    svg_parts.append(
        '                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16">'
    )
    svg_parts.append(
        '                                <path d="M8.5.75a.75.75 0 00-1.5 0v5.19L4.391 3.33a.75.75 0 10-1.06 1.061L5.939 7H.75a.75.75 0 000 1.5h5.19l-2.61 2.609a.75.75 0 101.061 1.06L7 9.561v5.189a.75.75 0 001.5 0V9.56l2.609 2.61a.75.75 0 101.06-1.061L9.561 8.5h5.189a.75.75 0 000-1.5H9.56l2.61-2.609a.75.75 0 00-1.061-1.06L8.5 5.939V.75z"/>'
    )
    svg_parts.append("                            </svg>")
    svg_parts.append(
        f'                            Best streak {stats["best_streak"]} days'
    )
    svg_parts.append("                        </div>")
    svg_parts.append('                        <h3 class="field">')
    svg_parts.append(
        '                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16">'
    )
    svg_parts.append(
        '                                <path fill-rule="evenodd" d="M10.5 7.75a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0zm1.43.75a4.002 4.002 0 01-7.86 0H.75a.75.75 0 110-1.5h3.32a4.001 4.001 0 017.86 0h3.32a.75.75 0 110 1.5h-3.32z"/>'
    )
    svg_parts.append("                            </svg>")
    svg_parts.append("                            Commits per day")
    svg_parts.append("                        </h3>")
    svg_parts.append('                        <div class="field">')
    svg_parts.append(
        '                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16">'
    )
    svg_parts.append(
        '                                <path d="M7.823 1.677L4.927 4.573A.25.25 0 005.104 5H7.25v3.236a.75.75 0 101.5 0V5h2.146a.25.25 0 00.177-.427L8.177 1.677a.25.25 0 00-.354 0zM13.75 11a.75.75 0 000 1.5h.5a.75.75 0 000-1.5h-.5zm-3.75.75a.75.75 0 01.75-.75h.5a.75.75 0 010 1.5h-.5a.75.75 0 01-.75-.75zM7.75 11a.75.75 0 000 1.5h.5a.75.75 0 000-1.5h-.5zM4 11.75a.75.75 0 01.75-.75h.5a.75.75 0 010 1.5h-.5a.75.75 0 01-.75-.75zM1.75 11a.75.75 0 000 1.5h.5a.75.75 0 000-1.5h-.5z"/>'
    )
    svg_parts.append("                            </svg>")
    svg_parts.append(
        f'                            Highest in a day at {stats["highest_day"]}'
    )
    svg_parts.append("                        </div>")
    svg_parts.append('                        <div class="field">')
    svg_parts.append(
        '                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16">'
    )
    svg_parts.append(
        '                                <path d="M10.896 2H8.75V.75a.75.75 0 00-1.5 0V2H5.104a.25.25 0 00-.177.427l2.896 2.896a.25.25 0 00.354 0l2.896-2.896A.25.25 0 0010.896 2zM8.75 15.25a.75.75 0 01-1.5 0V14H5.104a.25.25 0 01-.177-.427l2.896-2.896a.25.25 0 01.354 0l2.896 2.896a.25.25 0 01-.177.427H8.75v1.25zm-6.5-6.5a.75.75 0 000-1.5h-.5a.75.75 0 000 1.5h.5zM6 8a.75.75 0 01-.75.75h-.5a.75.75 0 010-1.5h.5A.75.75 0 016 8zm2.25.75a.75.75 0 000-1.5h-.5a.75.75 0 000 1.5h.5zM12 8a.75.75 0 01-.75.75h-.5a.75.75 0 010-1.5h.5A.75.75 0 0112 8zm2.25.75a.75.75 0 000-1.5h-.5a.75.75 0 000 1.5h.5z"/>'
    )
    svg_parts.append("                            </svg>")
    svg_parts.append(
        f'                            Average per day at ~{stats["avg_per_day"]:.2f}'
    )
    svg_parts.append("                        </div>")
    svg_parts.append("                    </section>")
    svg_parts.append("                </div>")

    # 3D Isometric Viewport
    svg_parts.append(
        '                <svg version="1.1" xmlns="http://www.w3.org/2000/svg" style="margin-top: -130px;" viewBox="0,0 480,270">'
    )
    svg_parts.append('                    <filter id="brightness1">')
    svg_parts.append("                        <feComponentTransfer>")
    svg_parts.append(
        '                            <feFuncR type="linear" slope="0.6"/>'
    )
    svg_parts.append(
        '                            <feFuncG type="linear" slope="0.6"/>'
    )
    svg_parts.append(
        '                            <feFuncB type="linear" slope="0.6"/>'
    )
    svg_parts.append("                        </feComponentTransfer>")
    svg_parts.append("                    </filter>")
    svg_parts.append('                    <filter id="brightness2">')
    svg_parts.append("                        <feComponentTransfer>")
    svg_parts.append(
        '                            <feFuncR type="linear" slope="0.2"/>'
    )
    svg_parts.append(
        '                            <feFuncG type="linear" slope="0.2"/>'
    )
    svg_parts.append(
        '                            <feFuncB type="linear" slope="0.2"/>'
    )
    svg_parts.append("                        </feComponentTransfer>")
    svg_parts.append("                    </filter>")
    svg_parts.append('                    <g transform="scale(4) translate(12, 0)">')

    # Render week by week
    for col_idx in range(num_weeks):
        col_days = weeks.get(col_idx, [])
        # Week base translation: col_x = 6.8 * col_idx, col_y = 4.0 * col_idx
        w_x = col_idx * 6.8
        w_y = col_idx * 4.0
        svg_parts.append(f'                        <g transform="translate({w_x:.1f}, {w_y:.1f})">')

        for d in col_days:
            row_idx = d["row"]
            lvl = d["level"]
            cnt = d["count"]

            # Ground coordinates for this day within the week
            base_dx = -1.7 * row_idx
            base_dy = 6.0 + 1.0 * row_idx

            # 1. Ground diamond (always present as base floor)
            svg_parts.append(f'                            <g transform="translate({base_dx:.1f}, {base_dy:.1f})">')
            svg_parts.append(f'                                <path fill="{palette["empty"]}" d="M1.7,2 0,1 1.7,0 3.4,1 z"/>')
            svg_parts.append(f'                                <path fill="{palette["empty"]}" filter="url(#brightness1)" d="M0,1 1.7,2 1.7,2 0,1 z"/>')
            svg_parts.append(f'                                <path fill="{palette["empty"]}" filter="url(#brightness2)" d="M1.7,2 3.4,1 3.4,1 1.7,2 z"/>')
            svg_parts.append('                            </g>')

            # 2. 3D Building block if contributions > 0
            if lvl > 0:
                # Calculate building height based on level & count
                if lvl == 1:
                    raw_h = 0.8 + 0.3 * min(cnt, 2)
                elif lvl == 2:
                    raw_h = 1.6 + 0.4 * min(cnt, 4)
                elif lvl == 3:
                    raw_h = 3.0 + 0.5 * min(cnt, 8)
                else:  # lvl 4
                    raw_h = 4.8 + 0.6 * min(cnt, 15)

                h = min(raw_h * height_mult, max_height)
                col_color = level_colors[lvl]

                # Raised top Y coordinate
                top_dy = base_dy - h

                # Transform origin is the base center point in the week group coordinate space
                origin_x = base_dx + 1.7
                origin_y = base_dy + 1.0

                anim_class = f"bldg w{col_idx} d{row_idx}" if animate else ""
                origin_style = f' style="transform-origin: {origin_x:.2f}px {origin_y:.2f}px;"' if animate else ""

                svg_parts.append(f'                            <g class="{anim_class}"{origin_style} transform="translate({base_dx:.1f}, {top_dy:.2f})">')
                # Top diamond
                svg_parts.append(f'                                <path fill="{col_color}" d="M1.7,2 0,1 1.7,0 3.4,1 z"/>')
                # Left shaded face
                svg_parts.append(f'                                <path fill="{col_color}" filter="url(#brightness1)" d="M0,1 1.7,2 1.7,{2.0 + h:.2f} 0,{1.0 + h:.2f} z"/>')
                # Right shaded face
                svg_parts.append(f'                                <path fill="{col_color}" filter="url(#brightness2)" d="M1.7,2 3.4,1 3.4,{1.0 + h:.2f} 1.7,{2.0 + h:.2f} z"/>')
                svg_parts.append('                            </g>')

        svg_parts.append('                        </g>')

    svg_parts.append('                    </g>')
    svg_parts.append('                </svg>')
    svg_parts.append('            </section>')
    svg_parts.append('        </div>')
    svg_parts.append('    </foreignObject>')
    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


def main():
    parser = argparse.ArgumentParser(description="Generate 3D isometric contribution calendar SVG.")
    parser.add_argument("--user", default="Programmer-NITIN", help="GitHub username")
    parser.add_argument("--config", default="assets/calendar.json", help="Path to config JSON")
    parser.add_argument("-o", "--out", default="assets/metrics.isocalendar.svg", help="Output SVG path")
    parser.add_argument("--height", type=float, default=None, help="Height multiplier for 3D buildings")
    parser.add_argument("--duration", type=float, default=None, help="Animation duration in seconds")
    parser.add_argument("--stagger", type=float, default=None, help="Animation stagger delay per week in seconds")
    parser.add_argument("--palette", choices=list(PALETTES.keys()), default=None, help="Color palette")
    parser.add_argument("--loop", action="store_true", help="Loop animation infinitely")
    parser.add_argument("--no-anim", action="store_true", help="Disable building animation")

    args = parser.parse_args()

    # Load defaults from config if available
    cfg = {}
    config_path = Path(args.config)
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception as e:
            print(f"Warning: could not read {config_path}: {e}")

    username = args.user or cfg.get("username", "Programmer-NITIN")
    anim_cfg = cfg.get("animation", {})
    animate = False if args.no_anim else anim_cfg.get("enabled", True)
    duration = args.duration or anim_cfg.get("duration", 1.2)
    stagger = args.stagger or anim_cfg.get("stagger", 0.02)
    loop = args.loop or anim_cfg.get("loop", False)
    height_mult = args.height or cfg.get("height_multiplier", 1.5)
    max_height = cfg.get("max_height", 24.0)
    palette_name = args.palette or cfg.get("palette", "github")

    print(f"Fetching live GitHub contributions for @{username}...")
    days, total_contribs = fetch_contributions_html(username)
    print(f"Loaded {len(days)} calendar days ({total_contribs} contributions)")

    c_streak, b_streak, highest, avg_day = compute_streaks(days)
    
    # Check overrides
    streaks_cfg = cfg.get("streaks", {})
    if streaks_cfg.get("override_current") is not None:
        c_streak = streaks_cfg["override_current"]
    if streaks_cfg.get("override_best") is not None:
        b_streak = streaks_cfg["override_best"]
    if streaks_cfg.get("override_highest") is not None:
        highest = streaks_cfg["override_highest"]
    if streaks_cfg.get("override_average") is not None:
        avg_day = streaks_cfg["override_average"]

    stats = {
        "current_streak": c_streak,
        "best_streak": b_streak,
        "highest_day": highest,
        "avg_per_day": avg_day,
        "total": total_contribs,
    }
    print(f"Stats: Current streak {c_streak}d, Best {b_streak}d, Highest {highest}, Avg {avg_day:.2f}")

    svg_content = generate_isocalendar_svg(
        days=days,
        stats=stats,
        palette_name=palette_name,
        height_mult=height_mult,
        max_height=max_height,
        animate=animate,
        duration=duration,
        stagger=stagger,
        loop=loop,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print(f"wrote {out_path} ({len(svg_content) // 1024} KB)")


if __name__ == "__main__":
    main()
