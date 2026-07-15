"""Event-bar feature assembly. Every feature uses data <= close of the
event-signal bar t (PIT). On-chain/derivatives come from the PIT store
(build_pit_onchain_features is PIT by construction); missing coverage
stays NaN — never zero-filled (CPI zero-fill lesson)."""
from __future__ import annotations

import numpy as np
import pandas as pd

# Exact PIT-store columns consumed (all causal, oc_-prefixed by the loader).
# Names verified 2026-07 against tradingagents/dataflows/onchain_features.py
# `_add_derived` / `_add_derivatives_derived` output (real column names, not
# guessed): active-address z-score is `oc_active_addr_z_30d`, exchange
# net-flow z-score is `oc_net_flow_z_30d`, and MVRV Z-Score is the
# Glassnode-style 4-year full-cycle window `oc_mvrv_z_4y` (the 1y variant
# `oc_mvrv_z_1y` also exists but is not used here).
OC_FEATURES = [
    "oc_funding_rate", "oc_funding_z_30d", "oc_funding_oiw_z_30d",
    "oc_oi_chg_7d", "oc_oi_z_30d", "oc_oi_to_mcap",
    "oc_liq_asym_z_30d", "oc_liq_total_z_30d",
    "oc_smart_money_z_30d", "oc_taker_asym_z_30d", "oc_basis_z_30d",
    "oc_active_addr_z_30d", "oc_net_flow_z_30d", "oc_mvrv_z_4y",
]


def price_trend_features(
    ohlcv: pd.DataFrame, votes: pd.Series, event_dates: pd.DatetimeIndex
) -> pd.DataFrame:
    df = ohlcv.set_index(pd.DatetimeIndex(ohlcv["Date"]))
    close = df["Close"].astype(float)
    logret = np.log(close).diff()
    sigma = logret.ewm(span=20).std()

    above = (votes > 0.5).astype(int)
    grp = (above != above.shift(1)).cumsum()
    trend_age = above.groupby(grp).cumcount().where(votes.notna())

    feats = pd.DataFrame({
        "f_vote": votes,
        "f_trend_age": trend_age,
        "f_dist_20d_high": close / close.rolling(20).max() - 1.0,
        "f_ret_20d": close.pct_change(20),
        "f_ret_60d": close.pct_change(60),
        "f_sigma_level": sigma,
        "f_sigma_pctl_60d": sigma.rolling(60).rank(pct=True),
        "f_volvol": sigma.pct_change().rolling(20).std(),
    })
    return feats.reindex(event_dates)


def assemble_dataset(per_coin: dict) -> tuple[pd.DataFrame, pd.Series, pd.Series, pd.DataFrame]:
    coins = sorted(per_coin)

    # Cross-coin breadth: fraction of coins with vote > 0.5 per bar.
    all_votes = pd.concat(
        {c: per_coin[c]["votes"] for c in coins}, axis=1
    )
    breadth = (all_votes > 0.5).sum(axis=1) / all_votes.notna().sum(axis=1).clip(lower=1)

    xs, ys, ws, metas = [], [], [], []
    for coin in coins:
        blob = per_coin[coin]
        labels = blob["labels"]
        if not len(labels):
            continue
        ev = pd.DatetimeIndex(labels.index)
        x = price_trend_features(blob["ohlcv"], blob["votes"], ev)

        oc = blob.get("onchain")
        if oc is not None and getattr(oc.index, "tz", None) is not None:
            # Defense-in-depth: build_pit_onchain_features returns a UTC
            # tz-aware index; event dates (ev) are tz-naive, so reindexing
            # a tz-aware series against them silently returns all-NaN
            # (pandas does not raise). Normalize here regardless of what
            # the caller already did.
            oc = oc.copy()
            oc.index = oc.index.tz_localize(None)
        for col in OC_FEATURES:
            x[col] = oc[col].reindex(ev) if oc is not None and col in oc.columns else np.nan

        fng = blob.get("fng")
        x["f_fng"] = fng.reindex(ev) if fng is not None else np.nan
        x["f_breadth"] = breadth.reindex(ev)
        for c2 in coins:
            x[f"coin_{c2}"] = float(c2 == coin)

        xs.append(x)
        ys.append(labels["label"])
        ws.append(blob["weights"])
        m = labels[["entry_exec_date", "touch_date", "ret", "sigma"]].copy()
        m["coin"] = coin
        m["event_date"] = ev
        metas.append(m)

    X = pd.concat(xs, ignore_index=True)
    y = pd.concat(ys, ignore_index=True).astype(int)
    w = pd.concat(ws, ignore_index=True)
    meta = pd.concat(metas, ignore_index=True)
    return X, y, w, meta
