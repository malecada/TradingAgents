"""Multi-endpoint Ethereum JSON-RPC pool for the on-chain fetchers.

Motivation (2026-09-04): the single public dRPC endpoint hit its public
quota mid-run ("You reached Public endpoint rate limit") and every getLogs
returned "Can't route your request"; the nlst4 screening job died on
"rpc gave up".  This pool rotates over several free archive endpoints with
per-endpoint throttles, transient-error backoff, and a startup self-check
that disables any endpoint that silently returns EMPTY logs for pruned
history (rpc.flashbots.net did exactly that).

Semantics kept identical to predlab_nlst_dex_fetch.rpc so it can be dropped
in (``fetch.rpc = rpc_pool.rpc``): transient errors are retried, a
non-transient JSON-RPC error (range / size limit) is raised as RuntimeError
after every healthy endpoint refused it, so callers can bisect.
Thread-safe; ``workers`` parallel callers are fine.
"""
from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request

# name, url, min seconds between calls, serves historical eth_call/getBlock
ENDPOINTS: list[dict] = [
    {"name": "tenderly", "url": "https://mainnet.gateway.tenderly.co", "throttle": 0.6, "archive": True},
    {"name": "mevblocker", "url": "https://rpc.mevblocker.io", "throttle": 1.0, "archive": True},
    {"name": "drpc", "url": "https://eth.drpc.org", "throttle": 0.25, "archive": True},
    {"name": "nodereal", "url": "https://eth-mainnet.nodereal.io/v1/1659dfb40aa24bbb8153a677b98064d7", "throttle": 1.5, "archive": True},
    {"name": "onfinality", "url": "https://eth.api.onfinality.io/public", "throttle": 3.0, "archive": False},
    {"name": "0xrpc", "url": "https://0xrpc.io/eth", "throttle": 3.0, "archive": False},
]

# Self-check: USDC/WETH v2 pair Swap logs in blocks 16,800,000-16,809,999
# (2023-03) -> exactly 4,399 logs on a full archive node.
_CHECK_ADDR = "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc"
_CHECK_TOPIC = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
_CHECK_LO, _CHECK_HI, _CHECK_N = 16_800_000, 16_809_999, 4399

_ARCHIVE_METHODS = {"eth_call", "eth_getBlockByNumber", "eth_getBalance", "eth_getStorageAt"}
_PENALTY_MAX = 300.0


def _transient(msg: str) -> bool:
    m = msg.lower()
    return any(k in m for k in ("overloaded", "retry later", "rate limit", "too many",
                                "timeout", "temporarily", "unavailable", "quota",
                                "cu limit", "route", "upgrade to paid", "busy", "throttl"))


class Endpoint:
    def __init__(self, spec: dict):
        self.name, self.url = spec["name"], spec["url"]
        self.throttle, self.archive = float(spec["throttle"]), bool(spec["archive"])
        self.next_ok = 0.0          # earliest wall time for the next call
        self.penalty = 0.0          # current backoff after transient errors
        self.calls = self.errors = 0
        self.bytes = 0
        self.disabled: str | None = None
        self.inflight = 0

    def _post(self, method: str, params: list, timeout: float):
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
        req = urllib.request.Request(self.url, body, {"Content-Type": "application/json",
                                                       "User-Agent": "curl/8.5.0"})
        raw = urllib.request.urlopen(req, timeout=timeout).read()
        self.bytes += len(raw)
        return json.loads(raw)


