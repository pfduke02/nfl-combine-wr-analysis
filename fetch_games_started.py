"""Fetch per-season games/games-started for all receivers, 2006-2025.

Pro Football Reference blocks scripted requests (403), so pages are fetched
through Wayback Machine snapshots instead. Any snapshot taken after a season
ends has that season's final numbers.

Output: games_started_raw.csv with one row per player-season
(pfr_id, player_name, season, pos, g, gs).
"""

import re
import time

import pandas as pd
import requests

SEASONS = range(2006, 2026)
WAYBACK = "https://web.archive.org/web/2026/https://www.pro-football-reference.com/years/{yr}/receiving.htm"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

# newer pages use name_display/games/games_started; older ones player/g/gs
ROW_RE = re.compile(
    r'data-stat="(?:name_display|player)"[^>]*>'
    # ids can contain dots (A.J. Green -> GreeA.00), so match up to .htm
    r'<a href="[^"]*/players/./(?P<pid>[^/"]+?)\.htm">(?P<name>[^<]+)</a></td>'
    r'.*?data-stat="(?:games|g)"[^>]*>(?P<g>\d*)'
    r'.*?data-stat="(?:games_started|gs)"[^>]*>(?P<gs>\d*)',
    re.S,
)
POS_RE = re.compile(r'data-stat="pos"[^>]*>(?P<pos>[A-Za-z/\-]*)<')


def parse_season(html: str, season: int) -> pd.DataFrame:
    rows = []
    for chunk in html.split("<tr")[1:]:
        m = ROW_RE.search(chunk)
        if not m:
            continue
        p = POS_RE.search(chunk)
        rows.append({
            "pfr_id": m["pid"],
            "player_name": m["name"],
            "season": season,
            "pos": p["pos"] if p else "",
            "g": int(m["g"] or 0),
            "gs": int(m["gs"] or 0),
        })
    df = pd.DataFrame(rows)
    # traded players can appear as a combined (2TM) row plus per-team rows;
    # the combined row carries the full-season totals
    return (df.sort_values("g", ascending=False)
              .groupby("pfr_id", as_index=False).first())


def main():
    frames = []
    for yr in SEASONS:
        for attempt in (1, 2):
            try:
                r = requests.get(WAYBACK.format(yr=yr), headers=HEADERS, timeout=60)
                if r.status_code == 200 and "data-stat" in r.text:
                    break
            except requests.RequestException as e:
                print(f"{yr}: attempt {attempt} failed ({e})")
            time.sleep(5)
        else:
            print(f"{yr}: FAILED, skipping")
            continue
        df = parse_season(r.text, yr)
        frames.append(df)
        print(f"{yr}: {len(df)} players")
        time.sleep(2)

    out = pd.concat(frames, ignore_index=True)
    out.to_csv("games_started_raw.csv", index=False)
    print(f"\nsaved games_started_raw.csv: {len(out)} player-seasons")


if __name__ == "__main__":
    main()
