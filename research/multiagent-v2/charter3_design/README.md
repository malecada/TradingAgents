# Charter 3, stage V0: design evidence

Evidence behind §3.1, §4.1 and Appendix B of the Charter 3 draft
(`docs/superpowers/specs/2026-11-13-llm-v2-charter3-volatility-charter.md`).

Everything here was computed on decision-time regressors of the panel and on synthetic targets. No bar after a
decision was read, no text feature was joined with a realised variance of the window and no gate statistic was
computed on real outcomes.

| File | Content |
|---|---|
| `check1_control_designs.py`, `check1.jsonl`, `check1.log` | Five ways of removing the controls, flexible fits cross-fitted over blocks of weeks. 300 seeds in four cells. |
| `check2_past_only.py`, `check2.jsonl`, `check2.log` | Four ways with fits on earlier weeks only. Same seeds and cells. The variant `gbm_past_feat_quad_target` is the registered design. |
| `compare.py` | The nine variants side by side on the common seeds. |
| `check3_persistence_scale.py`, `check3.json` | How the simulated persistence shows in the autocorrelation of the target residual, the quantity the registered run reports. |
| `decision_time_facts.py`, `decision_time_facts.json` | Coverage of the features and the share of their rank variance that the controls leave (charter §3.1). |
| `tables.py`, `tables.md` | The tables of Appendix B, built from the stored draws. |

The draws of the two full designs are one level up: `charter3_null_gate.jsonl` and `charter3_null_gate_power.jsonl`
for the registered design, `charter3_null_gate_first_design.jsonl` and `charter3_null_gate_first_design_power.jsonl`
for the first design. They are written by `scripts/reader_charter3_null_gate.py real`.

To reproduce, build the decision-time panel once and pass it to the scripts:

    PYTHONPATH=.:scripts python scripts/reader_charter3_null_gate.py panel /tmp/c3/panel.parquet
    PYTHONPATH=.:scripts python research/multiagent-v2/charter3_design/check2_past_only.py /tmp/c3/panel.parquet 0 300 out.jsonl
    PYTHONPATH=.:scripts python research/multiagent-v2/charter3_design/tables.py

The seeds of check 1 and check 2 (0 to 299) are the first 300 seeds of the 2,000-draw files. The pass rates of
the registered design on the other 1,700 seeds are stated in Appendix B.3 of the charter.
