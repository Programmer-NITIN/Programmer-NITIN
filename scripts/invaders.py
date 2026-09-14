#!/usr/bin/env python3
"""
invaders.py - Generates an authentic, animated Retro Space Invaders / Arcade Galaga
Contribution Defense SVG powered by real live GitHub contribution data.
Stdlib only. Self-contained, responsive, dark/light adaptive.
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

    counts_map = {}
    tip_matches = re.findall(r'for="contribution-day-component-(\d+)-(\d+)"[^>]*>([^<]+)', html)
    if not tip_matches:
        tip_matches = re.findall(r'id="contribution-day-component-(\d+)-(\d+)-tool-tip"[^>]*>([^<]+)', html)
    for r_str, c_str, text in tip_matches:
        m = re.search(r"^(\d+)\s+contribution", text.strip())
        cnt = int(m.group(1)) if m else 0
        counts_map[(int(c_str), int(r_str))] = cnt

    alt_pat = r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*id="contribution-day-component-(\d+)-(\d+)"[^>]*data-level="(\d+)"'
    matches = re.findall(alt_pat, html)
    if not matches:
        pattern = r'id="contribution-day-component-(\d+)-(\d+)"[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d+)"'
        raw = re.findall(pattern, html)
        matches = [(m[2], m[0], m[1], m[3]) for m in raw]

    days = []
    for date_str, r_str, c_str, lvl_str in matches:
        r = int(r_str)
        c = int(c_str)
        lvl = int(lvl_str)
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

    days.sort(key=lambda d: d["date"])
    if total_contribs == 0:
        total_contribs = sum(d["count"] for d in days)
    return days, total_contribs


def generate_invaders_svg(days: list[dict], total_contribs: int, username: str = "Programmer-NITIN") -> str:
    """Renders the animated Retro Space Invaders Contribution Defense SVG."""
    weeks: dict[int, list[dict]] = {}
    for d in days:
        weeks.setdefault(d["col"], []).append(d)

    num_weeks = max(weeks.keys()) + 1 if weeks else 53
    max_day = max((d["count"] for d in days), default=36) or 36

    score = total_contribs * 100
    hi_score = max(score, max_day * 1000)

    # Grid geometry
    cell_size = 10
    cell_gap = 3.5
    step_x = cell_size + cell_gap  # 13.5
    step_y = cell_size + cell_gap  # 13.5

    grid_x0 = 68
    grid_y0 = 74

    width = 860
    height = 270

    # Pick 4 notable target positions for animated laser shots
    # High active columns in Nitin's history (e.g. recent active weeks)
    active_days = [d for d in days if d["count"] > 0]
    active_days.sort(key=lambda d: d["count"], reverse=True)
    top_targets = active_days[:5] if len(active_days) >= 5 else days[-5:]

    svg_parts = []
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">')
    
    # Defs: filters, gradients, pixel sprites
    svg_parts.append("""  <defs>
    <!-- Laser Glow Filter -->
    <filter id="laser-glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="2.5" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <filter id="alien-glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="1.5" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <!-- Pixel Space Invaders Sprites -->
    <!-- Squid (Top Tier Alien) 8x8 -->
    <g id="alien-squid">
      <rect x="3" y="0" width="2" height="1"/>
      <rect x="2" y="1" width="4" height="1"/>
      <rect x="1" y="2" width="6" height="1"/>
      <rect x="0" y="3" width="8" height="1"/>
      <rect x="0" y="4" width="2" height="1"/><rect x="6" y="4" width="2" height="1"/>
      <rect x="0" y="5" width="8" height="1"/>
      <rect x="1" y="6" width="2" height="1"/><rect x="5" y="6" width="2" height="1"/>
      <rect x="0" y="7" width="1" height="1"/><rect x="3" y="7" width="2" height="1"/><rect x="7" y="7" width="1" height="1"/>
    </g>

    <!-- Crab (Middle Tier Alien) 8x8 -->
    <g id="alien-crab">
      <rect x="2" y="0" width="1" height="1"/><rect x="5" y="0" width="1" height="1"/>
      <rect x="0" y="1" width="1" height="1"/><rect x="2" y="1" width="4" height="1"/><rect x="7" y="1" width="1" height="1"/>
      <rect x="0" y="2" width="8" height="1"/>
      <rect x="0" y="3" width="8" height="1"/>
      <rect x="1" y="4" width="6" height="1"/>
      <rect x="2" y="5" width="4" height="1"/>
      <rect x="1" y="6" width="1" height="1"/><rect x="6" y="6" width="1" height="1"/>
      <rect x="0" y="7" width="1" height="1"/><rect x="7" y="7" width="1" height="1"/>
    </g>

    <!-- Octopus (Standard Alien) 8x8 -->
    <g id="alien-octo">
      <rect x="2" y="0" width="4" height="1"/>
      <rect x="1" y="1" width="6" height="1"/>
      <rect x="0" y="2" width="8" height="1"/>
      <rect x="0" y="3" width="2" height="1"/><rect x="3" y="3" width="2" height="1"/><rect x="6" y="3" width="2" height="1"/>
      <rect x="0" y="4" width="8" height="1"/>
      <rect x="2" y="5" width="4" height="1"/>
      <rect x="1" y="6" width="2" height="1"/><rect x="5" y="6" width="2" height="1"/>
      <rect x="0" y="7" width="2" height="1"/><rect x="6" y="7" width="2" height="1"/>
    </g>

    <!-- Player Cannon Starship (24x14) -->
    <g id="player-ship">
      <!-- Cockpit laser cannon tip -->
      <rect x="11" y="0" width="2" height="4" fill="#39d353"/>
      <rect x="10" y="4" width="4" height="2" fill="#58a6ff"/>
      <!-- Main Hull -->
      <rect x="8" y="6" width="8" height="3" fill="#39d353"/>
      <rect x="4" y="9" width="16" height="3" fill="#39d353"/>
      <!-- Wings & Thrusters -->
      <rect x="1" y="12" width="22" height="2" fill="#58a6ff"/>
      <rect x="0" y="10" width="3" height="3" fill="#2ea043"/>
      <rect x="21" y="10" width="3" height="3" fill="#2ea043"/>
      <rect x="7" y="14" width="3" height="2" fill="#ff7b72"/>
      <rect x="14" y="14" width="3" height="2" fill="#ff7b72"/>
    </g>
  </defs>""")

    # Stylesheet with arcade scanlines, fonts, and dark/light support
    svg_parts.append("""  <style>
    /* <![CDATA[ */
    @keyframes crt-flicker {
      0%, 100% { opacity: 0.99; }
      50% { opacity: 0.96; }
    }
    @keyframes ship-patrol {
      0%   { transform: translateX(120px); }
      20%  { transform: translateX(380px); }
      45%  { transform: translateX(690px); }
      55%  { transform: translateX(720px); }
      75%  { transform: translateX(450px); }
      100% { transform: translateX(120px); }
    }
    @keyframes laser-shot-1 {
      0%   { transform: translate(710px, 205px); opacity: 0; }
      1%   { opacity: 1; }
      18%  { transform: translate(710px, 80px); opacity: 1; }
      19%  { transform: translate(710px, 80px); opacity: 0; }
      100% { transform: translate(710px, 80px); opacity: 0; }
    }
    @keyframes laser-shot-2 {
      0%, 25% { transform: translate(450px, 205px); opacity: 0; }
      26%  { opacity: 1; }
      42%  { transform: translate(450px, 110px); opacity: 1; }
      43%  { transform: translate(450px, 110px); opacity: 0; }
      100% { transform: translate(450px, 110px); opacity: 0; }
    }
    @keyframes burst-pulse {
      0%, 18% { transform: scale(0); opacity: 0; }
      19% { transform: scale(1.6); opacity: 1; }
      24% { transform: scale(2.2); opacity: 0; }
      100% { transform: scale(0); opacity: 0; }
    }
    @keyframes score-pop {
      0%, 18% { transform: translateY(0); opacity: 0; }
      20% { transform: translateY(-4px); opacity: 1; }
      26% { transform: translateY(-16px); opacity: 0; }
      100% { transform: translateY(0); opacity: 0; }
    }
    @keyframes alien-march {
      0%, 100% { transform: translateX(0); }
      50% { transform: translateX(2px); }
    }

    /* Typography and Palette */
    .arcade-font {
      font-family: ui-monospace, "Press Start 2P", "SF Mono", Monaco, Consolas, monospace;
      letter-spacing: 0.08em;
    }
    .hud-label { fill: #ff7b72; font-size: 11px; font-weight: 700; }
    .hud-val   { fill: #ffffff; font-size: 13px; font-weight: 700; }
    .hud-hi    { fill: #f2cc60; font-size: 13px; font-weight: 700; }
    .hud-title { fill: #39d353; font-size: 12px; font-weight: 700; letter-spacing: 0.15em; }

    /* Alien and Grid Colors - Dark Theme Defaults */
    .bg-cabinet { fill: #0d1117; stroke: #30363d; stroke-width: 1.5; }
    .bg-screen  { fill: #070a0f; }
    .cell-0 { fill: #161b22; opacity: 0.7; }
    .alien-1 { fill: #2ea043; }
    .alien-2 { fill: #3fb950; }
    .alien-3 { fill: #56d364; filter: url(#alien-glow); }
    .alien-4 { fill: #7ee787; filter: url(#alien-glow); }
    .grid-line { stroke: #1f242c; stroke-width: 0.5; stroke-dasharray: 2 2; }
    .star-dot { fill: #ffffff; opacity: 0.25; }

    /* Light Theme Adaptive Overrides */
    @media (prefers-color-scheme: light) {
      .bg-cabinet { fill: #f6f8fa; stroke: #d0d7de; }
      .bg-screen  { fill: #0f172a; }
      .hud-label { fill: #cf222e; }
      .hud-val   { fill: #ffffff; }
      .hud-hi    { fill: #d4a72c; }
    }
    /* ]]> */
  </style>""")

    # Cabinet Shell & Screen Frame
    svg_parts.append(f'  <rect class="bg-cabinet" x="1" y="1" width="{width-2}" height="{height-2}" rx="10"/>')
    svg_parts.append(f'  <rect class="bg-screen" x="14" y="14" width="{width-28}" height="{height-28}" rx="6"/>')

    # Starfield Background
    stars = [
        (45, 30), (120, 50), (280, 28), (420, 60), (580, 35), (730, 48), (810, 32),
        (90, 180), (220, 200), (350, 190), (520, 210), (640, 185), (790, 205),
        (160, 110), (310, 140), (480, 95), (670, 130), (760, 160)
    ]
    for sx, sy in stars:
        svg_parts.append(f'  <circle class="star-dot" cx="{sx}" cy="{sy}" r="1"/>')

    # Top Retro Arcade HUD
    svg_parts.append('  <g class="arcade-font">')
    # 1UP / SCORE
    svg_parts.append('    <text x="30" y="38" class="hud-label">1UP</text>')
    svg_parts.append(f'    <text x="30" y="55" class="hud-val">{score:06d}</text>')
    # HIGH SCORE
    svg_parts.append('    <text x="210" y="38" class="hud-label">HIGH SCORE</text>')
    svg_parts.append(f'    <text x="210" y="55" class="hud-hi">{hi_score:06d}</text>')
    # TITLE / MISSION
    svg_parts.append(f'    <text x="{width // 2}" y="42" text-anchor="middle" class="hud-title">SPACE INVADERS // COMMIT DEFENSE</text>')
    # STAGE / WEEKS
    svg_parts.append(f'    <text x="{width - 240}" y="38" class="hud-label">STAGE</text>')
    svg_parts.append(f'    <text x="{width - 240}" y="55" class="hud-val">{num_weeks:02d} WEEKS</text>')
    # LIVES / DEFENDERS
    svg_parts.append(f'    <text x="{width - 110}" y="38" class="hud-label">SHIPS</text>')
    svg_parts.append(f'    <g transform="translate({width - 110}, 43) scale(0.65)">')
    svg_parts.append('      <use href="#player-ship" x="0" y="0"/>')
    svg_parts.append('      <use href="#player-ship" x="28" y="0"/>')
    svg_parts.append('      <use href="#player-ship" x="56" y="0"/>')
    svg_parts.append('    </g>')
    svg_parts.append('  </g>')

    # Grid Separator Guide Line
    svg_parts.append(f'  <line x1="30" y1="64" x2="{width - 30}" y2="64" stroke="#30363d" stroke-width="1"/>')

    # Space Invaders Contribution Grid (53 Weeks x 7 Days)
    svg_parts.append('  <g id="alien-fleet" style="animation: alien-march 2s ease-in-out infinite alternate">')

    day_labels = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
    for r in range(7):
        ry = grid_y0 + r * step_y
        svg_parts.append(f'    <text x="{grid_x0 - 10}" y="{ry + 8}" font-size="8" text-anchor="end" fill="#484f58" class="arcade-font">{day_labels[r]}</text>')

    for col_idx in range(num_weeks):
        col_days = weeks.get(col_idx, [])
        cx = grid_x0 + col_idx * step_x

        for d in col_days:
            r = d["row"]
            cy = grid_y0 + r * step_y
            lvl = d["level"]
            cnt = d["count"]

            if lvl == 0:
                # Dim empty station dot / star
                svg_parts.append(f'    <rect class="cell-0" x="{cx:.1f}" y="{cy:.1f}" width="{cell_size}" height="{cell_size}" rx="2"/>')
            else:
                # Real Space Invaders Alien Sprite
                fill_cls = f"alien-{lvl}"
                # Alternate alien sprite types by row for authentic arcade look
                if r in (0, 1):
                    sprite = "#alien-squid"
                elif r in (2, 3, 4):
                    sprite = "#alien-crab"
                else:
                    sprite = "#alien-octo"

                # Scale sprite (8x8) to fit 10x10 cell with centering
                svg_parts.append(f'    <g transform="translate({cx + 1:.1f}, {cy + 1:.1f}) scale(1.05)" class="{fill_cls}">')
                svg_parts.append(f'      <use href="{sprite}"/>')
                svg_parts.append('    </g>')

    svg_parts.append('  </g>')

    # Ground Defense Baseline Laser Track
    track_y = grid_y0 + 7 * step_y + 16
    svg_parts.append(f'  <line x1="30" y1="{track_y + 18}" x2="{width - 30}" y2="{track_y + 18}" stroke="#238636" stroke-width="1.5" stroke-dasharray="4 4"/>')

    # Animated Player Cannon (Galaga / Space Invaders Defender Ship)
    # Ship patrols along the track beneath columns with active commits
    svg_parts.append(f'  <g id="cannon-patrol" style="animation: ship-patrol 10s ease-in-out infinite">')
    svg_parts.append(f'    <g transform="translate(0, {track_y:.1f})">')
    svg_parts.append('      <use href="#player-ship"/>')
    svg_parts.append('    </g>')
    svg_parts.append('  </g>')

    # Dynamic Dual Laser Blasts firing up at target blocks
    # Laser 1: Fires at recent week target (e.g. week 51, row 6)
    svg_parts.append('  <g style="animation: laser-shot-1 4.5s ease-out infinite">')
    svg_parts.append('    <line x1="0" y1="0" x2="0" y2="16" stroke="#58a6ff" stroke-width="2.5" stroke-linecap="round" filter="url(#laser-glow)"/>')
    svg_parts.append('    <line x1="8" y1="0" x2="8" y2="16" stroke="#39d353" stroke-width="2.5" stroke-linecap="round" filter="url(#laser-glow)"/>')
    svg_parts.append('  </g>')

    # Laser 2: Fires at mid-year target
    svg_parts.append('  <g style="animation: laser-shot-2 4.5s ease-out infinite">')
    svg_parts.append('    <line x1="0" y1="0" x2="0" y2="16" stroke="#ff7b72" stroke-width="2.5" stroke-linecap="round" filter="url(#laser-glow)"/>')
    svg_parts.append('    <line x1="8" y1="0" x2="8" y2="16" stroke="#f2cc60" stroke-width="2.5" stroke-linecap="round" filter="url(#laser-glow)"/>')
    svg_parts.append('  </g>')

    # Particle Hit Burst at Target 1 (week 51 peak day)
    target1_x = grid_x0 + 51 * step_x + 5
    target1_y = grid_y0 + 6 * step_y + 5
    svg_parts.append(f'  <g transform="translate({target1_x:.1f}, {target1_y:.1f})">')
    svg_parts.append('    <!-- Explosion Starburst -->')
    svg_parts.append('    <g style="animation: burst-pulse 4.5s ease-out infinite">')
    svg_parts.append('      <circle r="4" fill="#39d353" filter="url(#laser-glow)"/>')
    svg_parts.append('      <line x1="-8" y1="-8" x2="8" y2="8" stroke="#f2cc60" stroke-width="1.5"/>')
    svg_parts.append('      <line x1="-8" y1="8" x2="8" y2="-8" stroke="#f2cc60" stroke-width="1.5"/>')
    svg_parts.append('      <line x1="0" y1="-10" x2="0" y2="10" stroke="#ff7b72" stroke-width="1.5"/>')
    svg_parts.append('    </g>')
    svg_parts.append('    <!-- Floating Arcade Score Popup -->')
    svg_parts.append('    <g style="animation: score-pop 4.5s ease-out infinite">')
    svg_parts.append(f'      <text x="0" y="-8" text-anchor="middle" font-size="10" font-weight="700" fill="#f2cc60" class="arcade-font">+{max_day * 100}</text>')
    svg_parts.append('    </g>')
    svg_parts.append('  </g>')

    # Bottom Status Bar & Credits
    svg_parts.append(f'  <g class="arcade-font" transform="translate(30, {height - 18})">')
    svg_parts.append('    <text x="0" y="0" font-size="9" fill="#8b949e">PLAYER: <tspan fill="#58a6ff">NITIN PATIDAR</tspan></text>')
    svg_parts.append(f'    <text x="{width // 2}" y="0" text-anchor="middle" font-size="9" fill="#8b949e">TOTAL ALIEN COMMITS PURGED: <tspan fill="#39d353">{total_contribs}</tspan></text>')
    svg_parts.append(f'    <text x="{width - 60}" y="0" text-anchor="end" font-size="9" fill="#f2cc60">CREDIT 01</text>')
    svg_parts.append('  </g>')

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


def main():
    parser = argparse.ArgumentParser(description="Generate Space Invaders Contribution Defense SVG.")
    parser.add_argument("--user", default="Programmer-NITIN", help="GitHub username")
    parser.add_argument("--config", default="assets/invaders.json", help="Path to config JSON")
    parser.add_argument("-o", "--out", default="assets/invaders.svg", help="Output SVG path")

    args = parser.parse_args()

    cfg = {}
    config_path = Path(args.config)
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception as e:
            print(f"Warning: could not read {config_path}: {e}")

    username = args.user or cfg.get("username", "Programmer-NITIN")

    print(f"Fetching GitHub contributions for @{username}...")
    days, total_contribs = fetch_contributions_html(username)
    print(f"Loaded {len(days)} days ({total_contribs} contributions)")

    svg_content = generate_invaders_svg(days=days, total_contribs=total_contribs, username=username)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print(f"Successfully generated {out_path} ({len(svg_content) // 1024} KB)")


if __name__ == "__main__":
    main()
