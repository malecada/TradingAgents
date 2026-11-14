"""Unique article-like URLs first seen by the Wayback Machine in one week (2023-03-13..19) per candidate outlet."""
import json, sys, time, re, urllib.request, urllib.parse, collections
UA = "Mozilla/5.0 (X11; Linux x86_64) research-probe/0.1"
CDX = "http://web.archive.org/cdx/search/cdx?"
def cdx(params):
    url = CDX + urllib.parse.urlencode(params, doseq=True)
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                b = r.read()
                return json.loads(b) if b.strip() else []
        except Exception as e:
            print("  retry", repr(e)[:100], flush=True); time.sleep(15 * (attempt + 1))
    return None
SLUG = re.compile(r"/[a-z0-9]+(?:-[a-z0-9]+){3,}/?$")
out = {}
for dom in sys.argv[2:]:
    rows = cdx({"url": dom + "/*", "from": "20230313", "to": "20230319", "output": "json", "fl": "original,timestamp", "filter": ["statuscode:200", "mimetype:text/html"], "collapse": "urlkey", "limit": 20000})
    if rows is None:
        print(dom, "error", flush=True); out[dom] = None; continue
    rows = rows[1:]
    arts = [r for r in rows if SLUG.search(r[0].split("?")[0])]
    out[dom] = {"html_urls_captured": len(rows), "article_like": len(arts), "sample": [a[0] for a in arts[:3]]}
    print(dom, len(rows), len(arts), [a[0][-70:] for a in arts[:2]], flush=True)
    time.sleep(3)
json.dump(out, open(sys.argv[1], "w"), indent=1)
print("done", flush=True)
