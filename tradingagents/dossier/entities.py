"""Entity dictionary and linking for the universe (plan §5.2, §6.2 step 2).

Assets come from the card universe (Binance base symbols) joined to CoinGecko's
top-1000 names; exchanges, people, networks and institutions are curated lists.
Linking is dictionary-based with word boundaries; salience is ``primary`` when
the asset appears in the title or at least twice in the body.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re

COINGECKO = Path("data/dossier/coingecko_markets_top1000.json")

# Short tickers that collide with English words or other entities; require the $ prefix
# or an explicit name match for these.
AMBIGUOUS_TICKERS = {"OP", "ARB", "LINK", "ONE", "SUN", "GAS", "PEOPLE", "ME", "ACT", "AI", "API",
                     "CAT", "DOG", "BOB", "MOG", "TRB", "MASK", "BLUR", "FLOW", "NEAR", "WAVES",
                     "STORJ", "BAND", "LIT", "GRT", "ENS", "T", "C", "S", "W", "G", "PENGU", "WIF",
                     "TON", "APE", "BAT", "ICP", "FET", "TIA", "SEI", "SUI", "JUP", "RAY", "IO", "ZK",
                     "GMT", "GMX", "CRV", "SNX", "COMP", "YFI", "CAKE", "RUNE", "ROSE", "IOTA", "ATOM",
                     "EOS", "NEO", "DASH", "ZEC", "XAU", "XAG", "CL", "LAB", "MU", "SNDK", "HYPE"}
EXTRA_ALIASES = {"LUNA": ["Terra", "Luna", "Terra Luna"], "LUNC": ["Terra Classic", "Luna Classic"], "BTC": ["Bitcoin", "XBT"], "ETH": ["Ethereum", "Ether"], "SOL": ["Solana"],
                 "XRP": ["Ripple", "XRP Ledger"], "DOGE": ["Dogecoin"], "BNB": ["BNB Chain", "Binance Coin"],
                 "ADA": ["Cardano"], "AVAX": ["Avalanche"], "DOT": ["Polkadot"], "MATIC": ["Polygon"],
                 "POL": ["Polygon"], "LTC": ["Litecoin"], "LINK": ["Chainlink"], "TON": ["Toncoin"],
                 "SHIB": ["Shiba Inu"], "WIF": ["Dogwifhat"], "PEPE": ["Pepe"], "UNI": ["Uniswap"],
                 "ATOM": ["Cosmos"], "NEAR": ["Near Protocol"], "ARB": ["Arbitrum"], "OP": ["Optimism"],
                 "APT": ["Aptos"], "SUI": ["Sui"], "TRX": ["Tron"], "XLM": ["Stellar"], "HBAR": ["Hedera"],
                 "FIL": ["Filecoin"], "ICP": ["Internet Computer"], "TIA": ["Celestia"], "INJ": ["Injective"],
                 "RUNE": ["THORChain"], "AAVE": ["Aave"], "MKR": ["MakerDAO", "Maker"], "LDO": ["Lido"],
                 "CRV": ["Curve"], "HYPE": ["Hyperliquid"], "ENA": ["Ethena"], "ONDO": ["Ondo"], "ZEC": ["Zcash"],
                 "XMR": ["Monero"], "BCH": ["Bitcoin Cash"], "ETC": ["Ethereum Classic"], "WLD": ["Worldcoin"],
                 "FET": ["Fetch.ai"], "TAO": ["Bittensor"], "RENDER": ["Render"], "BONK": ["Bonk"], "FLOKI": ["Floki"]}
# Base symbols that are tokenized equities, commodities or indices on Binance, not crypto assets.
NON_CRYPTO_BASES = {"XAU", "XAG", "CL", "SNDK", "MU", "LAB"}

EXCHANGES = ["Binance", "Binance.US", "Coinbase", "Kraken", "FTX", "FTX US", "Alameda", "Alameda Research",
             "Bitfinex", "Huobi", "HTX", "OKX", "OKEx", "Gemini", "Bybit", "KuCoin", "Crypto.com", "Bitstamp",
             "Bittrex", "Gate.io", "MEXC", "Bitget", "Upbit", "Bithumb", "Deribit", "BitMEX", "Poloniex",
             "Hyperliquid", "dYdX", "Robinhood", "eToro", "Mt. Gox", "Celsius", "Voyager", "BlockFi",
             "Genesis", "Three Arrows Capital", "3AC", "Grayscale", "MicroStrategy", "Strategy", "Tether",
             "Circle", "Paxos", "Silvergate", "Signature Bank", "Silicon Valley Bank", "SVB", "BlackRock",
             "Fidelity", "Galaxy Digital", "Jump Trading", "Wintermute", "Cumberland", "Coinglass",
             "Chainalysis", "Consensys", "Ledger", "Trezor", "Ripple Labs", "Ripple"]
PEOPLE = ["Sam Bankman-Fried", "Bankman-Fried", "SBF", "Changpeng Zhao", "CZ", "Do Kwon", "Michael Saylor",
          "Saylor", "Gary Gensler", "Gensler", "Jerome Powell", "Powell", "Brian Armstrong", "Armstrong",
          "Vitalik Buterin", "Buterin", "Vitalik", "Elon Musk", "Musk", "Justin Sun", "Arthur Hayes",
          "Richard Teng", "Jesse Powell", "Paul Atkins", "Donald Trump", "Trump", "Joe Biden", "Biden",
          "Cathie Wood", "Larry Fink", "Alex Mashinsky", "Su Zhu", "Kyle Davies", "Caroline Ellison",
          "Gavin Wood", "Anatoly Yakovenko", "Charles Hoskinson", "Brad Garlinghouse", "Barry Silbert",
          "Hester Peirce", "Elizabeth Warren", "Warren", "Mark Karpeles"]
REGULATORS = ["SEC", "Securities and Exchange Commission", "CFTC", "Commodity Futures Trading Commission",
              "DOJ", "Department of Justice", "Treasury", "OFAC", "FinCEN", "Federal Reserve", "Fed",
              "FCA", "ESMA", "BaFin", "MAS", "MiCA", "IRS", "OCC", "FDIC", "FSA", "FATF", "Congress", "Senate",
              "White House", "European Central Bank", "ECB", "Bank of England", "People's Bank of China",
              "PBoC", "Reserve Bank of India", "RBI"]
NETWORKS = ["Ethereum", "Ether", "Bitcoin", "Solana", "BNB Chain", "BSC", "Binance Smart Chain", "Polygon",
            "Arbitrum", "Optimism", "Base", "Avalanche", "Tron", "Cardano", "Polkadot", "Cosmos", "Near",
            "Aptos", "Sui", "Fantom", "Sonic", "Algorand", "Tezos", "Stellar", "Ripple", "XRP Ledger", "Litecoin",
            "Dogecoin", "Bitcoin Cash", "Monero", "Zcash", "Hedera", "Internet Computer", "Filecoin", "Celestia",
            "Starknet", "zkSync", "Linea", "Scroll", "Mantle", "Blast", "Sei", "Injective", "Kaspa", "TON",
            "Toncoin", "Lightning Network", "Uniswap", "Aave", "Lido", "MakerDAO", "Maker", "Curve", "Compound",
            "Sushi", "SushiSwap", "PancakeSwap", "Jupiter", "Raydium", "EigenLayer", "Pendle", "Ethena",
            "Chainlink", "The Graph", "Wormhole", "LayerZero", "Ronin", "Axie Infinity", "OpenSea", "Blur",
            "Pump.fun", "Terra", "Luna", "UST", "TerraUSD", "Anchor Protocol", "USDC", "USDT", "DAI", "BUSD",
            "USDe", "FDUSD", "PYUSD", "TUSD", "WBTC", "stETH", "Pepe", "Shiba Inu", "Dogwifhat", "Bonk",
            "Floki", "Worldcoin", "Render", "Fetch.ai", "Bittensor", "Hyperliquid", "Ondo", "Mantra"]
SYNONYMS = {
    "SEC": ["Securities and Exchange Commission"], "CFTC": ["Commodity Futures Trading Commission"],
    "DOJ": ["Department of Justice"], "Federal Reserve": ["Fed"], "ECB": ["European Central Bank"],
    "PBoC": ["People's Bank of China"], "RBI": ["Reserve Bank of India"],
    "OKX": ["OKEx"], "Huobi": ["HTX"], "FTX": ["FTX US"], "Three Arrows Capital": ["3AC"],
    "Alameda Research": ["Alameda"], "Silicon Valley Bank": ["SVB"], "Ripple Labs": ["Ripple"],
    "MicroStrategy": ["Strategy"],
    "Sam Bankman-Fried": ["Bankman-Fried", "SBF"], "Changpeng Zhao": ["CZ"], "Michael Saylor": ["Saylor"],
    "Gary Gensler": ["Gensler"], "Jerome Powell": ["Powell"], "Brian Armstrong": ["Armstrong"],
    "Vitalik Buterin": ["Buterin", "Vitalik"], "Elon Musk": ["Musk"], "Donald Trump": ["Trump"],
    "Joe Biden": ["Biden"], "Elizabeth Warren": ["Warren"],
    "BNB Chain": ["BSC", "Binance Smart Chain"], "Terra": ["Luna", "TerraUSD", "UST"], "TON": ["Toncoin"],
    "Maker": ["MakerDAO"], "Sushi": ["SushiSwap"],
}
_ALIAS_TO_CANON = {a: c for c, aliases in SYNONYMS.items() for a in aliases}


def canonical_key(term: str) -> str:
    return _ALIAS_TO_CANON.get(term, term)


_MONTHS = ("January|February|March|April|May|June|July|August|September|October|November|December|"
           "Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec")
DATE_RE = re.compile(rf"\b(?:{_MONTHS})\.? ?\d{{0,2}}(?:st|nd|rd|th)?,? ?(?:20\d{{2}})?\b|(?<![\d.])20\d{{2}}(?!\.?\d)"
                     rf"|\b(?:Q[1-4]|H[12]|FY)\s?20\d{{2}}\b", re.IGNORECASE)
PRICE_LEVEL_RE = re.compile(r"\$\s?\d{1,3}(?:,\d{3})+(?:\.\d+)?(?!\s*(?:million|billion|trillion|mln|bln|[mbk]\b))"
                            r"|\$\s?\d{2,6}(?:\.\d+)?(?!\s*(?:million|billion|trillion|mln|bln|[mbk]\b))\b")


@dataclass
class Dictionary:
    assets: dict[str, list[str]]            # base symbol -> alias list (names, tickers)
    exchanges: list[str] = field(default_factory=lambda: list(EXCHANGES))
    people: list[str] = field(default_factory=lambda: list(PEOPLE))
    regulators: list[str] = field(default_factory=lambda: list(REGULATORS))
    networks: list[str] = field(default_factory=lambda: list(NETWORKS))

    def all_terms(self) -> list[tuple[str, str, str]]:
        """(term, role, key) for every alias, longest first."""
        out = []
        for base, aliases in self.assets.items():
            out += [(a, "asset", base) for a in aliases]
        out += [(x, "exchange", canonical_key(x)) for x in self.exchanges]
        out += [(x, "person", canonical_key(x)) for x in self.people]
        out += [(x, "regulator", canonical_key(x)) for x in self.regulators]
        out += [(x, "network", canonical_key(x)) for x in self.networks]
        return sorted(out, key=lambda t: -len(t[0]))


def _name_aliases(name: str) -> list[str]:
    out = {name}
    low = name.lower()
    for suffix in (" token", " coin", " network", " protocol", " finance", " chain"):
        if low.endswith(suffix) and len(name) > len(suffix) + 2:
            out.add(name[: -len(suffix)])
    return sorted(out)


_WORDS_FILE = Path("/usr/share/dict/words")
_ENGLISH = {w.strip().lower() for w in _WORDS_FILE.read_text(errors="ignore").splitlines()} if _WORDS_FILE.exists() else set()
# Single English words that are too common in finance prose to serve as case-sensitive proper-name aliases.
NAME_BLOCKLIST = {"Across", "Just", "Only", "Bounce", "Civic", "Origin", "Quant", "Measurable", "Request", "Status",
                  "Function", "Data", "Chain", "Bit", "Coin", "Token", "Prime", "Trust", "Safe", "Zero", "Ever", "Big",
                  "Act", "Mode", "Move", "Sign", "Super", "Turbo", "Book", "Mother", "Drift", "Hunt", "Mango", "Orca",
                  "Ray", "Usual", "Layer", "Swell", "Alpha", "Beta", "Gamma", "Delta", "Omega", "Pixel", "Pixels", "Story",
                  "Virtual", "Magic", "Spell", "Echo", "Fire", "Air", "Beam", "Cool", "Ice", "Port", "Moon", "Sun", "Dog",
                  "Cat", "People", "Band", "Core", "Ark", "Gas", "Mask", "Blur", "Flow", "Near", "Lit", "Wave", "Waves",
                  "Link", "One", "Stable", "Meme", "Hype", "Protocol", "Network", "Finance", "Swap", "Dash", "Neo", "Hedera",
                  "Celestia", "Fantom", "Mantle", "Blast", "Base", "Sonic", "Kaspa", "Render", "Ondo", "Venus", "Jupiter"}


def alias_ok(alias: str) -> bool:
    """Reject aliases that cannot be matched safely: shorter than 3 characters, purely numeric,
    or a single ordinary English word (Across, Render, Venus) unless allow-listed."""
    core = alias[1:] if alias.startswith("$") else alias
    if core.isdigit():
        return False
    if alias.startswith("$"):
        return len(core) >= 2          # the dollar sign disambiguates two-letter tickers ($OP, $AI)
    if len(core) < 3:
        return False
    if " " not in core and core in NAME_BLOCKLIST:
        return False
    return True


# Crypto proper names that the system dictionary lists as words but that never appear in ordinary prose
# with another meaning; these keep case-insensitive matching.
NAME_ALLOWLIST = {"Bitcoin", "Ethereum", "Ether", "Litecoin", "Dogecoin", "Solana", "Cardano", "Polkadot", "Chainlink",
                  "Uniswap", "Monero", "Tron", "Tether", "Binance", "Coinbase", "Kraken"}


def is_english_word(term: str) -> bool:
    return " " not in term and term not in NAME_ALLOWLIST and term.lower() in _ENGLISH


def build_dictionary(bases: list[str], coingecko_path: Path = COINGECKO) -> Dictionary:
    coins = json.loads(Path(coingecko_path).read_text())["coins"]
    by_symbol: dict[str, list[dict]] = {}
    for c in coins:
        by_symbol.setdefault(str(c["symbol"]).upper(), []).append(c)
    assets = {}
    for base in bases:
        if base in NON_CRYPTO_BASES:
            continue
        aliases = {f"${base}"}
        if base not in AMBIGUOUS_TICKERS:
            aliases.add(base)
        aliases.update(EXTRA_ALIASES.get(base, []))
        cands = sorted(by_symbol.get(base, []), key=lambda c: c.get("market_cap_rank") or 10**6)
        if cands:
            for alias in _name_aliases(cands[0]["name"]):
                if len(alias) >= 3 and alias.upper() != base:
                    aliases.add(alias)
        aliases = {a for a in aliases if alias_ok(a)}
        if aliases:
            assets[base] = sorted(aliases, key=lambda a: -len(a))
    return Dictionary(assets=assets)


def _pattern(term: str) -> re.Pattern:
    body = re.escape(term)
    if term.startswith("$"):
        return re.compile(rf"(?<![A-Za-z0-9_]){body}(?![A-Za-z0-9_])")
    # proper names that are also English words (Terra, Origin) match case-sensitively only
    flags = re.IGNORECASE if len(term) > 4 and not term.isupper() and not is_english_word(term) else 0
    return re.compile(rf"(?<![A-Za-z0-9_$]){body}(?![A-Za-z0-9_])", flags)


class Linker:
    def __init__(self, dictionary: Dictionary):
        self.dictionary = dictionary
        self.patterns = [(t, role, key, _pattern(t)) for t, role, key in dictionary.all_terms()]

    def mentions(self, text: str) -> dict[tuple[str, str], int]:
        counts: dict[tuple[str, str], int] = {}
        for term, role, key, pat in self.patterns:
            n = len(pat.findall(text))
            if n:
                counts[(role, key)] = counts.get((role, key), 0) + n
        return counts

    def link_assets(self, title: str, body: str) -> list[tuple[str, str]]:
        """[(base, salience)] with salience 'primary' or 'mentioned'."""
        in_title = {k for (r, k) in self.mentions(title or "") if r == "asset"}
        body_counts = {k: n for (r, k), n in self.mentions(body or "").items() if r == "asset"}
        out = []
        for base in sorted(in_title | set(body_counts)):
            primary = base in in_title or body_counts.get(base, 0) >= 2
            out.append((base, "primary" if primary else "mentioned"))
        return out
