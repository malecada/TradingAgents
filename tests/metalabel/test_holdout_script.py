import json
import pytest

import scripts.metalabel_holdout as h


def test_refuses_without_chosen_tau(tmp_path, monkeypatch):
    res = tmp_path / "dev_results.json"
    res.write_text(json.dumps({"chosen_tau": None}))
    monkeypatch.setattr(h, "DEV_RESULTS", res)
    with pytest.raises(RuntimeError, match="G2 did not pass"):
        h.main()


def test_refuses_when_already_spent(tmp_path, monkeypatch):
    res = tmp_path / "dev_results.json"
    res.write_text(json.dumps({"chosen_tau": 0.5}))
    flag = tmp_path / "holdout_spent.flag"
    flag.write_text("spent")
    monkeypatch.setattr(h, "DEV_RESULTS", res)
    monkeypatch.setattr(h, "SPENT_FLAG", flag)
    with pytest.raises(RuntimeError, match="already spent"):
        h.main()
