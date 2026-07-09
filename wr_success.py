"""Build the WR success dataset.

1. Summarize games_started_raw.csv to one row per player (career totals).
2. Join career games started onto combine + draft data for WRs from the
   2006-2018 combines.

Outputs: career_starts.csv, wr_combine_success_2006_2018.csv
"""

import pandas as pd

from combine_data import load_combine


def build():
    per_season = pd.read_csv("games_started_raw.csv")
    career = (per_season.groupby("pfr_id")
              .agg(player_name=("player_name", "last"),
                   seasons=("season", "nunique"),
                   career_g=("g", "sum"),
                   career_gs=("gs", "sum"))
              .reset_index())
    career.to_csv("career_starts.csv", index=False)

    combine = load_combine(since=2000)
    wr = combine[(combine["pos"] == "WR")
                 & combine["season"].between(2006, 2018)].copy()
    wr = wr.merge(career.drop(columns="player_name"), on="pfr_id", how="left")
    # no stats rows means the player never logged an NFL target: 0 starts
    for col in ["seasons", "career_g", "career_gs"]:
        wr[col] = wr[col].fillna(0).astype(int)
    wr.to_csv("wr_combine_success_2006_2018.csv", index=False)
    return career, wr


if __name__ == "__main__":
    career, wr = build()
    print(f"career_starts.csv: {len(career)} players")
    print(f"wr_combine_success_2006_2018.csv: {len(wr)} WRs, "
          f"{wr['draft_ovr'].notna().sum()} drafted")
    print("\ntop 5 by career games started:")
    cols = ["player_name", "season", "draft_ovr", "career_g", "career_gs"]
    print(wr.nlargest(5, "career_gs")[cols].to_string(index=False))
