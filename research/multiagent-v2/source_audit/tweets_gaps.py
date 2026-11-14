import sys
import pandas as pd
d = pd.read_parquet(sys.argv[1], columns=["created_at", "first_posted_at", "text", "channels", "user_name"])
d["ts"] = pd.to_datetime(d["created_at"], utc=True)
w = d[(d["ts"] >= "2023-01-01") & (d["ts"] < "2025-01-01")]
per_day = w.groupby(w["ts"].dt.normalize()).size().reindex(pd.date_range("2023-01-01", "2024-12-31", tz="UTC"), fill_value=0)
print("days", len(per_day), "days without a tweet", int((per_day == 0).sum()), "days under 10", int((per_day < 10).sum()), "median per day", per_day.median())
m = per_day.groupby(per_day.index.strftime("%Y-%m")).agg(["sum", lambda x: int((x == 0).sum())])
print(m.to_string())
print("first_posted_at present", round(float(d["first_posted_at"].notna().mean()), 3))
ch = w["channels"].explode().value_counts().head(12); print(ch.to_string())
print(w["user_name"].value_counts().head(15).to_string())
for t in w["text"].sample(12, random_state=3):
    print("-", str(t)[:200].replace("\n", " "))
