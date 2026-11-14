import json, sys, time, datetime, urllib.request
UA = "Mozilla/5.0 (X11; Linux x86_64) research-probe/0.1"
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())
def ts(ms): return datetime.datetime.fromtimestamp(ms/1000, datetime.UTC).strftime("%Y-%m-%d %H:%M")
base = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo={p}&pageSize={n}"
d = get(base.format(p=1, n=1))
out = {}
for c in d["data"]["catalogs"]:
    print(c["catalogId"], c["catalogName"], c.get("total"))
    out[c["catalogId"]] = {"name": c["catalogName"], "total": c.get("total")}
time.sleep(1.5)
for cid in (48, 161, 49):
    tot = out.get(cid, {}).get("total") or 0
    for page in (max(1, tot // 50 - 0), max(1, tot // 50 // 2), max(1, tot // 50 * 3 // 4)):
        try:
            r = get(base.format(p=page, n=50) + f"&catalogId={cid}")
            arts = r["data"]["catalogs"][0]["articles"]
            if arts:
                print(cid, "page", page, len(arts), ts(arts[-1]["releaseDate"]), "..", ts(arts[0]["releaseDate"]), "|", arts[0]["title"][:80])
            else:
                print(cid, "page", page, "empty")
        except Exception as e:
            print(cid, "page", page, "error", repr(e)[:120])
        time.sleep(1.5)
json.dump(out, open("/tmp/srcaudit/bn_catalogs.json", "w"))
