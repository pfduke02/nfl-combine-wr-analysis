"""Load NFL combine data (nflverse) into pandas.

Usage:
    from combine_data import load_combine
    df = load_combine()            # 2007-2026, the "last 20 years" slice
    df = load_combine(since=2000)  # full raw dataset
"""

import pandas as pd

RAW_URL = "https://github.com/nflverse/nflverse-data/releases/download/combine/combine.csv"
RAW_PATH = "combine_raw.csv"

COLUMNS = [
    "pfr_id", "player_name", "pos", "season", "school",
    "draft_year", "draft_team", "draft_round", "draft_ovr",
    "ht", "wt", "forty", "bench", "vertical", "broad_jump", "cone", "shuttle",
]


def load_combine(since: int = 2007, local: bool = True) -> pd.DataFrame:
    """Return combine data from `since` onward, one row per player."""
    df = pd.read_csv(RAW_PATH if local else RAW_URL)
    df = df.loc[df["season"] >= since, COLUMNS].reset_index(drop=True)
    # nullable Int64 so draft picks read as 13, not 13.0
    for col in ["draft_year", "draft_round", "draft_ovr", "wt", "bench",
                "broad_jump"]:
        df[col] = df[col].astype("Int64")
    return df


if __name__ == "__main__":
    df = load_combine()
    df.to_csv("nfl_combine_2007_2026.csv", index=False)
    print(df.head().to_string())
    print(f"\n{df.shape[0]} rows, {df['draft_ovr'].notna().sum()} drafted")
