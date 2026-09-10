"""Independent-review regressions, exclusively synthetic temporary files."""
import json

import pytest

from .test_lifecycle import registered, start, complete
from tradingagents.research.admission import local_path
from tradingagents.research.verify import verify_run


def test_secret_paths_and_resolved_aliases_are_rejected(tmp_path):
    (tmp_path / "keys").mkdir()
    (tmp_path / "alias").symlink_to(tmp_path / "keys", target_is_directory=True)
    for name in ("keys/fake.txt", "alias/fake.txt", ".env", "apis/fake.txt", "hf_token.txt"):
        with pytest.raises(ValueError, match="secret"):
            local_path(tmp_path, name)


def test_mutated_own_claim_cannot_be_completed(registered):
    run = start(registered)
    path = run.directory / "claim.json"
    claim = json.loads(path.read_text())
    claim["windows"][0]["identity"] = "different-identity"
    path.write_text(json.dumps(claim))
    with pytest.raises(ValueError, match="claim.*changed"):
        complete(run)


@pytest.mark.parametrize("field", ["windows", "inputs", "design_source"])
def test_verifier_reconstructs_saved_claim_not_just_mutable_hash(registered, field):
    import hashlib
    run = start(registered)
    complete(run)
    path = run.directory / "claim.json"
    claim = json.loads(path.read_text())
    if field == "windows":
        claim["windows"][0]["identity"] = "different-identity"
    elif field == "inputs":
        claim["inputs"]["sample"]["path"] = "different.json"
    else:
        claim["design_source"] = "0" * 40
    path.write_text(json.dumps(claim))
    final = run.directory / "complete.json"
    receipt = json.loads(final.read_text())
    receipt["claim_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    final.write_text(json.dumps(receipt))
    with pytest.raises(ValueError):
        verify_run(run.directory)
