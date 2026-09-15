"""Future F1/F3 bounded public read transport; no run or acquisition entry point.

Derived from preserved q2_transport.py; its frozen bytes remain unchanged.
Per-request cap and finite deadline must be supplied by the admitted packet.
"""
import json
import http.client
import signal
import urllib.error
import urllib.parse
import urllib.request
TIMEOUT_SECONDS=30
DENIALS={403,418,429,451}
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _deadline(signum, frame):
    raise TimeoutError("30-second request wall deadline")


def public_post(url, payload, *, max_bytes):
    """Main-thread Linux transport: no proxies, auth, retry or redirects.

    The alarm bounds connection and streamed-body reads together. Exact received
    prefix bytes are retained on timeout/oversize and never labeled a full body.
    """
    if url != 'https://mainnet.base.org':
        raise ValueError('unregistered public endpoint')
    if type(max_bytes) is not int or max_bytes not in (16384,65536,262144):
        raise ValueError('registered scalar/code/header response cap required')
    if not isinstance(payload,dict):raise ValueError('single RPC only; no hidden batch')
    members = [payload]
    for member in members:
        if not isinstance(member, dict) or member.get('jsonrpc') != '2.0' or member.get('method') not in {'eth_chainId', 'eth_getBlockByNumber', 'eth_call', 'eth_getStorageAt', 'eth_getCode'}:
            raise ValueError('unregistered or non-read-only RPC method')
    ids = [m.get('id') for m in members]
    if any(not isinstance(i, str) for i in ids) or len(ids) != len(set(ids)):
        raise ValueError('unique string request IDs required')
    encoded = json.dumps(payload, separators=(',', ':'), allow_nan=False).encode()
    if len(encoded) > 32768:
        raise ValueError('request body too large')
    body, headers, status, error, complete = bytearray(), {}, None, None, False
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    if previous_timer != (0.0, 0.0):
        raise RuntimeError("capture requires no pre-existing real-time alarm")
    signal.signal(signal.SIGALRM, _deadline)
    try:
        signal.setitimer(signal.ITIMER_REAL, TIMEOUT_SECONDS)
        request = urllib.request.Request(url, data=encoded, method="POST",
            headers={"Accept": "application/json", "Content-Type": "application/json",
                     "User-Agent": "RegisteredDefiFinancialSource/1.0"})
        try:
            response = opener.open(request, timeout=TIMEOUT_SECONDS)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            status = response.code
            headers = {name: response.headers[name] for name in ("Date", "Content-Type", "Retry-After")
                       if name in response.headers}
            while True:
                chunk = response.read1(min(65536, max_bytes - len(body) + 1))
                if not chunk:
                    remaining_length = getattr(response, "length", None)
                    if remaining_length is not None and remaining_length > 0:
                        error = "incomplete HTTP body: premature Content-Length EOF; retained received prefix"
                    else:
                        complete = True
                    break
                remaining = max_bytes - len(body)
                body.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    error = "response exceeds registered byte cap; retained exact prefix only"
                    break
            if status != 200 and error is None:
                error = f"HTTP {status}"
    except http.client.IncompleteRead as exc:
        remaining = max_bytes - len(body)
        body.extend(exc.partial[:remaining])
        error = "IncompleteRead: incomplete HTTP body; retained received prefix"
    except (OSError, ValueError, http.client.HTTPException) as exc:
        error = type(exc).__name__ + ": " + str(exc)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        signal.setitimer(signal.ITIMER_REAL, *previous_timer)
    return {"body": bytes(body), "http_status": status, "headers": headers,
            "error": error, "body_complete": complete}
