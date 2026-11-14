"""Wayback captures of outlet RSS feeds in one month (2023-03): captures per day and distinct contents."""
import json, sys, time, urllib.request, urllib.parse, collections
UA = "Mozilla/5.0 (X11; Linux x86_64) research-probe/0.1"
CDX = "http://web.archive.org/cdx/search/cdx?"
def cdx(params):
    url = CDX + urllib.parse.urlencode(params, doseq=True)
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                b = r.read()
                return json.loads(b) if b.strip() else []
        except Exception as e:
            print("  retry", repr(e)[:100], flush=True); time.sleep(10 * (attempt + 1))
    return None
feeds = sys.argv[2:]
out = {}
for f in feeds:
    rows = cdx({"url": f, "from": "20230301", "to": "20230331", "output": "json", "fl": "timestamp,statuscode,digest,mimetype", "filter": "statuscode:200", "limit": 5000})
    if rows is None:
        print(f, "error"); out[f] = None; continue
    rows = rows[1:]
    days = collections.Counter(r[0][:8] for r in rows)
    dig = len({r[2] for r in rows})
    per_day = sorted(days.values())
    out[f] = {"captures": len(rows), "distinct_contents": dig, "days_with_capture": len(days), "median_per_day": per_day[len(per_day)//2] if per_day else 0}
    print(f, out[f], flush=True)
    time.sleep(2.5)
json.dump(out, open(sys.argv[1], "w"), indent=1)
