#!/usr/bin/env python3
"""
invaders.py - Generates an authentic, animated Retro Space Invaders / Arcade Galaga
Contribution Defense SVG powered by real live GitHub contribution data.

Authentic Features:
- True arcade battlefield distance: player cannon is stationed at the bottom ground line
  with plenty of airspace and 4 classic green defense bunkers between the ship and aliens.
- Real arcade laser missiles: crisp, blazing, high-speed vertical player bullets firing straight
  from the cannon barrel with muzzle flash and traveling at high velocity directly into targets.
- Authentic Space Invaders 8x8 pixel explosions upon impact + floating arcade score popups.
- Dynamic reactive aliens: hit aliens actually disintegrate and vanish upon impact!
- Alien squiggly bomb drops that strike defense bunkers with sparks.
- 100% SMIL animations (<animate>, <animateTransform>) so everything plays reliably inside
  <img> tags in GitHub README and preview.html.
- Responsive, dark/light mode adaptive, zero dependencies.
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
    """Renders the authentic Space Invaders Contribution Defense SVG with distance and real bullets."""
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
    grid_y0 = 70

    # Layout dimensions: plenty of vertical space giving the ship authentic arcade distance!
    width = 860
    height = 310

    # Positions
    bunker_y = 194
    ship_y = 244  # 83px of battlefield distance from bottom alien row!
    track_y = 265

    # 3 Real Targets in Nitin's history (col 12, col 29, col 51)
    # Target 1: Early-year commit
    t1_col, t1_row, t1_score = 12, 1, 200
    t1_cx = grid_x0 + t1_col * step_x + 5
    t1_cy = grid_y0 + t1_row * step_y + 5
    ship_x1 = t1_cx - 11  # Cannon tip (x+11) aligns exactly at t1_cx

    # Target 2: Mid-year commit
    t2_col, t2_row, t2_score = 29, 2, 300
    t2_cx = grid_x0 + t2_col * step_x + 5
    t2_cy = grid_y0 + t2_row * step_y + 5
    ship_x2 = t2_cx - 11

    # Target 3: Peak week commit (Nitin's 36-commit max day!)
    t3_col, t3_row, t3_score = 51, 6, max_day * 100
    t3_cx = grid_x0 + t3_col * step_x + 5
    t3_cy = grid_y0 + t3_row * step_y + 5
    ship_x3 = t3_cx - 11

    # Animation timing (9.0s cycle)
    cycle = 9.0

    # Ship patrol keyframe timings (8 keyframes)
    ship_times = [0.0, 0.1444, 0.3111, 0.4222, 0.5778, 0.7000, 0.9778, 1.0]
    ship_xs = [ship_x1, ship_x1, ship_x2, ship_x2, ship_x3, ship_x3, ship_x1, ship_x1]
    ship_key_times_str = ";".join(f"{t:.4f}" for t in ship_times)
    ship_values_str = ";".join(f"{x:.1f} {ship_y}" for x in ship_xs)

    # Bullet timings
    # Shot 1: fires at 0.5s, reaches target at 0.85s (0.35s flight!)
    b1_start, b1_hit = 0.5, 0.85
    b1_k0, b1_k1, b1_k2, b1_k3 = 0.0, b1_start / cycle, b1_hit / cycle, (b1_hit + 0.02) / cycle

    # Shot 2: fires at 3.0s, reaches target at 3.33s (0.33s flight!)
    b2_start, b2_hit = 3.0, 3.33
    b2_k0, b2_k1, b2_k2, b2_k3 = 0.0, b2_start / cycle, b2_hit / cycle, (b2_hit + 0.02) / cycle

    # Shot 3: fires at 5.4s, reaches target at 5.65s (0.25s high-velocity strike!)
    b3_start, b3_hit = 5.4, 5.65
    b3_k0, b3_k1, b3_k2, b3_k3 = 0.0, b3_start / cycle, b3_hit / cycle, (b3_hit + 0.02) / cycle

    # Bomb drop timing (alien bomb from col 20 drops onto bunker 2)
    bomb_col = 20
    bomb_x = grid_x0 + bomb_col * step_x + 5
    bomb_y0 = grid_y0 + 6 * step_y + 12
    bomb_y1 = bunker_y
    bomb_start, bomb_hit = 1.8, 2.35
    bomb_k1, bomb_k2 = bomb_start / cycle, bomb_hit / cycle

    svg_parts = []
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">')

    # Defs: filters, gradients, pixel sprites
    svg_parts.append("""  <defs>
    <!-- High-energy Laser Glow Filter -->
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

    <!-- Real Arcade Player Bullet / Laser Missile -->
    <g id="player-bullet">
      <!-- High-voltage outer glow aura -->
      <line x1="0" y1="-14" x2="0" y2="0" stroke="#00ffcc" stroke-width="3.5" stroke-linecap="round" opacity="0.6" filter="url(#laser-glow)"/>
      <!-- Pure white laser core -->
      <line x1="0" y1="-12" x2="0" y2="-1" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round"/>
      <!-- Pointed armor-piercing projectile tip -->
      <polygon points="0,-16 -1.8,-11 1.8,-11" fill="#ffffff"/>
    </g>

    <!-- Alien Torpedo / Squiggly Bomb -->
    <g id="alien-bomb-sprite">
      <rect x="-1" y="0" width="2" height="2" fill="#ff7b72"/>
      <rect x="0" y="2" width="2" height="2" fill="#f2cc60"/>
      <rect x="-1" y="4" width="2" height="2" fill="#ff7b72"/>
      <rect x="0" y="6" width="2" height="2" fill="#f2cc60"/>
      <rect x="-1" y="8" width="2" height="2" fill="#ff7b72"/>
    </g>

    <!-- Classic 1978 Space Invaders 8x8 Alien Explosion Sprite -->
    <g id="alien-explosion-sprite">
      <rect x="0" y="0" width="1" height="1"/><rect x="7" y="0" width="1" height="1"/>
      <rect x="2" y="1" width="1" height="1"/><rect x="5" y="1" width="1" height="1"/>
      <rect x="3" y="2" width="2" height="1"/>
      <rect x="1" y="3" width="6" height="1"/>
      <rect x="0" y="4" width="8" height="1"/>
      <rect x="3" y="5" width="2" height="1"/>
      <rect x="2" y="6" width="1" height="1"/><rect x="5" y="6" width="1" height="1"/>
      <rect x="0" y="7" width="1" height="1"/><rect x="7" y="7" width="1" height="1"/>
    </g>

    <!-- Classic Defensive Green Bunker with Archway & Battle Damage -->
    <g id="defense-bunker">
      <!-- Main bunker body with iconic dome & arch cutout -->
      <path d="M6 0 h24 v4 h6 v4 h4 v14 h-12 v-8 h-16 v8 h-12 v-14 h4 v-4 h6 z" fill="#2ea043"/>
      <!-- Battle scars from previous alien attacks -->
      <rect x="11" y="3" width="3" height="3" fill="#070a0f"/>
      <rect x="25" y="7" width="4" height="2" fill="#070a0f"/>
      <rect x="5" y="13" width="2" height="4" fill="#070a0f"/>
    </g>

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
      <rect x="11" y="0" width="2" height="4" fill="#ffffff"/>
      <rect x="10" y="4" width="4" height="2" fill="#58a6ff"/>
      <!-- Main Armor Hull -->
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
        (90, 180), (220, 180), (350, 190), (520, 185), (640, 185), (790, 205),
        (160, 110), (310, 140), (480, 95), (670, 130), (760, 160), (250, 230), (450, 235), (620, 230)
    ]
    for i, (sx, sy) in enumerate(stars):
        base_opacity = 0.15 + (i % 5) * 0.06
        svg_parts.append(f'  <circle class="star-dot" cx="{sx}" cy="{sy}" r="1" opacity="{base_opacity:.2f}">')
        svg_parts.append(f'    <animate attributeName="opacity" values="{base_opacity:.2f};0.60;{base_opacity:.2f}" dur="{1.5 + (i % 7) * 0.4:.1f}s" repeatCount="indefinite"/>')
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
    svg_parts.append(f'  <line x1="30" y1="62" x2="{width - 30}" y2="62" stroke="#30363d" stroke-width="1"/>')

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
                svg_parts.append(f'    <rect class="cell-0" x="{cx:.1f}" y="{cy:.1f}" width="{cell_size}" height="{cell_size}" rx="2"/>')
            else:
                fill_cls = f"alien-{lvl}"
                if r in (0, 1):
                    sprite = "#alien-squid"
                elif r in (2, 3, 4):
                    sprite = "#alien-crab"
                else:
                    sprite = "#alien-octo"

                # Check if this specific alien is one of the 3 targeted enemies
                is_t1 = (col_idx == t1_col and r == t1_row)
                is_t2 = (col_idx == t2_col and r == t2_row)
                is_t3 = (col_idx == t3_col and r == t3_row)

                if is_t1:
                    # Alien 1 disintegrates when hit by bullet 1
                    svg_parts.append(f'    <g transform="translate({cx + 1:.1f}, {cy + 1:.1f}) scale(1.05)" class="{fill_cls}">')
                    svg_parts.append(f'      <animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;{b1_k2:.4f};{b1_k3:.4f};0.9500;1" dur="{cycle}s" repeatCount="indefinite"/>')
                    svg_parts.append(f'      <use href="{sprite}"/>')
                    svg_parts.append('    </g>')
                elif is_t2:
                    # Alien 2 disintegrates when hit by bullet 2
                    svg_parts.append(f'    <g transform="translate({cx + 1:.1f}, {cy + 1:.1f}) scale(1.05)" class="{fill_cls}">')
                    svg_parts.append(f'      <animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;{b2_k2:.4f};{b2_k3:.4f};0.9500;1" dur="{cycle}s" repeatCount="indefinite"/>')
                    svg_parts.append(f'      <use href="{sprite}"/>')
                    svg_parts.append('    </g>')
                elif is_t3:
                    # Alien 3 disintegrates when hit by bullet 3 (Big Peak Day!)
                    svg_parts.append(f'    <g transform="translate({cx + 1:.1f}, {cy + 1:.1f}) scale(1.05)" class="{fill_cls}">')
                    svg_parts.append(f'      <animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;{b3_k2:.4f};{b3_k3:.4f};0.9500;1" dur="{cycle}s" repeatCount="indefinite"/>')
                    svg_parts.append(f'      <use href="{sprite}"/>')
                    svg_parts.append('    </g>')
                else:
                    svg_parts.append(f'    <g transform="translate({cx + 1:.1f}, {cy + 1:.1f}) scale(1.05)" class="{fill_cls}">')
                    svg_parts.append(f'      <use href="{sprite}"/>')
                    svg_parts.append('    </g>')

    svg_parts.append('  </g>')

    # ─── 4 CLASSIC GREEN DEFENSIVE BUNKERS (Iconic Space Invaders Archetype) ───
    # Positioned at authentic distance in the open battlefield between the alien fleet and ship
    bunker_xs = [130, 330, 550, 670]
    svg_parts.append('  <!-- 4 Classic Defense Bunkers -->')
    for bx in bunker_xs:
        svg_parts.append(f'  <use href="#defense-bunker" x="{bx}" y="{bunker_y}"/>')

    # ─── ALIEN BOMB DROP (Col 20 alien drops squiggly bomb on Bunker 2) ───
    svg_parts.append(f'  <g id="alien-bomb" opacity="0">')
    svg_parts.append(f'    <animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{bomb_k1:.4f};{(bomb_k1+0.01):.4f};{bomb_k2:.4f};{(bomb_k2+0.01):.4f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append(f'    <animateTransform attributeName="transform" type="translate"')
    svg_parts.append(f'      values="{bomb_x} {bomb_y0};{bomb_x} {bomb_y0};{bomb_x} {bomb_y0};{bomb_x} {bomb_y1};{bomb_x} {bomb_y1};{bomb_x} {bomb_y0}"')
    svg_parts.append(f'      keyTimes="0;{bomb_k1:.4f};{(bomb_k1+0.01):.4f};{bomb_k2:.4f};{(bomb_k2+0.01):.4f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append('    <use href="#alien-bomb-sprite"/>')
    svg_parts.append('  </g>')
    # Bunker spark from alien bomb impact
    svg_parts.append(f'  <circle cx="{bomb_x}" cy="{bomb_y1}" r="3" fill="#ff7b72" opacity="0">')
    svg_parts.append(f'    <animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;{bomb_k2:.4f};{(bomb_k2+0.01):.4f};{(bomb_k2+0.04):.4f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append('  </circle>')

    # Ground Defense Baseline Laser Track
    svg_parts.append(f'  <line x1="30" y1="{track_y}" x2="{width - 30}" y2="{track_y}" stroke="#238636" stroke-width="1.5" stroke-dasharray="4 4"/>')

    # ─── ANIMATED PLAYER CANNON SHIP (SMIL patrol with authentic pause & aim) ───
    spline_7 = "0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1"
    svg_parts.append(f'  <g id="cannon-patrol">')
    svg_parts.append(f'    <animateTransform attributeName="transform" type="translate"')
    svg_parts.append(f'      values="{ship_values_str}"')
    svg_parts.append(f'      keyTimes="{ship_key_times_str}"')
    svg_parts.append(f'      dur="{cycle}s" repeatCount="indefinite" calcMode="spline"')
    svg_parts.append(f'      keySplines="{spline_7}"/>')
    svg_parts.append('    <use href="#player-ship"/>')
    # Cannon muzzle flash right at cannon barrel tip
    svg_parts.append('    <circle cx="12" cy="0" r="3.5" fill="#ffffff" filter="url(#laser-glow)" opacity="0">')
    # Flashes when each bullet is fired
    mf1_s, mf2_s, mf3_s = b1_start / cycle, b2_start / cycle, b3_start / cycle
    svg_parts.append(f'      <animate attributeName="opacity" values="0;0;1;0;0;1;0;0;1;0;0" keyTimes="0;{mf1_s:.4f};{(mf1_s+0.01):.4f};{(mf1_s+0.02):.4f};{mf2_s:.4f};{(mf2_s+0.01):.4f};{(mf2_s+0.02):.4f};{mf3_s:.4f};{(mf3_s+0.01):.4f};{(mf3_s+0.02):.4f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append('    </circle>')
    svg_parts.append('  </g>')

    # ─── REAL BULLET 1: Fires vertically from cannon tip to Target 1 ───
    svg_parts.append('  <!-- Real Arcade Bullet 1 -->')
    svg_parts.append(f'  <g id="bullet-1" opacity="0">')
    svg_parts.append(f'    <animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{b1_k1:.4f};{(b1_k1+0.005):.4f};{b1_k2:.4f};{b1_k3:.4f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append(f'    <animateTransform attributeName="transform" type="translate"')
    svg_parts.append(f'      values="{t1_cx:.1f} {ship_y};{t1_cx:.1f} {ship_y};{t1_cx:.1f} {ship_y};{t1_cx:.1f} {t1_cy:.1f};{t1_cx:.1f} {t1_cy:.1f};{t1_cx:.1f} {ship_y}"')
    svg_parts.append(f'      keyTimes="0;{b1_k1:.4f};{(b1_k1+0.005):.4f};{b1_k2:.4f};{b1_k3:.4f};1"')
    svg_parts.append(f'      dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append('    <use href="#player-bullet"/>')
    svg_parts.append('  </g>')

    # Impact Explosion 1 (Space Invaders 8x8 Pixel Blast)
    exp1_k1 = b1_k2
    exp1_k2 = (b1_hit + 0.03) / cycle
    exp1_k3 = (b1_hit + 0.40) / cycle
    svg_parts.append(f'  <g transform="translate({t1_cx:.1f}, {t1_cy:.1f})" opacity="0">')
    svg_parts.append(f'    <animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;{exp1_k1:.4f};{exp1_k2:.4f};{exp1_k3:.4f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append('    <g transform="translate(-7, -7) scale(1.8)" fill="#ff7b72" filter="url(#alien-glow)">')
    svg_parts.append('      <use href="#alien-explosion-sprite"/>')
    svg_parts.append('    </g>')
    svg_parts.append('  </g>')

    # Floating Arcade Score 1
    sc1_k1 = exp1_k1
    sc1_k2 = (b1_hit + 0.05) / cycle
    sc1_k3 = (b1_hit + 0.60) / cycle
    svg_parts.append(f'  <text x="{t1_cx:.1f}" y="{t1_cy - 8:.1f}" text-anchor="middle" font-size="10" font-weight="700" fill="#f2cc60" class="arcade-font" opacity="0">')
    svg_parts.append(f'    <animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;{sc1_k1:.4f};{sc1_k2:.4f};{sc1_k3:.4f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append(f'    <animateTransform attributeName="transform" type="translate" values="0 0;0 0;0 -4;0 -18;0 0" keyTimes="0;{sc1_k1:.4f};{sc1_k2:.4f};{sc1_k3:.4f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append(f'    +{t1_score}')
    svg_parts.append('  </text>')

    # ─── REAL BULLET 2: Fires vertically from cannon tip to Target 2 ───
    svg_parts.append('  <!-- Real Arcade Bullet 2 -->')
    svg_parts.append(f'  <g id="bullet-2" opacity="0">')
    svg_parts.append(f'    <animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{b2_k1:.4f};{(b2_k1+0.005):.4f};{b2_k2:.4f};{b2_k3:.4f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append(f'    <animateTransform attributeName="transform" type="translate"')
    svg_parts.append(f'      values="{t2_cx:.1f} {ship_y};{t2_cx:.1f} {ship_y};{t2_cx:.1f} {ship_y};{t2_cx:.1f} {t2_cy:.1f};{t2_cx:.1f} {t2_cy:.1f};{t2_cx:.1f} {ship_y}"')
    svg_parts.append(f'      keyTimes="0;{b2_k1:.4f};{(b2_k1+0.005):.4f};{b2_k2:.4f};{b2_k3:.4f};1"')
    svg_parts.append(f'      dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append('    <use href="#player-bullet"/>')
    svg_parts.append('  </g>')

    # Impact Explosion 2
    exp2_k1 = b2_k2
    exp2_k2 = (b2_hit + 0.03) / cycle
    exp2_k3 = (b2_hit + 0.40) / cycle
    svg_parts.append(f'  <g transform="translate({t2_cx:.1f}, {t2_cy:.1f})" opacity="0">')
    svg_parts.append(f'    <animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;{exp2_k1:.4f};{exp2_k2:.4f};{exp2_k3:.4f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append('    <g transform="translate(-7, -7) scale(1.8)" fill="#f2cc60" filter="url(#alien-glow)">')
    svg_parts.append('      <use href="#alien-explosion-sprite"/>')
    svg_parts.append('    </g>')
    svg_parts.append('  </g>')

    # Floating Arcade Score 2
    sc2_k1 = exp2_k1
    sc2_k2 = (b2_hit + 0.05) / cycle
    sc2_k3 = (b2_hit + 0.60) / cycle
    svg_parts.append(f'  <text x="{t2_cx:.1f}" y="{t2_cy - 8:.1f}" text-anchor="middle" font-size="10" font-weight="700" fill="#f2cc60" class="arcade-font" opacity="0">')
    svg_parts.append(f'    <animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;{sc2_k1:.4f};{sc2_k2:.4f};{sc2_k3:.4f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append(f'    <animateTransform attributeName="transform" type="translate" values="0 0;0 0;0 -4;0 -18;0 0" keyTimes="0;{sc2_k1:.4f};{sc2_k2:.4f};{sc2_k3:.4f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append(f'    +{t2_score}')
    svg_parts.append('  </text>')

    # ─── REAL BULLET 3: Fires vertically from cannon tip to Target 3 (Peak Day Strike!) ───
    svg_parts.append('  <!-- Real Arcade Bullet 3 (Peak Day Strike) -->')
    svg_parts.append(f'  <g id="bullet-3" opacity="0">')
    svg_parts.append(f'    <animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{b3_k1:.4f};{(b3_k1+0.005):.4f};{b3_k2:.4f};{b3_k3:.4f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append(f'    <animateTransform attributeName="transform" type="translate"')
    svg_parts.append(f'      values="{t3_cx:.1f} {ship_y};{t3_cx:.1f} {ship_y};{t3_cx:.1f} {ship_y};{t3_cx:.1f} {t3_cy:.1f};{t3_cx:.1f} {t3_cy:.1f};{t3_cx:.1f} {ship_y}"')
    svg_parts.append(f'      keyTimes="0;{b3_k1:.4f};{(b3_k1+0.005):.4f};{b3_k2:.4f};{b3_k3:.4f};1"')
    svg_parts.append(f'      dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append('    <use href="#player-bullet"/>')
    svg_parts.append('  </g>')

    # Impact Explosion 3 (Big Golden Starburst Explosion!)
    exp3_k1 = b3_k2
    exp3_k2 = (b3_hit + 0.03) / cycle
    exp3_k3 = (b3_hit + 0.50) / cycle
    svg_parts.append(f'  <g transform="translate({t3_cx:.1f}, {t3_cy:.1f})" opacity="0">')
    svg_parts.append(f'    <animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;{exp3_k1:.4f};{exp3_k2:.4f};{exp3_k3:.4f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append('    <g transform="translate(-10, -10) scale(2.5)" fill="#f2cc60" filter="url(#alien-glow)">')
    svg_parts.append('      <use href="#alien-explosion-sprite"/>')
    svg_parts.append('    </g>')
    # Additional outer particle burst rays
    svg_parts.append('    <g>')
    svg_parts.append(f'      <animateTransform attributeName="transform" type="scale" values="0.2;1.6;2.2;0.2" keyTimes="0;0.2;0.6;1" dur="0.5s" begin="{b3_hit}s" repeatCount="indefinite" additive="sum"/>')
    svg_parts.append('      <line x1="-12" y1="-12" x2="12" y2="12" stroke="#39d353" stroke-width="1.5"/>')
    svg_parts.append('      <line x1="-12" y1="12" x2="12" y2="-12" stroke="#ff7b72" stroke-width="1.5"/>')
    svg_parts.append('      <line x1="0" y1="-14" x2="0" y2="14" stroke="#ffffff" stroke-width="2"/>')
    svg_parts.append('    </g>')
    svg_parts.append('  </g>')

    # Floating Arcade Score 3 (+3600 Golden High Score)
    sc3_k1 = exp3_k1
    sc3_k2 = (b3_hit + 0.05) / cycle
    sc3_k3 = (b3_hit + 0.70) / cycle
    svg_parts.append(f'  <text x="{t3_cx:.1f}" y="{t3_cy - 10:.1f}" text-anchor="middle" font-size="12" font-weight="700" fill="#f2cc60" class="arcade-font" opacity="0">')
    svg_parts.append(f'    <animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;{sc3_k1:.4f};{sc3_k2:.4f};{sc3_k3:.4f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append(f'    <animateTransform attributeName="transform" type="translate" values="0 0;0 0;0 -6;0 -24;0 0" keyTimes="0;{sc3_k1:.4f};{sc3_k2:.4f};{sc3_k3:.4f};1" dur="{cycle}s" repeatCount="indefinite"/>')
    svg_parts.append(f'    +{t3_score}')
    svg_parts.append('  </text>')

    # ─── Thruster Glow on Player Ship ───
    svg_parts.append(f'  <g id="thruster-glow">')
    svg_parts.append(f'    <animateTransform attributeName="transform" type="translate"')
    svg_parts.append(f'      values="{ship_values_str}"')
    svg_parts.append(f'      keyTimes="{ship_key_times_str}"')
    svg_parts.append(f'      dur="{cycle}s" repeatCount="indefinite" calcMode="spline"')
    svg_parts.append(f'      keySplines="{spline_7}"/>')
    svg_parts.append('    <ellipse cx="12" cy="18" rx="6" ry="2" fill="#ff7b72" opacity="0.6">')
    svg_parts.append('      <animate attributeName="ry" values="2;4;2" dur="0.4s" repeatCount="indefinite"/>')
    svg_parts.append('      <animate attributeName="opacity" values="0.6;0.95;0.6" dur="0.4s" repeatCount="indefinite"/>')
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
