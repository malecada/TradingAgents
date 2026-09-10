"""Immutable, registered Binance USD-M hourly data recovery; no strategy metrics.

Run only after the transform-source commit: --execute --batch primary|extended.
All target ranges come from the committed/hash-pinned scope addendum. Daily bars
are primary, public symbol-klines API corroborates, and all source/original
overlaps must agree exactly. Failed intervals remain unavailable independently.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import io
import json
from pathlib import Path
import re
import sys
from threading import Lock
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
KEY = "audit_data_recovery_2026_09_10"
SYMBOLS = ["TRXUSDT", "FILUSDT", "LTCUSDT"]
IDENTITY_QUARANTINE = {"BNXUSDT", "ICPUSDT"}
GAPS = [("2022-02-26", "2022-03-01"), ("2022-04-01", "2022-04-03")]
FIELDS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
          "quote_volume", "n_trades", "taker_buy_base", "taker_buy_quote_volume", "ignore"]
OLD_COLUMNS = ["open", "high", "low", "close", "volume", "quote_volume", "taker_buy_quote_volume"]
ARCHIVE = "https://data.binance.vision/data/futures/um"
HOUR = pd.Timedelta(hours=1)
DAY = pd.Timedelta(days=1)


class RecoveryError(ValueError):
    pass


def utc(value):
    stamp = pd.Timestamp(value)
    return stamp.tz_localize("UTC") if stamp.tz is None else stamp.tz_convert("UTC")


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    with Path(path).open("x") as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write("\n")


def target_clock(symbol, ranges=None):
    ranges = ranges if ranges is not None else [{"start": a, "end_exclusive": b} for a, b in GAPS]
    values = [pd.date_range(utc(r["start"]), utc(r["end_exclusive"]), freq="1h", inclusive="left") for r in ranges]
    return pd.DatetimeIndex(np.concatenate([v.to_numpy() for v in values]), name="ts")


def request_plan(scope=None):
    scope = scope if scope is not None else [{"symbol": s, "ranges": [{"start": a, "end_exclusive": b} for a,b in GAPS]} for s in SYMBOLS]
    plan = {}
    def add(symbol, kind, url, start, end):
        key = hashlib.sha256(url.encode()).hexdigest()[:20]
        plan[key] = {"id": key, "symbol": symbol, "kind": kind, "url": url,
                     "start": start.isoformat(), "end_exclusive": end.isoformat()}
    for item in scope:
        symbol = item["symbol"]
        if symbol in IDENTITY_QUARANTINE:
            # Same ticker was reused after settlement. An alias request requires
            # its own registered mapping; even 2022 API queries cannot use new BNX.
            continue
        for r in item["ranges"]:
            start, end = utc(r["start"]), utc(r["end_exclusive"])
            if start >= end or start < utc("2021-01-01") or end > utc("2025-04-01"):
                raise RecoveryError("range outside registered development recovery")
            for month in pd.period_range(start.tz_localize(None).to_period("M"), (end-HOUR).tz_localize(None).to_period("M"), freq="M"):
                lo, hi = utc(month.to_timestamp()), utc((month+1).to_timestamp())
                url = f"{ARCHIVE}/monthly/klines/{symbol}/1h/{symbol}-1h-{month}.zip"
                add(symbol, "monthly_zip", url, lo, hi)
                add(symbol, "checksum", url+".CHECKSUM", lo, hi)
            lo, hi = start.floor("D")-DAY, end.ceil("D")+DAY
            for day in pd.date_range(lo, hi, freq="1D", inclusive="left"):
                url = f"{ARCHIVE}/daily/klines/{symbol}/1h/{symbol}-1h-{day.date()}.zip"
                add(symbol, "daily_zip", url, day, day+DAY)
                add(symbol, "checksum", url+".CHECKSUM", day, day+DAY)
            cursor = lo
            while cursor < hi:
                stop = min(cursor + 500*HOUR, hi)
                params = {"symbol": symbol, "interval": "1h", "startTime": int(cursor.timestamp()*1000),
                          "endTime": int(stop.timestamp()*1000)-1, "limit": 500}
                add(symbol, "api", "https://fapi.binance.com/fapi/v1/klines?"+urllib.parse.urlencode(params), cursor, stop)
                cursor = stop
    return list(plan.values())


def verify_checksum(raw, checksum, filename):
    parts = checksum.decode("ascii").strip().split()
    if len(parts) != 2 or parts[1].lstrip("*") != filename:
        raise RecoveryError("checksum filename mismatch")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]) or hashlib.sha256(raw).hexdigest() != parts[0].lower():
        raise RecoveryError("provider checksum mismatch")


def parse_rows(values):
    if not values or any(len(row) != 12 for row in values):
        raise RecoveryError("empty or invalid 12-field kline schema")
    df = pd.DataFrame(values, columns=FIELDS)
    try:
        for c in FIELDS:
            df[c] = pd.to_numeric(df[c], errors="raise")
    except (TypeError, ValueError) as exc:
        raise RecoveryError("non-numeric bar field") from exc
    if not np.isfinite(df.to_numpy(float)).all():
        raise RecoveryError("nonfinite bar field")
    ts = df.open_time.to_numpy(float)
    if ((ts < 1e12) | (ts >= 1e13) | (ts % 3600000 != 0)).any():
        raise RecoveryError("expected millisecond hourly open-time clock")
    if not (df.close_time == df.open_time + 3599999).all():
        raise RecoveryError("invalid bar close-time clock")
    if ((df[["open","high","low","close"]] <= 0).any().any() or
            (df.low > df[["open","close"]].min(axis=1)).any() or
            (df.high < df[["open","close"]].max(axis=1)).any()):
        raise RecoveryError("invalid positive OHLC bounds")
    if (df[["volume","quote_volume","n_trades","taker_buy_base","taker_buy_quote_volume"]] < 0).any().any() or (df.n_trades % 1 != 0).any():
        raise RecoveryError("invalid nonnegative volume/trade count")
    index = pd.DatetimeIndex(pd.to_datetime(df.open_time, unit="ms", utc=True), name="ts")
    if not index.is_unique or not index.is_monotonic_increasing:
        raise RecoveryError("duplicate or unsorted observed timestamps")
    df.index = index
    for c in ["open_time","close_time","n_trades"]:
        df[c] = df[c].astype("int64")
    for c in set(FIELDS)-{"open_time","close_time","n_trades"}:
        df[c] = df[c].astype("float64")
    return df


def parse_zip(raw):
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            if len(archive.namelist()) != 1 or not archive.namelist()[0].lower().endswith('.csv'):
                raise RecoveryError("corrupt archive/CSV: expected exactly one CSV")
            text = archive.read(archive.namelist()[0])
        table = pd.read_csv(io.BytesIO(text), header=None, dtype=str, keep_default_na=False)
        if str(table.iloc[0,0]).lower() == "open_time":
            table = table.iloc[1:]
        return parse_rows(table.values.tolist())
    except (zipfile.BadZipFile, pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeError, IndexError, RuntimeError) as exc:
        raise RecoveryError("corrupt archive/CSV") from exc


def compare_overlap(left, right, left_name, right_name):
    common = left.index.intersection(right.index)
    columns = [c for c in left.columns if c in right.columns]
    a, b = left.loc[common, columns], right.loc[common, columns]
    different = ~(a.to_numpy() == b.to_numpy())
    if different.any():
        i,j = np.argwhere(different)[0]
        raise RecoveryError(f"overlap conflict {left_name}/{right_name}: {common[i]} {columns[j]} {a.iloc[i,j]!r} != {b.iloc[i,j]!r}; {int(different.sum())} differing values")
    return {"left": left_name, "right": right_name, "rows": len(common), "fields": columns, "conflicts": 0}


def insert_verified(old, recovered, target):
    if not old.index.is_unique or not old.index.is_monotonic_increasing or list(old.columns) != OLD_COLUMNS:
        raise RecoveryError("original frame schema/clock cannot be preserved")
    if len(old.index.intersection(target)):
        raise RecoveryError("requested target already present in original")
    if len(recovered.index.difference(target)):
        raise RecoveryError("unexpected unregistered insertion timestamp")
    if len(target.difference(recovered.index)) or not recovered.index.is_unique:
        raise RecoveryError("incomplete target coverage")
    additions = recovered[OLD_COLUMNS].astype(old.dtypes.to_dict())
    merged = pd.concat([old, additions]).sort_index()
    if not merged.loc[old.index].equals(old):
        raise RecoveryError("original row values changed during insertion")
    return merged, {"original_rows": len(old), "inserted_rows": len(additions),
                    "snapshot_rows": len(merged), "original_rows_unchanged": True}


class ReceiptStore:
    def __init__(self, root, budget=250000000):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=False)
        self.budget, self.used = budget, 0
        self.lock = Lock()

    def save(self, name, url, body, status, headers, *, accounted=False, error=None):
        path = self.root/f"{name}.bin"
        with self.lock:
            if path.exists() or path.with_suffix(".json").exists():
                raise FileExistsError(path)
            if not accounted:
                if self.used + len(body) > self.budget:
                    raise RecoveryError("aggregate download budget exhausted")
                self.used += len(body)
            with path.open("xb") as f:
                f.write(body)
            receipt = {"url": url, "status": status, "retrieved_utc": datetime.now(timezone.utc).isoformat(),
                       "headers": dict(headers), "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                       "body_file": path.name, "error": error}
            write_json(path.with_suffix(".json"), receipt)
            return receipt

    def read_response(self, response):
        body = bytearray()
        length = response.headers.get("Content-Length")
        declared = int(length) if length and length.isdigit() else None
        error = None
        try:
            while declared is None or len(body) < declared:
                with self.lock:
                    remaining = self.budget-self.used
                    if remaining <= 0:
                        raise RecoveryError("aggregate download budget exhausted")
                    chunk = response.read(min(65536, remaining))
                    self.used += len(chunk)
                if not chunk:
                    break
                body.extend(chunk)
            if declared is not None and len(body) != declared:
                raise RecoveryError("truncated response body")
        except (OSError, RecoveryError) as exc:
            error = str(exc)
        return bytes(body), error


def fetch_receipt(request, store, limits):
    for attempt in range(1, limits["max_attempts_per_request"]+1):
        status, headers, body, error = None, {}, b"", None
        try:
            query = urllib.request.Request(request["url"], headers={"User-Agent":"TradingAgents-data-recovery/2026-09-10"})
            try:
                response = urllib.request.urlopen(query, timeout=limits["timeout_seconds"])
            except urllib.error.HTTPError as exc:
                response = exc
            with response:
                status, headers = response.status, dict(response.headers)
                body, error = store.read_response(response)
        except (OSError, urllib.error.URLError, RecoveryError) as exc:
            error = str(exc)
        receipt = store.save(f"{request['id']}-attempt{attempt}", request["url"], body, status, headers, accounted=True, error=error)
        if status == 200 and error is None:
            return receipt
        if attempt == limits["max_attempts_per_request"] or (status is not None and status not in [408,429] and status < 500):
            return receipt
        retry = {k.lower():v for k,v in headers.items()}.get("retry-after", "2")
        try:
            delay = float(retry)
        except ValueError:
            try:
                delay = max(0, (parsedate_to_datetime(retry)-datetime.now(timezone.utc)).total_seconds())
            except (ValueError, TypeError, OverflowError):
                return receipt  # malformed provider backoff cannot justify an early retry
        if delay > limits["timeout_seconds"]:
            # Respect the provider's backoff by making no premature retry.
            return receipt
        time.sleep(max(0, delay))
    raise AssertionError("unreachable")


def load_sources(plan, receipts, store):
    frames, errors = {}, {}
    by_url = {r["url"]: r for r in plan}
    for req in plan:
        if req["kind"] == "checksum":
            continue
        try:
            receipt = receipts[req["id"]]
            if receipt["status"] != 200 or receipt["error"]:
                raise RecoveryError(f"source request failed: {receipt['status']} {receipt['error']}")
            path = store.root/receipt["body_file"]
            if sha256(path) != receipt["sha256"]:
                raise RecoveryError("raw receipt body changed")
            body = path.read_bytes()
            if req["kind"] == "api":
                frame = parse_rows(json.loads(body))
            else:
                checksum_req = by_url[req["url"]+".CHECKSUM"]
                check = receipts[checksum_req["id"]]
                if check["status"] != 200 or check["error"]:
                    raise RecoveryError("checksum request unavailable")
                check_path = store.root/check["body_file"]
                if sha256(check_path) != check["sha256"]:
                    raise RecoveryError("checksum receipt changed")
                verify_checksum(body, check_path.read_bytes(), Path(req["url"]).name)
                frame = parse_zip(body)
            allowed = pd.date_range(utc(req["start"]), utc(req["end_exclusive"]), freq="1h", inclusive="left")
            if len(frame.index.difference(allowed)):
                raise RecoveryError("source returned timestamps outside requested window")
            if req["kind"] == "daily_zip" and not frame.index.equals(allowed.rename("ts")):
                raise RecoveryError("daily archive incomplete target coverage")
            frames[req["id"]] = frame
        except (RecoveryError, OSError, ValueError, KeyError, TypeError, IndexError) as exc:
            errors[req["id"]] = str(exc)
    return frames, errors


def join_consistent(parts, label):
    if not parts:
        raise RecoveryError(f"no valid {label} source")
    combined = parts[0]
    for part in parts[1:]:
        compare_overlap(combined, part, label, label)
        combined = pd.concat([combined, part.loc[part.index.difference(combined.index)]]).sort_index()
    return combined


def recover_symbol(item, old, plan, frames, errors):
    current, outcomes, comparisons, additions = old.copy(), [], [], []
    for r in item["ranges"]:
        target = target_clock(item["symbol"], [r])
        lo, hi = utc(r["start"]).floor("D")-DAY, utc(r["end_exclusive"]).ceil("D")+DAY
        relevant = [p for p in plan if p["symbol"] == item["symbol"] and p["kind"] != "checksum" and
                    utc(p["start"]) < hi and utc(p["end_exclusive"]) > lo]
        outcome = {**r, "expected_hours": len(target), "inserted_hours": 0, "status": "unavailable"}
        try:
            if item["symbol"] in IDENTITY_QUARANTINE:
                raise RecoveryError("identity_quarantine: settled original/new contract ticker reuse; alias mapping not registered")
            missing = [p["url"]+": "+errors.get(p["id"],"missing receipt") for p in relevant if p["id"] not in frames]
            if missing:
                raise RecoveryError("required source unavailable: " + " | ".join(missing))
            groups = {kind: join_consistent([frames[p["id"]] for p in relevant if p["kind"] == kind], kind)
                      for kind in ["daily_zip","monthly_zip","api"]}
            checks = []
            for kind, frame in groups.items():
                checks.append(compare_overlap(old, frame, "original", kind))
            for a,b in [("daily_zip","monthly_zip"),("daily_zip","api"),("monthly_zip","api")]:
                checks.append(compare_overlap(groups[a],groups[b],a,b))
            if any(check["rows"] == 0 for check in checks):
                raise RecoveryError("required overlap comparison has no observations")
            for kind in ["daily_zip","api"]:
                if len(target.difference(groups[kind].index)):
                    raise RecoveryError(f"incomplete target coverage: {kind}")
            recovered = groups["daily_zip"].loc[target]
            current, insertion = insert_verified(current, recovered, target)
            outcome.update(status="verified", inserted_hours=insertion["inserted_rows"],
                           monthly_target_hours=len(target.intersection(groups["monthly_zip"].index)), comparisons=checks)
            comparisons.extend(checks)
            additions.append(recovered)
        except RecoveryError as exc:
            outcome["reason"] = str(exc)
        outcomes.append(outcome)
    return current, outcomes, comparisons, pd.concat(additions).sort_index() if additions else None


def read_original(source, expected_hash):
    if sha256(source) != expected_hash:
        raise RecoveryError(f"original source checksum mismatch: {source}")
    # Push the date predicate into Parquet: post-cutoff price rows are never loaded.
    return pd.read_parquet(source, filters=[('ts','>=',utc('2020-06-01')),
                                            ('ts','<',utc('2025-04-01'))])


def write_symbol_artifacts(output, symbol, source, expected_hash, old, merged, verified):
    hashes = {}
    for filename, frame in [(f'{symbol}.parquet', merged), (f'{symbol}-insertions.parquet', verified)]:
        if sha256(source) != expected_hash:
            raise RecoveryError(f"original source checksum mismatch before artifact write: {source}")
        path = output/filename
        if path.exists():
            raise FileExistsError(path)
        frame.attrs = {}
        frame.to_parquet(path)
        hashes[path.name] = sha256(path)
    if not pd.read_parquet(output/f'{symbol}.parquet').loc[old.index].equals(old):
        raise RecoveryError("serialized snapshot changed original development rows")
    return hashes


def run(batch):
    from tradingagents.predlab import registry
    gate = registry.get_experiment(KEY)
    provenance = registry.preflight(KEY, ("2021-01-01","2025-03-31"))
    spec = gate["timestamp_inventory_scope_addendum"]
    scope_path = ROOT/spec["path"]
    if sha256(scope_path) != spec["sha256"]:
        raise RecoveryError("scope addendum checksum mismatch")
    scope = json.loads(scope_path.read_text())["scope"]
    scope = [r for r in scope if (r["symbol"] in SYMBOLS) == (batch == "primary")]
    output = ROOT/gate["output_root"]/f"hourly-{batch}"
    output.mkdir(parents=True, exist_ok=False)
    write_json(output/"started.json", {"registered_gate":gate, "scope":scope, **provenance,
                                      "started_utc":datetime.now(timezone.utc).isoformat()})
    namespace = ROOT/gate["output_root"]
    prior_downloads = sum(p.stat().st_size for p in namespace.glob("hourly-*/raw/*.bin"))
    documentary_bytes = sum(p.stat().st_size for p in namespace.rglob('*') if p.is_file()
                            and not p.relative_to(namespace).parts[0].startswith('hourly-'))
    documentary_reserve = max(5000000, documentary_bytes)
    store = ReceiptStore(output/"raw", budget=gate["fetch_limits"]["max_download_bytes"]-prior_downloads-documentary_reserve)
    plan = request_plan(scope)
    write_json(output/"request-plan.json", plan)
    receipts = {}
    with ThreadPoolExecutor(max_workers=gate["fetch_limits"]["max_parallel_requests"]) as pool:
        pending = {pool.submit(fetch_receipt, r, store, gate["fetch_limits"]):r for r in plan}
        for i,future in enumerate(as_completed(pending),1):
            req = pending[future]
            receipts[req["id"]] = future.result()
            if i % 25 == 0:
                print(f"Raw receipts: {i}/{len(plan)}; {store.used} bytes", flush=True)
    frames, errors = load_sources(plan, receipts, store)
    outcomes, old_hashes, output_hashes = [], {}, {}
    for item in scope:
        source = Path(item["source_path"]).resolve()
        try:
            if not any(source.is_relative_to(Path(p).resolve()) for p in gate["source_roots"]):
                raise RecoveryError("unregistered original source root")
            old = read_original(source, item["source_sha256"])
            old_hashes[str(source)] = item["source_sha256"]
            merged, ranges, comparisons, verified = recover_symbol(item, old, plan, frames, errors)
            summary = {"symbol":item["symbol"], "ranges":ranges, "original_development_rows":len(old),
                       "inserted_hours":sum(r["inserted_hours"] for r in ranges),
                       "all_ranges_verified":all(r["status"]=="verified" for r in ranges)}
            if verified is not None:
                hashes = write_symbol_artifacts(output,item['symbol'],source,item['source_sha256'],old,merged,verified)
                output_hashes.update(hashes)
                summary.update(snapshot_rows=len(merged), original_development_rows_unchanged=True)
        except (RecoveryError, OSError, ValueError) as exc:
            summary = {'symbol':item['symbol'], 'inserted_hours':0, 'all_ranges_verified':False,
                       'ranges':[{**r,'status':'unavailable','inserted_hours':0,
                                  'expected_hours':len(target_clock(item['symbol'],[r])),
                                  'reason':str(exc)} for r in item['ranges']]}
        outcomes.append(summary)
        print(f"{item['symbol']}: {summary['inserted_hours']} verified insertions", flush=True)
    if any(sha256(p)!=h for p,h in old_hashes.items()):
        raise RecoveryError("original source changed during recovery")
    if registry.preflight(KEY,("2021-01-01","2025-03-31")) != provenance:
        raise RecoveryError("transform/gate/provenance changed during recovery")
    write_json(output/"result.json", {**provenance,"type":"data_recovery_only","batch":batch,
        "strategy_metrics_computed":False,"strategy_replay_permitted":False,
        "source_hierarchy":"verified daily primary; symbol-klines API corroboration; all original/monthly/daily/API overlaps exact",
        "overlap_policy":"exact equality; conflicts quarantined without tolerance or overwriting",
        "snapshot_window":["2020-06-01T00:00:00Z","2025-04-01T00:00:00Z"],
        "original_preservation":"original files unchanged; all original rows within snapshot window preserved exactly; outside-window prices not materialized",
        "original_sha256":old_hashes,"scope_sha256":spec["sha256"],"output_sha256":output_hashes,
        "download_bytes":store.used,"prior_batch_download_bytes":prior_downloads,
        "documentary_bytes_at_start":documentary_bytes,"documentary_budget_reserved":documentary_reserve,
        "raw_receipt_sha256":{p.name:sha256(p) for p in sorted(store.root.iterdir())},
        "request_count":len(plan),"request_errors":errors,"symbols":outcomes,
        "requested_hours":sum(len(target_clock(x['symbol'],x['ranges'])) for x in scope),
        "inserted_hours":sum(x['inserted_hours'] for x in outcomes),
        "all_ranges_verified":all(x['all_ranges_verified'] for x in outcomes),
        "completed_utc":datetime.now(timezone.utc).isoformat()})
    return output/"result.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--batch", choices=["primary","extended"], default="primary")
    args = parser.parse_args()
    if not args.execute:
        parser.error("--execute required after transform source is committed")
    print(run(args.batch))


if __name__ == "__main__":
    main()
