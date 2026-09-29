"""Frozen Jev question wording, article state and asset candidates (charter §4).

Class definitions are C1's prompt class list plus its v2 additional rules,
verbatim. Any edit changes ``questions_sha256()`` and must precede registration.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Callable

CLASSES = ("hack", "regulatory", "listing_delisting", "unlock_emission",
           "upgrade_partnership", "insolvency_halt")
GENERAL_RULES = ("Only report events the article itself asserts as fact or formal action "
                 "(not speculation, price commentary, or opinion). No knowledge of later "
                 "events; judge only the given text.")
CLASS_DEFINITIONS = {
    "hack": "exploit, breach, funds stolen or drained from a protocol/venue",
    "regulatory": ("government/agency action — lawsuit, charge, settlement, ban, "
                   "license grant/revocation, emergency order"),
    "listing_delisting": "an exchange lists or delists a specific asset",
    "unlock_emission": ("token unlock, vesting cliff, or emission-schedule news "
                        "for a specific asset"),
    "upgrade_partnership": ("protocol upgrade, mainnet launch, hard fork, or a concrete "
                            "named partnership/acquisition involving the asset"),
    "insolvency_halt": ("insolvency, bankruptcy, withdrawal halt or suspension, depeg, "
                        "collapse of a venue/fund/stablecoin"),
}
V2_RULES = {
    "regulatory": ("the target must be a crypto asset, crypto company, or crypto venue. "
                   "Enforcement against non-crypto firms or people (even by SEC/CFTC) is NOT "
                   "an event. Personnel changes and prospective/planned regulation are NOT "
                   "events. Convictions, sentencing, and extradition of crypto-company "
                   "principals ARE regulatory events for the affected venue/asset."),
    "upgrade_partnership": ("requires a concrete named action that is signed, live, or "
                            "deployed. Exploration, MOUs, and conference statements are NOT "
                            "events."),
    "listing_delisting": ("includes IDO/IEO, exchange debut, \"X lists Y\", \"trading opens\", "
                          "and \"exchange adds support for Y\"."),
}
NONE_KEY = "none"
ASSET_INSTRUCTIONS = ("Which listed entity is primarily affected by the main event the article "
                      "reports? Prefer the affected crypto asset or protocol token; use the venue "
                      "(exchange/fund) when no single asset is affected.")
NONE_OPTION = "The article reports no qualifying event, or no listed entity fits."
CONTENT_LIMIT = 4000
MAX_CANDIDATES = 30
MAX_SPAN = 3
DICTIONARY = (
    "Bitcoin", "BTC", "Ethereum", "Ether", "ETH", "Solana", "SOL", "Ripple", "XRP", "Cardano",
    "ADA", "Dogecoin", "DOGE", "BNB", "Binance", "Coinbase", "Kraken", "FTX", "FTT", "Alameda",
    "Terra", "LUNA", "UST", "Celsius", "Three Arrows", "3AC", "Voyager", "BlockFi", "Genesis",
    "Tether", "USDT", "USDC", "Circle", "Polygon", "MATIC", "Avalanche", "AVAX", "Chainlink",
    "Polkadot", "Litecoin", "LTC", "Tron", "TRX", "Shiba Inu", "SHIB", "Uniswap", "Arbitrum",
    "Optimism", "Aptos", "Cosmos", "Stellar", "XLM", "Monero", "XMR", "Bitfinex", "Huobi", "OKX",
    "OKEx", "Gemini", "Bybit", "KuCoin", "Crypto.com", "Silvergate", "Signature Bank",
    "Silicon Valley Bank", "SVB", "Worldcoin", "EigenLayer", "Lido", "Aave", "MakerDAO", "Curve",
    "Ronin", "Axie Infinity", "Wormhole", "Poly Network", "Mt. Gox", "Grayscale", "MicroStrategy",
    "Sam Bankman-Fried", "SBF", "Do Kwon", "Changpeng Zhao", "CZ",
)
STOPWORDS = frozenset("""
a an the and or but nor of in on at to for from by with without over under after before as
into onto about amid against via vs per than then this that these those it its his her their
our your my we you they he she i is are was were be been being has have had do does did will
would can could may might must shall should not no new says said say reports report update
updates news price prices market markets today week year daily how why what when where who
which here there more most just now also up down out off back first last top big full live
faces face denies deny hits hit falls fall rises rise surges surge plunges plunge jumps jump
drops drop soars soar slides slide tumbles tumble gains gain loses lose wins win gets get adds
add lists list delists delist halts halt suspends suspend receives receive reaches reach
expands expand signs sign buys buy sells sell plans plan seeks seek warns warn calls call
takes take makes make sets set hires hire joins join backs partners partner acquires acquire
settles settle bans ban approves approve rejects reject launches launch files file sues sue
charges charge fines fine opens open closes close announces announce unveils unveil
completes complete
""".split())
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9.&'$-]*")


def noul_instruction(cls: str) -> str:
    extra = f" Additional rule: {V2_RULES[cls]}" if cls in V2_RULES else ""
    return (f"The article reports a '{cls}' event. Definition: {CLASS_DEFINITIONS[cls]}."
            f"{extra} {GENERAL_RULES}")


def _text(value) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value)


def build_state(row: dict, transform: Callable[[str], str] | None = None) -> dict:
    """Headline always; summary and content (first 4,000 chars) when non-empty."""
    state = {"headline": _text(row.get("headline"))}
    summary = _text(row.get("summary"))
    content = _text(row.get("content"))[:CONTENT_LIMIT]
    if summary.strip():
        state["summary"] = summary
    if content.strip():
        state["content"] = content
    if transform is not None:
        state = {k: transform(v) for k, v in state.items()}
    return state


def _qualifies(token: str) -> bool:
    if not token or token.lower() in STOPWORDS:
        return False
    has_alpha = any(ch.isalpha() for ch in token)
    return token[0].isupper() or (has_alpha and any(ch.isdigit() for ch in token))


def _flush(run: list[str], out: list[str]) -> None:
    for i in range(len(run)):
        for n in range(min(MAX_SPAN, len(run) - i), 0, -1):
            out.append(" ".join(run[i:i + n]))


def _spans(text: str) -> list[str]:
    out: list[str] = []
    run: list[str] = []
    for raw in _TOKEN.findall(text):
        token = raw.rstrip(".'-&$")
        if _qualifies(token):
            run.append(token)
        else:
            _flush(run, out)
            run = []
    _flush(run, out)
    return out


def candidates(row: dict) -> list[str]:
    """Alpaca symbols, dictionary names, then capitalized spans; dedup; cap 30."""
    text = " ".join(_text(row.get(f)) for f in ("headline", "summary"))
    found: list[str] = []
    if row.get("store") == "alpaca":
        for symbol in _text(row.get("symbols")).split(","):
            symbol = symbol.strip().upper()
            for quote in ("USDT", "USDC", "USD"):
                if symbol.endswith(quote) and len(symbol) > len(quote):
                    symbol = symbol[: -len(quote)]
                    break
            if symbol:
                found.append(symbol)
    for name in DICTIONARY:
        match = re.search(r"(?<![A-Za-z0-9])" + re.escape(name) + r"(?![A-Za-z0-9])",
                          text, re.IGNORECASE)
        if match:
            found.append(match.group(0))
    found.extend(_spans(text))
    seen: set[str] = set()
    out: list[str] = []
    for cand in found:
        if cand.lower() not in seen:
            seen.add(cand.lower())
            out.append(cand)
    return out[:MAX_CANDIDATES]


def build_questions(cands: list[str], *, reverse: bool, with_asset: bool = True) -> dict:
    questions = {f"ev_{c}": {"type": "noul", "instructions": noul_instruction(c)}
                 for c in CLASSES}
    if with_asset and cands:
        keys = [f"c{i:02d}" for i in range(len(cands))]
        order = list(reversed(keys)) if reverse else keys
        criteria = {k: cands[int(k[1:])] for k in order}
        criteria[NONE_KEY] = NONE_OPTION
        questions["asset"] = {"type": "choice", "instructions": ASSET_INSTRUCTIONS,
                              "criteria": criteria}
    return questions


def questions_sha256() -> str:
    payload = {"classes": CLASSES, "general": GENERAL_RULES, "definitions": CLASS_DEFINITIONS,
               "v2": V2_RULES, "noul": {c: noul_instruction(c) for c in CLASSES},
               "asset": ASSET_INSTRUCTIONS, "none": NONE_OPTION, "none_key": NONE_KEY,
               "dictionary": DICTIONARY, "stopwords": sorted(STOPWORDS),
               "content_limit": CONTENT_LIMIT, "max_candidates": MAX_CANDIDATES,
               "max_span": MAX_SPAN}
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()
