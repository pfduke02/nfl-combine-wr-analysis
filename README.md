# NFL Combine WR Analysis

Do "workout warrior" wide receivers bust? Combine workouts (2006–2018 classes)
vs. career games started, adjusted for draft position.

**Write-up:** [blog_post_spikiness.md](blog_post_spikiness.md)

## Pipeline

1. `combine_data.py` — loads nflverse combine + draft data (`load_combine()`)
2. `fetch_games_started.py` — scrapes per-season games started from Pro
   Football Reference via Wayback Machine snapshots (PFR blocks direct requests)
3. `wr_success.py` — career games-started totals, joined to combine WRs
4. `wr_workout_z.py` — WR-relative workout z-scores; over/under-performer profiles
5. `wr_sd_analysis.py` — does profile "spikiness" (SD of z-scores) predict
   beating your draft slot? (Spoiler: no. r = −0.03)

Key result: expected career starts ≈ `89·exp(−pick/62) + 8`; residuals from
that curve are the success metric. See `CLAUDE.md` for data gotchas.

## Requirements

Python 3.9+ with pandas, numpy, scipy, matplotlib, requests.
