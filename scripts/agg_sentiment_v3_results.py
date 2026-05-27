import json
from pathlib import Path

ROOT = Path("data/sentiment_v3_ab")
rows = []
for v in ["A_pure_quant", "B_legacy_sentiment", "C_v3_features_only", "D_v3_full"]:
    for c in ["bitcoin", "ethereum"]:
        p = ROOT / v / f"backtest_{c}" / "summary.json"
        if not p.exists():
            continue
        j = json.loads(p.read_text())
        h = j[c]["hybrid"]
        b = j[c]["baseline"]
        rows.append((v, c, h["sharpe_ratio"], h["total_return"], h["max_drawdown"], h["n_trades"], b["sharpe_ratio"]))

print(f"{'variant':<22}{'coin':<10}{'hyb_SR':>8}{'hyb_ret':>10}{'hyb_DD':>9}{'trades':>8}{'base_SR':>10}")
print("-" * 80)
for r in rows:
    print(f"{r[0]:<22}{r[1]:<10}{r[2]:>8.2f}{r[3]*100:>9.1f}%{r[4]*100:>8.2f}%{r[5]:>8}{r[6]:>10.2f}")

print()
print("PORTFOLIO (avg BTC+ETH SR)")
sr_by_v = {v: {} for v in ["A_pure_quant", "B_legacy_sentiment", "C_v3_features_only", "D_v3_full"]}
for r in rows:
    sr_by_v[r[0]][r[1]] = r[2]
print(f"{'variant':<22}{'BTC SR':>10}{'ETH SR':>10}{'avg SR':>10}")
for v, d in sr_by_v.items():
    btc = d.get("bitcoin", float("nan"))
    eth = d.get("ethereum", float("nan"))
    avg = (btc + eth) / 2
    print(f"{v:<22}{btc:>10.2f}{eth:>10.2f}{avg:>10.2f}")

print()
print("DELTAS vs A_pure_quant (no-sentiment baseline)")
print(f"{'variant':<22}{'BTC dSR':>10}{'ETH dSR':>10}")
A = sr_by_v["A_pure_quant"]
for v in ["B_legacy_sentiment", "C_v3_features_only", "D_v3_full"]:
    d = sr_by_v[v]
    db = d.get("bitcoin", float("nan")) - A.get("bitcoin", float("nan"))
    de = d.get("ethereum", float("nan")) - A.get("ethereum", float("nan"))
    print(f"{v:<22}{db:>+10.2f}{de:>+10.2f}")

print()
print("DELTAS D vs B (v3 full vs legacy sentiment)")
B = sr_by_v["B_legacy_sentiment"]
D = sr_by_v["D_v3_full"]
print(f"BTC dSR(D-B): {D.get('bitcoin', float('nan')) - B.get('bitcoin', float('nan')):+.2f}")
print(f"ETH dSR(D-B): {D.get('ethereum', float('nan')) - B.get('ethereum', float('nan')):+.2f}")
print()
print("DELTAS D vs C (LLM analyst incremental)")
C = sr_by_v["C_v3_features_only"]
print(f"BTC dSR(D-C): {D.get('bitcoin', float('nan')) - C.get('bitcoin', float('nan')):+.2f}")
print(f"ETH dSR(D-C): {D.get('ethereum', float('nan')) - C.get('ethereum', float('nan')):+.2f}")
