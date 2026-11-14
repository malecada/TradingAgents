"""Facts of the daily decision panel on the registered builders (Charter 4 preparation). No price outcome.

Inputs: the item, document and record tables of the reader store, the card panel and the daily bars up to the bar
that closes at a decision (``history_features`` reads no later bar). Nothing here joins a text feature with a
return, a variance or any other price quantity dated at or after its decision.

    PYTHONPATH=.:scripts python research/multiagent-v2/charter4_design/decision_facts.py
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import reader_charter4_null_gate as null_gate  # noqa: E402
from reader_charter4_register import INPUTS  # noqa: E402
from tradingagents.reader import charter2 as c2, charter4 as c4, reading  # noqa: E402

OUT = Path(__file__).with_name("decision_facts.json")
SIGNED = ["tone_1d", "tone_prev6", "stance_1d"]


def by_year(frame: pd.DataFrame, mask: np.ndarray) -> dict:
    year = pd.DatetimeIndex(frame["date"]).year.to_numpy()
    out = {}
    for y in sorted(set(year.tolist())):
        part, days = mask & (year == y), int(frame.loc[year == y, "date"].nunique())
        out[str(int(y))] = {"days": days, "rows": int(part.sum()), "per_day": float(part.sum() / days),
                            "days_with_any": int(frame.loc[part, "date"].nunique()),
                            "assets": int(frame.loc[part, "base"].nunique())}
    return out


def density(frame: pd.DataFrame, test: np.ndarray) -> dict:
    out = {}
    for name, mask in (("tone_1d_nonzero", frame["tone_1d"] != 0), ("tone_prev6_nonzero", frame["tone_prev6"] != 0),
                       ("tone_week_nonzero", (frame["tone_1d"] + frame["tone_prev6"]) != 0),
                       ("subject_record_1d", frame["n_subject_1d"] > 0), ("subject_record_7d", frame["n_subject_7d"] > 0),
                       ("news_1d", frame["news_1d"] > 0)):
        mask = mask.to_numpy(dtype=bool)
        out[name] = {"rows": int(mask.sum()), "share": float(mask.mean()), "rows_test_days": int((mask & test).sum()),
                     "by_year": by_year(frame, mask)}
    for c in SIGNED:
        out[f"{c}_sign"] = {"positive": int((frame[c] > 0).sum()), "negative": int((frame[c] < 0).sum()),
                            "positive_test_days": int(((frame[c] > 0) & test).sum()),
                            "negative_test_days": int(((frame[c] < 0) & test).sum())}
    return out


def concentration(frame: pd.DataFrame) -> dict:
    hot = frame[frame["tone_1d"] != 0]
    counts = hot["base"].value_counts()
    return {"assets_with_any": int(len(counts)), "assets_in_panel": int(frame["base"].nunique()),
            "top": {b: int(n) for b, n in counts.head(8).items()},
            "share_of_two_largest": float(counts.reindex(list(c4.LARGE)).fillna(0).sum() / max(len(hot), 1)),
            "rows_outside_two_largest": int((~hot["base"].isin(c4.LARGE)).sum())}


def gaps(frame: pd.DataFrame, items: pd.DataFrame, docs: pd.DataFrame, records: pd.DataFrame) -> dict:
    """Timely news item rows of the members of a decision day that carry no judgement the reading rule asks for."""
    flagged = c4.item_days(reading.flag_items(items, docs))
    rows = c4.gap_rows(flagged, records)
    members = frame[["date", "base"]].drop_duplicates().rename(columns={"date": "day"})
    rows = rows.merge(members, on=["day", "base"], how="inner")
    untyped = ~rows["typed"].astype(bool)
    news = flagged[flagged["news"] & flagged["timely"]].merge(members, on=["day", "base"], how="inner")
    year = rows["day"].dt.year
    return {"timely_news_item_rows_of_members": int(len(news)), "documents_of_those_rows": int(news["doc_id"].nunique()),
            "rows_without_judgement": int(len(rows)), "documents_without_judgement": int(rows["doc_id"].nunique()),
            "untyped_rows": int(untyped.sum()), "untyped_documents": int(rows.loc[untyped, "doc_id"].nunique()),
            "read_rows_without_record": int((~untyped).sum()),
            "read_documents_without_record": int(rows.loc[~untyped, "doc_id"].nunique()),
            "rows_by_year": {str(int(y)): int(n) for y, n in year.value_counts().sort_index().items()},
            "panel_rows_gap_1d": int((frame["gap_1d"] > 0).sum()), "panel_rows_gap_7d": int((frame["gap_7d"] > 0).sum()),
            "panel_rows_gap_7d_share": float((frame["gap_7d"] > 0).mean()),
            "panel_rows_gap_7d_with_tone": int(((frame["gap_7d"] > 0) & ((frame["tone_1d"] != 0) | (frame["tone_prev6"] != 0))).sum())}


def after_controls(frame: pd.DataFrame, test: np.ndarray, resid: np.ndarray) -> dict:
    """Share of the variance of every gate feature rank that the two-step control removal leaves."""
    feats = c4.PARTIAL_SCORES[c4.GATE_SCORE][0]
    ranks = c4.feature_ranks(frame, feats)
    out = {}
    for j, f in enumerate(feats):
        ok = np.isfinite(resid[:, j])
        hot = ok & (frame[f].to_numpy() != 0)
        out[f] = {"rows_with_residual": int(ok.sum()),
                  "variance_share_left": float(np.var(resid[ok, j]) / np.var(ranks[ok, j])),
                  "variance_share_left_test_days": float(np.var(resid[ok & test, j]) / np.var(ranks[ok & test, j])),
                  "corr_residual_with_rank_on_nonzero_rows": float(np.corrcoef(resid[hot, j], ranks[hot, j])[0, 1])}
    return out


MIXES = {"tone_1d_only": (1.0, 0.0), "tone_prev6_only": (0.0, 1.0), "one_to_one": (1.0, 1.0),
         "two_to_one": (2.0, 1.0), "one_to_two": (1.0, 2.0)}


def turnover(frame: pd.DataFrame, test: np.ndarray, resid: np.ndarray) -> dict:
    """Mean daily turnover of the score book of the charter (weights in proportion to the demeaned score, gross
    exposure 2) on the test days, for fixed mixes of the two residual gate features. The turnover of a
    two-feature score depends on the ratio of its two weights only, so the range holds for any fitted score.
    No outcome is used."""
    out = {}
    for name, mix in MIXES.items():
        book = pd.DataFrame({"date": frame["date"], "symbol": frame["symbol"], "s": resid @ np.array(mix)})[test].dropna()
        centred = book["s"] - book.groupby("date")["s"].transform("mean")
        gross = centred.abs().groupby(book["date"]).transform("sum")
        book = book.assign(w=(2.0 * centred / gross).where(gross > 0)).dropna()
        weights = book.pivot(index="date", columns="symbol", values="w").fillna(0.0)
        moved = weights.diff().abs().sum(axis=1)
        moved.iloc[0] = weights.iloc[0].abs().sum()
        out[name] = {"days": int(len(weights)), "mean_turnover": float(moved.mean()),
                     "cost_bp_per_day": float(moved.mean() * c4.COST_PER_SIDE * 1e4)}
    return out


def main() -> None:
    items, docs, records = (pd.read_parquet(ROOT / INPUTS[name]) for name in ("items", "docs", "records"))
    frame = null_gate.decision_panel(ROOT).sort_values(["date", "symbol"]).reset_index(drop=True)
    if any(c in frame.columns for c in c4.TARGET_COLUMNS):
        raise SystemExit("the decision panel carries a forward column")
    days = np.sort(frame["date"].unique())
    test = frame["date"].isin(days[c4.BURN_IN_DAYS:]).to_numpy()
    every = np.ones(len(frame), dtype=bool)
    feats, controls, flexible = c4.PARTIAL_SCORES[c4.GATE_SCORE]
    resid = c4.feature_residuals(frame, feats, controls, flexible)
    out = {"panel": {"rows": int(len(frame)), "days": int(len(days)), "first_day": str(pd.Timestamp(days[0]).date()),
                     "last_day": str(pd.Timestamp(days[-1]).date()), "contracts": int(frame["symbol"].nunique()),
                     "assets": int(frame["base"].nunique()), "test_days": int(len(days) - c4.BURN_IN_DAYS),
                     "first_test_day": str(pd.Timestamp(days[c4.BURN_IN_DAYS]).date()), "rows_test_days": int(test.sum()),
                     "weekly_universe_rows": int(len(c2.universe(pd.read_parquet(ROOT / INPUTS["cards"]))))},
           "timing": c4.timing_facts(items),
           "coverage_all_days": c4.feature_coverage(frame, every), "coverage_test_days": c4.feature_coverage(frame, test),
           "density": density(frame, test), "concentration": concentration(frame),
           "gaps": gaps(frame, items, docs, records), "after_controls": after_controls(frame, test, resid),
           "turnover": turnover(frame, test, resid)}
    OUT.write_text(json.dumps(c4.json_safe(out), indent=1) + "\n")
    print(json.dumps({k: out[k] for k in ("panel", "concentration", "gaps", "after_controls", "turnover")}, indent=1))


if __name__ == "__main__":
    main()
