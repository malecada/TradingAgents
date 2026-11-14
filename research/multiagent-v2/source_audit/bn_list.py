"""Binance announcement lists (title, release time) for the listing, news, delisting, maintenance and airdrop catalogs."""
import json, sys, time, urllib.request
UA = "Mozilla/5.0 (X11; Linux x86_64) research-probe/0.1"
BASE = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo={p}&pageSize=50&catalogId={c}"
def get(url):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:
            print("retry", repr(e)[:100], flush=True); time.sleep(5 * (attempt + 1))
    return None
out = open(sys.argv[1], "w")
for cid in [int(x) for x in sys.argv[2].split(",")]:
    page, n = 1, 0
    while True:
        r = get(BASE.format(p=page, c=cid))
        cats = ((r or {}).get("data") or {}).get("catalogs") or [{}]; arts = cats[0].get("articles") or []
        if not arts:
            break
        for a in arts:
            out.write(json.dumps({"catalog": cid, "id": a["id"], "code": a["code"], "title": a["title"], "release_ms": a["releaseDate"]}) + "\n")
        n += len(arts); page += 1
        time.sleep(1.2)
    print("catalog", cid, "rows", n, flush=True)
out.close()
print("done", flush=True)
