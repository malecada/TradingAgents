"""New fixed256KiB transport derived from frozen carry_capture323ea01a; no edits to ancestor."""
import http.client
import signal
import urllib.error
import urllib.parse
import urllib.request
MAX_BYTES=256*1024
TIMEOUT_SECONDS=20
DENIALS={403,418,429,451}
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _deadline(signum, frame):
    raise TimeoutError("20-second request wall deadline")


def public_get(url):
    """Main-thread Linux transport: no proxies, auth, retry or redirects.

    The alarm bounds connection and streamed-body reads together. Exact received
    prefix bytes are retained on timeout/oversize and never labeled a full body.
    """
    parsed=urllib.parse.urlsplit(url)
    if parsed.scheme!='https' or parsed.netloc!='eapi.binance.com' or parsed.path not in ('/eapi/v1/time','/eapi/v1/index','/eapi/v1/depth','/eapi/v1/mark') or parsed.fragment:
        raise ValueError('unregistered public endpoint')
    body, headers, status, error, complete = bytearray(), {}, None, None, False
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    if previous_timer != (0.0, 0.0):
        raise RuntimeError("capture requires no pre-existing real-time alarm")
    signal.signal(signal.SIGALRM, _deadline)
    try:
        signal.setitimer(signal.ITIMER_REAL, TIMEOUT_SECONDS)
        request = urllib.request.Request(url, headers={"Accept": "application/json",
                                         "User-Agent": "RegisteredOptionsEntryResearch/1.0"})
        try:
            response = opener.open(request, timeout=TIMEOUT_SECONDS)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            status = response.code
            headers = {name: response.headers[name] for name in ("Date", "Content-Type")
                       if name in response.headers}
            while True:
                chunk = response.read1(min(65536, MAX_BYTES - len(body) + 1))
                if not chunk:
                    remaining_length = getattr(response, "length", None)
                    if remaining_length is not None and remaining_length > 0:
                        error = "incomplete HTTP body: premature Content-Length EOF; retained received prefix"
                    else:
                        complete = True
                    break
                remaining = MAX_BYTES - len(body)
                body.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    error = "response exceeds256KiB; retained exact prefix only"
                    break
            if status != 200 and error is None:
                error = f"HTTP {status}"
    except http.client.IncompleteRead as exc:
        remaining = MAX_BYTES - len(body)
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
