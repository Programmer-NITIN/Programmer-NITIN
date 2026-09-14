#!/usr/bin/env python3
"""
invaders.py - Generates an authentic, animated Retro Space Invaders / Arcade Galaga
Contribution Defense SVG powered by real live GitHub contribution data.

Uses SMIL animations (<animate>, <animateTransform>) instead of CSS @keyframes
so animations work correctly when embedded via <img> tags (GitHub README, preview.html).

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
    """Renders the animated Retro Space Invaders Contribution Defense SVG.

    All animations use SMIL (<animate>, <animateTransform>) so they work
    correctly when the SVG is embedded via <img> tags.
    """
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

    # Animation timing constants (seconds)
    cycle = 10.0       # Full ship patrol cycle
    laser1_start = 1.5  # Laser 1 fires at this time in the cycle
    laser1_dur = 1.2    # Laser 1 travel duration
    laser2_start = 4.5  # Laser 2 fires
    laser2_dur = 1.2
    burst_delay = 0.15  # Explosion appears slightly after laser hits
    burst_dur = 0.5
    score_dur = 0.7

    # Ship patrol X positions (matching keyframe stops)
    ship_y = grid_y0 + 7 * step_y + 16
    ship_positions = [120, 380, 690, 720, 450, 120]
    ship_times = [0, 0.20, 0.45, 0.55, 0.75, 1.0]  # normalized

    # Laser target positions
    # Laser 1 fires from ship position ~690px to week 51 area
    laser1_ship_x = 690
    target1_col = min(51, num_weeks - 1)
    target1_row = 6
    target1_x = grid_x0 + target1_col * step_x + 5
    target1_y = grid_y0 + target1_row * step_y + 5

    # Laser 2 fires from ship position ~450px to mid-year area
    laser2_ship_x = 450
    target2_col = min(26, num_weeks - 1)
    target2_row = 3
    target2_x = grid_x0 + target2_col * step_x + 5
    target2_y = grid_y0 + target2_row * step_y + 5

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

    # Stylesheet - static styles only, no @keyframes
    svg_parts.append("""  <style>
    /* <![CDATA[ */
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
    .star-dot { fill: #ffffff; }

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

    # Starfield Background with twinkling SMIL animation
    stars = [
        (45, 30), (120, 50), (280, 28), (420, 60), (580, 35), (730, 48), (810, 32),
        (90, 180), (220, 200), (350, 190), (520, 210), (640, 185), (790, 205),
        (160, 110), (310, 140), (480, 95), (670, 130), (760, 160)
    ]
    for i, (sx, sy) in enumerate(stars):
        base_opacity = 0.15 + (i % 5) * 0.06
        svg_parts.append(f'  <circle class="star-dot" cx="{sx}" cy="{sy}" r="1" opacity="{base_opacity:.2f}">')
        svg_parts.append(f'    <animate attributeName="opacity" values="{base_opacity:.2f};0.55;{base_opacity:.2f}" dur="{1.5 + (i % 7) * 0.4:.1f}s" repeatCount="indefinite"/>')
        svg_parts.append('  </circle>')

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
    # Alien fleet with SMIL horizontal march
    svg_parts.append('  <g id="alien-fleet">')
    svg_parts.append('    <animateTransform attributeName="transform" type="translate" values="0,0;3,0;0,0;-3,0;0,0" dur="3s" repeatCount="indefinite"/>')

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

    # ─── Animated Player Cannon Ship (SMIL patrol) ───
    # Build keyTimes and values for smooth patrol
    ship_key_times = ";".join(f"{t:.2f}" for t in ship_times)
    ship_x_values = ";".join(str(x) for x in ship_positions)

    svg_parts.append(f'  <g id="cannon-patrol">')
    svg_parts.append(f'    <animateTransform attributeName="transform" type="translate"')
    svg_parts.append(f'      values="{ship_positions[0]} {ship_y};{ship_positions[1]} {ship_y};{ship_positions[2]} {ship_y};{ship_positions[3]} {ship_y};{ship_positions[4]} {ship_y};{ship_positions[5]} {ship_y}"')
    svg_parts.append(f'      keyTimes="{ship_key_times}"')
    svg_parts.append(f'      dur="{cycle}s" repeatCount="indefinite" calcMode="spline"')
    svg_parts.append(f'      keySplines="0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1"/>')
    svg_parts.append('    <use href="#player-ship"/>')
    svg_parts.append('  </g>')

    # ─── LASER SHOT 1 ───
    # Twin laser beams fire from ship at position ~690 up to target1
    laser1_x = laser1_ship_x + 8  # center on ship cannon
    svg_parts.append(f'  <g id="laser-1" opacity="0">')
    # Visibility: appear at laser1_start, disappear after travel
    svg_parts.append(f'    <animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{laser1_start/cycle:.3f};{(laser1_start+0.05)/cycle:.3f};{(laser1_start+laser1_dur)/cycle:.3f};{(laser1_start+laser1_dur+0.05)/cycle:.3f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    # Vertical movement: descend from ship_y up to target1_y
    svg_parts.append(f'    <animateTransform attributeName="transform" type="translate"')
    svg_parts.append(f'      values="{laser1_x} {ship_y};{laser1_x} {ship_y};{laser1_x} {ship_y};{laser1_x} {target1_y};{laser1_x} {target1_y};{laser1_x} {ship_y}"')
    svg_parts.append(f'      keyTimes="0;{laser1_start/cycle:.3f};{(laser1_start+0.05)/cycle:.3f};{(laser1_start+laser1_dur)/cycle:.3f};{(laser1_start+laser1_dur+0.05)/cycle:.3f};1"')
    svg_parts.append(f'      dur="{cycle}s" repeatCount="indefinite"/>')
    # Laser beam lines (drawn at origin, positioned by animateTransform)
    svg_parts.append('    <line x1="0" y1="0" x2="0" y2="16" stroke="#58a6ff" stroke-width="2.5" stroke-linecap="round" filter="url(#laser-glow)"/>')
    svg_parts.append('    <line x1="8" y1="0" x2="8" y2="16" stroke="#39d353" stroke-width="2.5" stroke-linecap="round" filter="url(#laser-glow)"/>')
    svg_parts.append('  </g>')

    # ─── LASER SHOT 2 ───
    laser2_x = laser2_ship_x + 8
    svg_parts.append(f'  <g id="laser-2" opacity="0">')
    svg_parts.append(f'    <animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{laser2_start/cycle:.3f};{(laser2_start+0.05)/cycle:.3f};{(laser2_start+laser2_dur)/cycle:.3f};{(laser2_start+laser2_dur+0.05)/cycle:.3f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append(f'    <animateTransform attributeName="transform" type="translate"')
    svg_parts.append(f'      values="{laser2_x} {ship_y};{laser2_x} {ship_y};{laser2_x} {ship_y};{laser2_x} {target2_y};{laser2_x} {target2_y};{laser2_x} {ship_y}"')
    svg_parts.append(f'      keyTimes="0;{laser2_start/cycle:.3f};{(laser2_start+0.05)/cycle:.3f};{(laser2_start+laser2_dur)/cycle:.3f};{(laser2_start+laser2_dur+0.05)/cycle:.3f};1"')
    svg_parts.append(f'      dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append('    <line x1="0" y1="0" x2="0" y2="16" stroke="#ff7b72" stroke-width="2.5" stroke-linecap="round" filter="url(#laser-glow)"/>')
    svg_parts.append('    <line x1="8" y1="0" x2="8" y2="16" stroke="#f2cc60" stroke-width="2.5" stroke-linecap="round" filter="url(#laser-glow)"/>')
    svg_parts.append('  </g>')

    # ─── EXPLOSION BURST at Target 1 ───
    burst1_start = laser1_start + laser1_dur
    svg_parts.append(f'  <g transform="translate({target1_x:.1f}, {target1_y:.1f})" opacity="0">')
    svg_parts.append(f'    <animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;{burst1_start/cycle:.3f};{(burst1_start+0.1)/cycle:.3f};{(burst1_start+burst_dur)/cycle:.3f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    # Starburst explosion
    svg_parts.append('    <g>')
    svg_parts.append(f'      <animateTransform attributeName="transform" type="scale" values="0.5;1.8;2.2;0.5" keyTimes="0;0.3;0.7;1" dur="{burst_dur}s" begin="{burst1_start}s" repeatCount="indefinite" additive="sum"/>')
    svg_parts.append('      <circle r="4" fill="#39d353" filter="url(#laser-glow)"/>')
    svg_parts.append('      <line x1="-8" y1="-8" x2="8" y2="8" stroke="#f2cc60" stroke-width="1.5"/>')
    svg_parts.append('      <line x1="-8" y1="8" x2="8" y2="-8" stroke="#f2cc60" stroke-width="1.5"/>')
    svg_parts.append('      <line x1="0" y1="-10" x2="0" y2="10" stroke="#ff7b72" stroke-width="1.5"/>')
    svg_parts.append('      <line x1="-10" y1="0" x2="10" y2="0" stroke="#58a6ff" stroke-width="1.5"/>')
    svg_parts.append('    </g>')
    svg_parts.append('  </g>')

    # ─── FLOATING SCORE POPUP at Target 1 ───
    score_start = burst1_start + 0.1
    svg_parts.append(f'  <text x="{target1_x:.1f}" y="{target1_y - 8:.1f}" text-anchor="middle" font-size="10" font-weight="700" fill="#f2cc60" class="arcade-font" opacity="0">')
    svg_parts.append(f'    <animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;{score_start/cycle:.3f};{(score_start+0.15)/cycle:.3f};{(score_start+score_dur)/cycle:.3f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append(f'    <animateTransform attributeName="transform" type="translate" values="0 0;0 0;0 -4;0 -20;0 0" keyTimes="0;{score_start/cycle:.3f};{(score_start+0.15)/cycle:.3f};{(score_start+score_dur)/cycle:.3f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append(f'    +{max_day * 100}')
    svg_parts.append('  </text>')

    # ─── EXPLOSION BURST at Target 2 ───
    burst2_start = laser2_start + laser2_dur
    svg_parts.append(f'  <g transform="translate({target2_x:.1f}, {target2_y:.1f})" opacity="0">')
    svg_parts.append(f'    <animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;{burst2_start/cycle:.3f};{(burst2_start+0.1)/cycle:.3f};{(burst2_start+burst_dur)/cycle:.3f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append('    <g>')
    svg_parts.append(f'      <animateTransform attributeName="transform" type="scale" values="0.5;1.8;2.2;0.5" keyTimes="0;0.3;0.7;1" dur="{burst_dur}s" begin="{burst2_start}s" repeatCount="indefinite" additive="sum"/>')
    svg_parts.append('      <circle r="4" fill="#ff7b72" filter="url(#laser-glow)"/>')
    svg_parts.append('      <line x1="-8" y1="-8" x2="8" y2="8" stroke="#f2cc60" stroke-width="1.5"/>')
    svg_parts.append('      <line x1="-8" y1="8" x2="8" y2="-8" stroke="#f2cc60" stroke-width="1.5"/>')
    svg_parts.append('      <line x1="0" y1="-10" x2="0" y2="10" stroke="#39d353" stroke-width="1.5"/>')
    svg_parts.append('      <line x1="-10" y1="0" x2="10" y2="0" stroke="#58a6ff" stroke-width="1.5"/>')
    svg_parts.append('    </g>')
    svg_parts.append('  </g>')

    # ─── FLOATING SCORE POPUP at Target 2 ───
    score2_start = burst2_start + 0.1
    active_days = [d for d in days if d["count"] > 0]
    mid_score = active_days[len(active_days) // 2]["count"] * 100 if active_days else 500
    svg_parts.append(f'  <text x="{target2_x:.1f}" y="{target2_y - 8:.1f}" text-anchor="middle" font-size="10" font-weight="700" fill="#f2cc60" class="arcade-font" opacity="0">')
    svg_parts.append(f'    <animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;{score2_start/cycle:.3f};{(score2_start+0.15)/cycle:.3f};{(score2_start+score_dur)/cycle:.3f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append(f'    <animateTransform attributeName="transform" type="translate" values="0 0;0 0;0 -4;0 -20;0 0" keyTimes="0;{score2_start/cycle:.3f};{(score2_start+0.15)/cycle:.3f};{(score2_start+score_dur)/cycle:.3f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append(f'    +{mid_score}')
    svg_parts.append('  </text>')

    # ─── Thruster Glow on Player Ship ───
    # Pulsing engine glow at the bottom of the ship
    svg_parts.append(f'  <g id="thruster-glow">')
    svg_parts.append(f'    <animateTransform attributeName="transform" type="translate"')
    svg_parts.append(f'      values="{ship_positions[0]} {ship_y};{ship_positions[1]} {ship_y};{ship_positions[2]} {ship_y};{ship_positions[3]} {ship_y};{ship_positions[4]} {ship_y};{ship_positions[5]} {ship_y}"')
    svg_parts.append(f'      keyTimes="{ship_key_times}"')
    svg_parts.append(f'      dur="{cycle}s" repeatCount="indefinite" calcMode="spline"')
    svg_parts.append(f'      keySplines="0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1"/>')
    svg_parts.append('    <ellipse cx="12" cy="18" rx="6" ry="2" fill="#ff7b72" opacity="0.6">')
    svg_parts.append('      <animate attributeName="ry" values="2;4;2" dur="0.5s" repeatCount="indefinite"/>')
    svg_parts.append('      <animate attributeName="opacity" values="0.6;0.9;0.6" dur="0.5s" repeatCount="indefinite"/>')
    svg_parts.append('    </ellipse>')
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
