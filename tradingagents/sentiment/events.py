"""GDELT V2Themes → CryptoEventType taxonomy + extractor."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Tuple

import pandas as pd

from tradingagents.sentiment.snapshot import CryptoEventType, EventFlag


THEME_TO_EVENT: dict[str, CryptoEventType] = {
    # Regulatory
    "LEGISLATION": CryptoEventType.SEC_RULEMAKING,
    "ECON_GOVCRYPTO": CryptoEventType.NATIONAL_REG,
    "TAX_FNCACT_REGULATOR": CryptoEventType.SEC_RULEMAKING,
    "LEGAL_TRIAL": CryptoEventType.SEC_ENFORCEMENT,
    # Security
    "CYBER_ATTACK": CryptoEventType.EXCHANGE_HACK,
    "TERROR_HACK": CryptoEventType.PROTOCOL_EXPLOIT,
    # Market structure
    "ECON_STOCKMARKET": CryptoEventType.ETF_FLOW,
    "ECON_BUSINESS_LISTING": CryptoEventType.EXCHANGE_LISTING,
    # Macro
    "ECON_INTEREST_RATES": CryptoEventType.FED_FOMC,
    "ECON_INFLATION": CryptoEventType.CPI_PRINT,
    "WB_2459_FOREIGN_EXCHANGE_RATES": CryptoEventType.DXY_EXTREME,
}


_KEYWORD_OVERRIDES: list[tuple[str, CryptoEventType, int]] = [
    ("hack", CryptoEventType.EXCHANGE_HACK, -1),
    ("exploit", CryptoEventType.PROTOCOL_EXPLOIT, -1),
    ("bridge", CryptoEventType.BRIDGE_EXPLOIT, -1),
    ("etf approval", CryptoEventType.ETF_APPROVAL_DENIAL, +1),
    ("etf denial", CryptoEventType.ETF_APPROVAL_DENIAL, -1),
    ("halving", CryptoEventType.HALVING, +1),
    ("fork", CryptoEventType.HARD_FORK, 0),
    ("upgrade", CryptoEventType.NETWORK_UPGRADE, +1),
    ("sec ", CryptoEventType.SEC_ENFORCEMENT, -1),
    ("cftc", CryptoEventType.CFTC_ACTION, -1),
    ("mica", CryptoEventType.MICA_EU, 0),
    ("fomc", CryptoEventType.FED_FOMC, 0),
    ("cpi", CryptoEventType.CPI_PRINT, 0),
]


def classify_event_rule(themes: str, headline: str) -> Tuple[CryptoEventType, float]:
    """Rule-based event classifier. Returns (event_type, confidence)."""
    hl_lower = (headline or "").lower()
    for kw, et, _ in _KEYWORD_OVERRIDES:
        if kw in hl_lower:
            return et, 0.85
    theme_tokens = (themes or "").split(";")
    for tok in theme_tokens:
        tok = tok.strip().split(",", 1)[0]
        if tok in THEME_TO_EVENT:
            return THEME_TO_EVENT[tok], 0.6
    return CryptoEventType.NONE, 0.0


def _direction_hint(et: CryptoEventType, headline: str) -> int:
    hl = (headline or "").lower()
    for kw, kw_et, direction in _KEYWORD_OVERRIDES:
        if kw_et == et and kw in hl:
            return direction
    if et in {CryptoEventType.EXCHANGE_HACK, CryptoEventType.PROTOCOL_EXPLOIT,
              CryptoEventType.BRIDGE_EXPLOIT, CryptoEventType.SEC_ENFORCEMENT}:
        return -1
    if et in {CryptoEventType.ETF_APPROVAL_DENIAL, CryptoEventType.NETWORK_UPGRADE,
              CryptoEventType.HALVING}:
        return +1
    return 0


def extract_events(
    gdelt_rows: pd.DataFrame,
    coin: str,
    as_of: datetime,
    *,
    max_events: int = 50,
) -> List[EventFlag]:
    """Build EventFlag list from a GDELT rows dataframe, PIT-enforced."""
    if gdelt_rows.empty:
        return []
    coin_upper = coin.upper() if coin.upper() in {"BTC", "ETH"} else "MULTI"
    flags: List[EventFlag] = []
    df = gdelt_rows.copy()
    # PIT filter
    if "as_of_ts" in df.columns:
        df = df[pd.to_datetime(df["as_of_ts"], utc=True) < as_of]
    df = df.head(max_events)
    for row in df.itertuples(index=False):
        themes = getattr(row, "themes", "") or ""
        headline = getattr(row, "headline", "") or ""
        et, conf = classify_event_rule(themes, headline)
        if et == CryptoEventType.NONE:
            continue
        flags.append(EventFlag(
            event_type=et,
            asset=coin_upper,
            direction_hint=_direction_hint(et, headline),
            severity=0.5,
            event_ts=pd.to_datetime(getattr(row, "event_ts"), utc=True).to_pydatetime(),
            as_of_ts=pd.to_datetime(getattr(row, "as_of_ts"), utc=True).to_pydatetime(),
            half_life_days=3.0,
            source_url=getattr(row, "url", None) or None,
            confidence=conf,
        ))
    return flags
