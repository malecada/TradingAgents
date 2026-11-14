"""Robust summary of pubtime_probe.json rows (ISO timestamps with and without fractional seconds or offsets)."""
import json, sys
import pandas as pd
d = json.load(open(sys.argv[1]))
r = pd.DataFrame(d["rows"])
print(r.columns.tolist(), len(r))
r["pub_ts"] = pd.to_datetime(r["pub"], utc=True, format="ISO8601", errors="coerce")
r["mod_ts"] = pd.to_datetime(r["mod"], utc=True, format="ISO8601", errors="coerce")
r["cap"] = pd.to_datetime(r["capture"], utc=True)
print("pub missing", int(r["pub"].isna().sum()), "pub unparsed", int((r["pub"].notna() & r["pub_ts"].isna()).sum()))
has_time = r["pub_ts"].notna() & ~((r["pub_ts"].dt.hour == 0) & (r["pub_ts"].dt.minute == 0) & (r["pub_ts"].dt.second == 0))
t = r[has_time].copy()
t["lag_h"] = (t["cap"] - t["pub_ts"]).dt.total_seconds() / 3600
t["mod_gap_h"] = (t["mod_ts"] - t["pub_ts"]).dt.total_seconds() / 3600
out = {"sampled": int(len(r)), "with_time_of_day": int(len(t)), "by_outlet_n": t["outlet"].value_counts().to_dict(),
       "hours_publication_to_capture": {str(q): round(float(t["lag_h"].quantile(q)), 2) for q in (0.1, 0.25, 0.5, 0.75, 0.9)},
       "by_outlet": {k: {str(q): round(float(g["lag_h"].quantile(q)), 2) for q in (0.25, 0.5, 0.75, 0.9)} for k, g in t.groupby("outlet")},
       "share_within_1h": round(float((t["lag_h"] <= 1).mean()), 3), "share_within_6h": round(float((t["lag_h"] <= 6).mean()), 3),
       "negative_lag": int((t["lag_h"] < -0.02).sum()), "min_lag_h": round(float(t["lag_h"].min()), 3),
       "modification_recorded": int(t["mod_gap_h"].notna().sum()),
       "share_modified_over_10min_after_publication": round(float((t["mod_gap_h"] > 1 / 6).mean()), 3),
       "share_capture_before_modification": round(float(((t["mod_ts"] - t["cap"]).dt.total_seconds() > 60).mean()), 3),
       "publication_hour_utc": {str(q): float(t["pub_ts"].dt.hour.quantile(q)) for q in (0.1, 0.25, 0.5, 0.75, 0.9)},
       "hours_capture_to_next_midnight": {str(q): round(float(((t["cap"].dt.normalize() + pd.Timedelta(days=1) - t["cap"]).dt.total_seconds() / 3600).quantile(q)), 2) for q in (0.25, 0.5, 0.75)}}
print(json.dumps(out, indent=1))
if len(sys.argv) > 2:
    json.dump(out, open(sys.argv[2], "w"), indent=1)
neg = t[t["lag_h"] < -0.02][["outlet", "capture", "pub", "lag_h"]]
print(neg.head(10).to_string())
