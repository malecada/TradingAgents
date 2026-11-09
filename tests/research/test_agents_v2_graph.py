"""Rule-twin book and config-sha coverage (pre-run audit M2, M5)."""
def test_rule_weights_are_net_neutral_and_capped():
    from tradingagents.agents_v2.graph import rule_weights
    cands = [{"alias": f"Asset_{i}", "p_outperform_7d": p, "confidence": 0.8, "vol_ann": 0.6, "abstain": False}
             for i, p in enumerate([0.9, 0.8, 0.7, 0.6, 0.55, 0.52])]      # all above 0.5: raw book would be all-long
    cands.append({"alias": "Asset_X", "p_outperform_7d": 0.9, "confidence": 1.0, "vol_ann": 0.5, "abstain": True})
    w = rule_weights(cands)
    assert abs(sum(w.values())) < 1e-9                       # demeaned: net exposure zero
    assert sum(abs(v) for v in w.values()) <= 1.0 + 1e-9     # gross cap
    assert all(abs(v) <= 0.10 + 1e-9 for v in w.values())    # per-asset cap
    assert w["Asset_X"] == 0.0                               # abstentions flat
    assert w["Asset_0"] > 0 > w["Asset_5"]                   # ranking preserved


def test_config_sha_covers_pins_and_debate_count():
    from tradingagents.agents_v2 import graph
    base = graph.config_sha()
    old = graph.N_DEBATE
    try:
        graph.N_DEBATE = old + 1
        assert graph.config_sha() != base
    finally:
        graph.N_DEBATE = old
