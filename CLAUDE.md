# Football combine / draft analysis

Exploring NFL combine data vs. draft position and career outcomes. Everything
is pandas-based (python3, no venv yet); plots use matplotlib `Agg` and are
saved as PNGs in the project root.

## Data sources
- **Combine + draft**: nflverse free release
  (`https://github.com/nflverse/nflverse-data/releases/download/combine/combine.csv`),
  originally scraped from Pro Football Reference. Cached as `combine_raw.csv`
  (2000–2026 combines, includes `pfr_id`).
- **Games started**: Pro Football Reference yearly receiving pages. PFR
  **403-blocks direct requests/curl** even with browser headers — fetch through
  Wayback Machine snapshots instead
  (`https://web.archive.org/web/2026/<pfr-url>`), which works fine. Any
  snapshot after a season ends has final numbers.

## Files
- `combine_data.py` — `load_combine(since=2007)` loads/filters combine data.
- `fetch_games_started.py` — scrapes G/GS per player-season (2006–2025) via
  Wayback → `games_started_raw.csv`.
- `wr_success.py` — summarizes to career totals (`career_starts.csv`) and
  joins onto 2006–2018 combine WRs → `wr_combine_success_2006_2018.csv`.
- `nfl_combine_2007_2026.csv` — the main "giant CSV" deliverable.

## Gotchas
- Join player tables on `pfr_id`, never on name.
- Draft columns are nullable `Int64`; NaN/`<NA>` in `draft_ovr` = undrafted,
  not missing. Blank workout cells = player skipped that drill.
- Missing `career_gs` after the join means the player never logged an NFL
  target → fill with 0 (done in `wr_success.py`).
- PFR row format changed over time: newer pages use
  `name_display`/`games`/`games_started` data-stats, older ones
  `player`/`g`/`gs`; player id comes from the `/players/X/<id>.htm` href.
  Traded players have a combined "2TM" row — dedupe per season by max games.
- PFR ids can contain literal dots (A.J. Green = `GreeA.00`, D.J. Moore =
  `MoorD.00`) — don't assume `\w+` or stop at `.` when parsing them.
- Expected-starts curve: `career_gs ≈ 89·exp(−pick/62) + 8` (fit in
  `wr_drafted_with_expectation.csv`, script inline in conversation).
- Workout z-scores (`wr_workout_z.py`): computed within all 2006–2018 combine
  WRs, sign-aligned so **higher = better** (forty/cone/shuttle negated).
  Per-drill n varies a lot — many players skip bench/agility drills.
- Raw `pos` has 25 labels; collapse to QB/RB/WR/TE/OL/DL/LB/DB/ST for plots
  (mapping in the by-position plot code / conversation).
- "Success" metric so far: career games started (GS), summed 2006–2025.
  Caveat: still-active players (recent classes) have truncated careers.
