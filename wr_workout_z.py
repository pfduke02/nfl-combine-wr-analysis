"""Combine workout z-score profiles of WR draft over/under-performers.

Z-scores are computed within all 2006-2018 combine WRs (position-controlled)
and sign-aligned so higher = better (timed drills negated). Groups come from
the residual vs. the fitted draft-position expectation: among picks <= 64,
bottom residual quartile = underperformers, top quartile = overperformers.

Outputs: wr_workout_z_by_group.csv, wr_workout_z_players.csv,
wr_bust_workout_heatmap.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

WORKOUTS = ["forty", "bench", "vertical", "broad_jump", "cone", "shuttle"]
MEASUREMENTS = ["ht_in", "wt"]
LOWER_IS_BETTER = {"forty", "cone", "shuttle"}


def height_to_inches(ht: pd.Series) -> pd.Series:
    parts = ht.str.split("-", expand=True)
    return parts[0].astype(float) * 12 + parts[1].astype(float)


def zscore_within_wr(wr: pd.DataFrame) -> pd.DataFrame:
    z = pd.DataFrame(index=wr.index)
    for col in WORKOUTS + MEASUREMENTS:
        vals = wr[col].astype(float)
        s = (vals - vals.mean()) / vals.std()
        z[col] = -s if col in LOWER_IS_BETTER else s
    return z


def main():
    wr = pd.read_csv("wr_combine_success_2006_2018.csv")
    wr["ht_in"] = height_to_inches(wr["ht"])
    z = zscore_within_wr(wr)

    drafted = pd.read_csv("wr_drafted_with_expectation.csv")
    r12 = drafted[drafted["draft_ovr"] <= 64].copy()
    lo, hi = r12["resid"].quantile([0.25, 0.75])
    r12["group"] = np.select(
        [r12["resid"] <= lo, r12["resid"] >= hi], ["under", "over"], "middle")

    wr = wr.merge(r12[["pfr_id", "group", "resid"]], on="pfr_id", how="left")
    zg = z.join(wr[["player_name", "season", "draft_ovr", "group", "resid"]])

    # group means, per-cell n, and under-vs-over Welch t-test per drill
    rows = []
    for col in WORKOUTS + MEASUREMENTS:
        row = {"workout": col,
               "kind": "workout" if col in WORKOUTS else "measurement"}
        for g in ["under", "middle", "over"]:
            vals = zg.loc[zg["group"] == g, col].dropna()
            row[f"z_{g}"] = vals.mean()
            row[f"n_{g}"] = len(vals)
        u = zg.loc[zg["group"] == "under", col].dropna()
        o = zg.loc[zg["group"] == "over", col].dropna()
        row["p_under_vs_over"] = stats.ttest_ind(u, o, equal_var=False).pvalue
        rows.append(row)
    by_group = pd.DataFrame(rows)
    by_group.to_csv("wr_workout_z_by_group.csv", index=False)

    print(f"groups (picks <=64, n={len(r12)}): "
          f"under n={(r12['group'] == 'under').sum()}, "
          f"over n={(r12['group'] == 'over').sum()}")
    print("\nmean z-score by group (higher = better, WR-relative):")
    print(by_group.round(2).to_string(index=False))

    # per-player table + heatmap for the underperformers
    busts = (zg[zg["group"] == "under"]
             .sort_values("resid")
             .set_index("player_name"))
    busts.to_csv("wr_workout_z_players.csv")

    hm = busts[WORKOUTS]
    fig, ax = plt.subplots(figsize=(8, 0.42 * len(hm) + 1.5))
    im = ax.imshow(hm.to_numpy(float), cmap="RdBu", vmin=-3, vmax=3, aspect="auto")
    ax.set_xticks(range(len(WORKOUTS)), WORKOUTS, rotation=30, ha="right")
    ax.set_yticks(range(len(hm)),
                  [f"{n} ({int(p)})" for n, p in zip(hm.index, busts["draft_ovr"])])
    for i in range(hm.shape[0]):
        for j in range(hm.shape[1]):
            v = hm.iat[i, j]
            if pd.notna(v):
                ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=8)
    ax.set_title("WR-relative workout z-scores — round 1-2 underperformers (pick)")
    fig.colorbar(im, ax=ax, shrink=0.8, label="z (higher = better)")
    fig.savefig("wr_bust_workout_heatmap.png", dpi=120, bbox_inches="tight")

    print("\nsanity: John Ross forty z =",
          zg.loc[zg["player_name"] == "John Ross", "forty"].round(2).iloc[0])


if __name__ == "__main__":
    main()
