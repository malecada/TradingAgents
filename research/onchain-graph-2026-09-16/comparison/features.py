"""Fixed PROTOCOL.md features from already admitted daily aggregates only."""
import numpy as np
import pandas as pd


MARKET = ["return_1", "return_7", "return_30", "volatility_7", "volatility_30",
          "log_quote_volume", "relative_quote_volume_7"]
ACTIVITY = [f"{kind}_{transform}" for kind in ("events", "nodes", "directed_pairs")
            for transform in ("log_count", "relative_7")]
MOTIFS = [f"{kind}_{transform}" for kind in ("stars", "dyads", "triangles")
          for transform in ("log_count", "per_event")] + ["nonzero_fraction"]
FEATURE_SETS = {"M0": MARKET, "M1": MARKET+ACTIVITY, "M2": MARKET+ACTIVITY+MOTIFS}
COUNTS = ["events", "nodes", "directed_pairs", "stars", "dyads", "triangles", "overlap_nodes", "nonzero_nodes"]


def _daily(frame, columns, *, graph):
    result = frame.copy()
    result["day"] = pd.to_datetime(result.day, utc=True, errors="raise")
    if result.day.isna().any() or result.day.duplicated().any() or (result.day != result.day.dt.floor("D")).any():
        raise ValueError("unique UTC midnight source days required")
    if result.empty:
        raise ValueError("nonempty source frame required")
    result["available_at"] = pd.to_datetime(result.available_at, utc=True, errors="raise")
    for column in columns:
        values = pd.to_numeric(result[column], errors="raise").to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError("supplied rows require finite values; omit unavailable source days")
        if graph:
            if (values < 0).any() or (values != np.floor(values)).any() or (values >= 2**53).any():
                raise ValueError("counts require exact nonnegative integers < 2**53")
        elif (values < 0).any() or (column in ("open", "close") and (values == 0).any()):
            raise ValueError("positive prices and nonnegative quote volume required")
        result[column] = values
    if graph:
        if ((result.nonzero_nodes > result.overlap_nodes) |
                (result.nodes > result.overlap_nodes) |
                (result.directed_pairs > result.events) |
                ((result.events == 0) & ((result.nodes != 0) | (result.directed_pairs != 0) |
                                         (result.stars != 0) | (result.dyads != 0) | (result.triangles != 0)))).any():
            raise ValueError("inconsistent count denominators")
    floor = result.day + (pd.Timedelta(days=2) if graph else pd.Timedelta(days=1, minutes=5))
    # Missing actual clocks remain missing, not replaced by an assumption.
    result["available_at"] = result.available_at.where(result.available_at >= floor, floor).where(result.available_at.notna())
    return result.set_index("day").sort_index()


def _window_clock(clock, width):
    # Integer nanoseconds avoid float precision loss in rolling timestamps.
    values = [pd.NaT] * len(clock)
    for end in range(width-1, len(clock)):
        window = clock.iloc[end-width+1:end+1]
        if window.notna().all():
            values[end] = window.max()
    return pd.Series(pd.to_datetime(values, utc=True), index=clock.index)


def build_panel(market, graph, *, start, end):
    """Build UTC decisions in [start,end), dense calendar and explicit warmups.

    Input graph counts must already pass source/role-conservation admission;
    aggregates alone cannot re-prove Local40 conservation. Labels use opening
    endpoints only. Feature data always joins exactly decision day minus two.
    """
    market = _daily(market, ["open", "close", "quote_volume"], graph=False)
    graph = _daily(graph, COUNTS, graph=True)
    start, end = pd.to_datetime([start, end], utc=True, errors="raise")
    if pd.isna(start) or pd.isna(end) or start >= end or start != start.floor("D") or end != end.floor("D"):
        raise ValueError("valid UTC midnight decision bounds required")
    calendar = pd.date_range(min(market.index.min(), graph.index.min(), start-pd.Timedelta(days=32)),
                             max(market.index.max(), graph.index.max(), end), freq="D")
    market, graph = market.reindex(calendar), graph.reindex(calendar)
    values, clocks = {}, {}

    def add(name, value, clock):
        values[name], clocks[name] = value, clock

    daily_return = np.log(market.close / market.close.shift(1))
    for days in (1, 7, 30):
        # All intervening closes are required even for endpoint return.
        complete = market.close.rolling(days+1, min_periods=days+1).count() == days+1
        add(f"return_{days}", np.log(market.close/market.close.shift(days)).where(complete),
            _window_clock(market.available_at, days+1))
    for days in (7, 30):
        add(f"volatility_{days}", daily_return.rolling(days, min_periods=days).std(ddof=0),
            _window_clock(market.available_at, days+1))
    add("log_quote_volume", np.log1p(market.quote_volume), market.available_at)
    add("relative_quote_volume_7", np.log((1+market.quote_volume)/(1+market.quote_volume.rolling(7, min_periods=7).mean())),
        _window_clock(market.available_at, 7))
    for kind in ("events", "nodes", "directed_pairs"):
        add(f"{kind}_log_count", np.log1p(graph[kind]), graph.available_at)
        add(f"{kind}_relative_7", np.log((1+graph[kind])/(1+graph[kind].rolling(7, min_periods=7).mean())),
            _window_clock(graph.available_at, 7))
    for kind in ("stars", "dyads", "triangles"):
        add(f"{kind}_log_count", np.log1p(graph[kind]), graph.available_at)
        add(f"{kind}_per_event", graph[kind]/(1+graph.events), graph.available_at)
    # Empty overlap has an undefined fraction and excludes the common row.
    add("nonzero_fraction", graph.nonzero_nodes/graph.overlap_nodes.replace(0, np.nan), graph.available_at)
    decisions = pd.date_range(start, end, freq="D", inclusive="left")
    source_days = decisions-pd.Timedelta(days=2)
    result = pd.DataFrame(dict(decision_at=decisions, label_start=decisions,
                              label_end=decisions+pd.Timedelta(days=1)))
    opens = market.open.reindex(decisions).to_numpy()
    next_opens = market.open.reindex(decisions+pd.Timedelta(days=1)).to_numpy()
    result["y"] = np.where(np.isfinite(opens) & np.isfinite(next_opens), (next_opens > opens).astype(float), np.nan)
    for name in FEATURE_SETS["M2"]:
        result[name] = values[name].reindex(source_days).to_numpy()
        result[name+"__available_at"] = clocks[name].reindex(source_days).array
    return result, {name: list(columns) for name, columns in FEATURE_SETS.items()}
