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


def test_alias_filters_and_token_safety():
    from tradingagents.dossier.entities import alias_ok
    assert not alias_ok("A") and not alias_ok("4") and not alias_ok("$4") and alias_ok("$AI") and not alias_ok("AI") and alias_ok("$OP")
    assert not alias_ok("Across") and not alias_ok("Render") and alias_ok("Ether") and alias_ok("Across Protocol") and alias_ok("Terra")
    d = build_dictionary(["BTC", "ETH", "ACX", "A", "4"])
    assert d.assets.get("A", []) == ["Vaulta"] and "4" not in d.assets and "Across" not in d.assets.get("ACX", [])
    m = Masker(d, decision_ts=pd.Timestamp("2024-01-15", tz="UTC"), seed=1, focus_asset="BTC")
    out = m.mask_text("Asset_A rose; price 102.4 and 0.2023 ratio; Bitcoin and Ether fell.")
    assert "Asset_Asset" not in out and "102.4" in out and "0.2023" in out and "Bitcoin" not in out and "Ether" not in out


def test_english_word_names_match_case_sensitively():
    d = build_dictionary(["LUNA", "BTC"])
    m = Masker(d, decision_ts=pd.Timestamp("2022-01-08", tz="UTC"), seed=1, focus_asset="LUNA")
    out = m.mask_text("Terra and LUNA rallied; luna moths and terra firma are unrelated.")
    assert out.count(m.alias("asset", "LUNA")) == 2 and "terra firma" in out and "luna moths" in out


def test_month_names_are_case_sensitive():
    d = build_dictionary(["BTC"])
    m = Masker(d, decision_ts=pd.Timestamp("2024-01-15", tz="UTC"), seed=1)
    out = m.mask_text("It may have happened in March; they march on. Dec 2023 and december.")
    assert "may have" in out and "march on" in out and "december" in out and "March" not in out and "Dec 2023" not in out