class Pool:
    def __init__(self, specs: list[dict] | None = None, selfcheck: bool = True, log=print):
        self.eps = [Endpoint(s) for s in (specs or ENDPOINTS)]
        self.lock = threading.Lock()
        self.log = log
        self.t0 = time.time()
        if selfcheck:
            self.self_check()

    # ------------------------------------------------------------ scheduling
    def _pick(self, need_archive: bool, exclude: set) -> "Endpoint | None":
        """Least-loaded ready endpoint; None if every eligible one is throttled."""
        now = time.time()
        cands = [e for e in self.eps if e.disabled is None and e.name not in exclude
                 and (e.archive or not need_archive)]
        ready = [e for e in cands if e.next_ok <= now]
        if not ready:
            return None
        return min(ready, key=lambda e: (e.inflight, e.penalty, e.next_ok))

    def _wait_time(self, need_archive: bool, exclude: set) -> float:
        cands = [e for e in self.eps if e.disabled is None and e.name not in exclude
                 and (e.archive or not need_archive)]
        if not cands:
            return -1.0
        return max(0.0, min(e.next_ok for e in cands) - time.time())

    def rpc(self, method: str, params: list, tries: int = 12, timeout: float = 90.0):
        need_archive = method in _ARCHIVE_METHODS
        refused: set = set()      # endpoints that returned a non-transient error
        last_err = "no endpoint"
        for _attempt in range(tries):
            with self.lock:
                ep = self._pick(need_archive, refused)
                if ep is None:
                    wait = self._wait_time(need_archive, refused)
                    if wait < 0:
                        break     # every eligible endpoint refused this request
                else:
                    ep.inflight += 1
                    ep.next_ok = time.time() + ep.throttle + ep.penalty
            if ep is None:
                time.sleep(min(wait, 5.0) + 0.05)
                continue
            try:
                r = ep._post(method, params, timeout)
                if not isinstance(r, dict):
                    raise RuntimeError(f"malformed response {str(r)[:80]}")
                if "error" in r:
                    err = r["error"]
                    msg = str(err.get("message", err)) if isinstance(err, dict) else str(err)
                    if _transient(msg):
                        self._penalize(ep, msg)
                        continue
                    refused.add(ep.name)
                    last_err = f"{ep.name}: {msg}"
                    continue
                with self.lock:
                    ep.calls += 1
                    ep.penalty = max(0.0, ep.penalty * 0.5 - 0.1)
                return r["result"]
            except urllib.error.HTTPError as e:
                txt = e.read()[:300].decode(errors="replace")
                if 400 <= e.code < 500 and e.code != 429 and not _transient(txt):
                    refused.add(ep.name)
                    last_err = f"{ep.name}: HTTP {e.code} {txt[:120]}"
                    continue
                self._penalize(ep, f"HTTP {e.code} {txt[:80]}")
            except RuntimeError as e:
                self._penalize(ep, str(e))
            except Exception as e:  # noqa: BLE001 — transport: backoff + rotate
                self._penalize(ep, f"{type(e).__name__}: {str(e)[:80]}")
            finally:
                with self.lock:
                    ep.inflight -= 1
        raise RuntimeError(f"rpc gave up: {method} ({last_err})")

    def _penalize(self, ep: Endpoint, msg: str) -> None:
        with self.lock:
            ep.errors += 1
            ep.penalty = min(_PENALTY_MAX, max(2.0, ep.penalty * 2.0))
            ep.next_ok = time.time() + ep.penalty
        self.log(f"rpc_pool: {ep.name} backoff {ep.penalty:.0f}s ({msg[:90]})")

    # ------------------------------------------------------------ self-check
    def self_check(self) -> None:
        for ep in self.eps:
            try:
                r = ep._post("eth_getLogs", [{"address": _CHECK_ADDR, "topics": [_CHECK_TOPIC],
                                              "fromBlock": hex(_CHECK_LO), "toBlock": hex(_CHECK_HI)}], 90.0)
                n = len(r["result"]) if isinstance(r, dict) and "result" in r else -1
                if n != _CHECK_N:
                    ep.disabled = f"self-check n={n} (msg={str(r)[:80]})"
            except Exception as e:  # noqa: BLE001
                ep.disabled = f"self-check {type(e).__name__}: {str(e)[:80]}"
            self.log(f"rpc_pool: {ep.name:<11} {'OK' if ep.disabled is None else 'DISABLED ' + ep.disabled}")
        if all(e.disabled for e in self.eps):
            raise RuntimeError("rpc_pool: no endpoint passed the self-check")

    def stats(self) -> str:
        el = time.time() - self.t0
        parts = [f"{e.name}:{e.calls}/{e.errors}" + ("(off)" if e.disabled else "") for e in self.eps]
        tot = sum(e.calls for e in self.eps)
        return f"rpc_pool {tot} calls {tot / max(el, 1):.2f}/s {sum(e.bytes for e in self.eps) / 1e6:.0f}MB  " + " ".join(parts)


_default: "Pool | None" = None
_default_lock = threading.Lock()


def get_pool() -> Pool:
    global _default
    with _default_lock:
        if _default is None:
            _default = Pool()
        return _default


def rpc(method: str, params: list, tries: int = 12):
    """Drop-in for predlab_nlst_dex_fetch.rpc."""
    return get_pool().rpc(method, params, tries=tries)
