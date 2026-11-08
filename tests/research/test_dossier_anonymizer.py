from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tradingagents.dossier.anonymizer import Masker  # noqa: E402
from tradingagents.dossier.entities import Linker, build_dictionary  # noqa: E402

BASES = ["BTC", "ETH", "SOL", "OP", "PEPE", "XAU"]


def test_dictionary_handles_ambiguous_and_non_crypto():
    d = build_dictionary(BASES)
    assert "XAU" not in d.assets
    assert "Bitcoin" in d.assets["BTC"] and "BTC" in d.assets["BTC"] and "$BTC" in d.assets["BTC"]
    assert "OP" not in d.assets["OP"] and "$OP" in d.assets["OP"] and "Optimism" in d.assets["OP"]


def test_linker_salience():
    linker = Linker(build_dictionary(BASES))
    links = dict(linker.link_assets("Solana outage drags SOL lower", "Traders rotated into ether. Bitcoin held. bitcoin ETF flows rose."))
    assert links["SOL"] == "primary" and links["BTC"] == "primary" and links["ETH"] == "mentioned"
    assert "OP" not in dict(linker.link_assets("Op-ed: the op is over", "nothing"))


def test_masker_roles_dates_prices_and_verify():
    d = build_dictionary(BASES)
    m = Masker(d, decision_ts=pd.Timestamp("2024-01-15", tz="UTC"), seed=7, focus_asset="BTC")
    text = ("Bitcoin fell to $41,250 on January 3, 2024 after the SEC sued Binance; CZ resigned in 2023. "
            "Ethereum's Dencun upgrade is set for March 13. A $140 million exploit hit Solana DEX. Q4 2023 revenue")
    out = m.mask_text(text)
    assert "Bitcoin" not in out and "Binance" not in out and "CZ" not in out and "Ethereum" not in out
    assert "2024" not in out and "2023" not in out and "$41,250" not in out
    assert "$140 million" in out and "[price level]" in out and "12 days ago" in out and "in 58 days" in out
    assert "[period] revenue" in out and "about 12 months ago" in out
    assert out.startswith(m.alias("asset", "BTC")) and m.alias("asset", "BTC") == out.split()[0]
    assert m.verify(out) == []
    assert {"asset:Bitcoin", "year"} <= set(m.verify("Bitcoin 2021"))
    m2 = Masker(d, decision_ts=pd.Timestamp("2024-01-15", tz="UTC"), seed=8, focus_asset="BTC")
    assert m2.alias("asset", "BTC") != m.alias("asset", "BTC") or m2.alias("asset", "ETH") != m.alias("asset", "ETH")


def test_synonyms_share_one_token():
    d = build_dictionary(BASES)
    m = Masker(d, decision_ts=pd.Timestamp("2024-01-15", tz="UTC"), seed=1)
    out = m.mask_text("The SEC and the Securities and Exchange Commission; SBF and Sam Bankman-Fried; OKX and OKEx.")
    toks = out.replace(";", " ").replace(".", " ").split()
    assert len({t for t in toks if t.startswith("Regulator_")}) == 1
    assert len({t for t in toks if t.startswith("Person_")}) == 1
    assert len({t for t in toks if t.startswith("Exchange_")}) == 1
