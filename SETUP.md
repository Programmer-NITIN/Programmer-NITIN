# GitHub Profile README Setup — Nitin Patidar (@Programmer-NITIN)

Everything here belongs in a repository named **`Programmer-NITIN`** under your GitHub account (`github.com/Programmer-NITIN/Programmer-NITIN`). That special repository's `README.md` is what GitHub displays on your public profile!

---

## 1. Quick Push to GitHub

From inside this folder (`c:\Users\nitin\github profile\Programmer-NITIN`):

```bash
git init
git branch -M main
git add .
git commit -m "feat: Nitin Patidar GitHub profile README with generated assets"
git remote add origin https://github.com/Programmer-NITIN/Programmer-NITIN.git
git push -u origin main
```

> **Note:** The repository must be **public** — SVGs and badge assets are loaded by URL, so private repos will show broken images.

---

## 2. Enable GitHub Actions Permissions

To allow automated daily updates to your contribution graph, language radar, and stat cards:

1. Go to your repo: `https://github.com/Programmer-NITIN/Programmer-NITIN`
2. Click **Settings** → **Actions** → **General**
3. Scroll down to **Workflow permissions**
4. Select **Read and write permissions**
5. Click **Save**

---

## 3. Add `METRICS_TOKEN` (for 3D Isometric Calendar & Achievements)

The `lowlighter/metrics` workflow requires a personal access token to render the 3D isometric contribution calendar:

1. Go to **[GitHub Token Settings](https://github.com/settings/tokens)** → **Generate new token (classic)**
2. Note: `METRICS_TOKEN`
3. Scopes required:
   - ✅ **`read:user`**
   - ✅ **`repo`** (optional, if you want private contributions counted)
4. Copy the generated token.
5. In your profile repo: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
6. Name: **`METRICS_TOKEN`**
7. Value: *(paste the token)* → Click **Add secret**

---

## 4. Run Workflows

In your repo, go to the **Actions** tab:
1. **Metrics** → Click **Run workflow** (generates 3D isometric calendar, languages, achievements)
2. **Snake** → Click **Run workflow** (generates snake eating contribution graph into `output` branch)
3. **Charts and cards** → Click **Run workflow** (refreshes radar charts & repo cards)

---

## 5. Tuning & Regenerating Local Assets

All asset generation scripts are in `scripts/`:

### Regenerate Portrait
```powershell
python scripts/dotify.py assets/jacket.png -o assets/portrait --cols 100 --equalize --detail 0.5 --color --reveal
```

### Regenerate Radar Charts
```powershell
python scripts/radar.py --data assets/skills.json -o assets/radar
python scripts/radar.py --github Programmer-NITIN -o assets/radar-langs --values
```

### Regenerate Cards
```powershell
python scripts/cards.py --user Programmer-NITIN --projects assets/projects.json --out assets
```

### Regenerate & Tune 3D Animated Isometric Calendar
Adjust building height, animation speed, color themes, and streaks in `assets/calendar.json`, or run via CLI:

```powershell
# Default settings using assets/calendar.json
python scripts/isocalendar.py

# Custom building height (e.g. taller skyscrapers 2.0x) and fast 0.8s animation
python scripts/isocalendar.py --height 2.0 --duration 0.8 --stagger 0.015

# Different palettes (github, emerald, halloween, winter, cyberpunk)
python scripts/isocalendar.py --palette emerald

# Infinite wave animation loop
python scripts/isocalendar.py --loop
```

### Local Preview
Open `preview.html` in your browser at any time to visually check all dark & light assets and click **replay building animation**!

