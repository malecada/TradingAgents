"""Independent corruption checks using disposable synthetic Git fixtures."""
import hashlib
import json

import pytest

from .test_lifecycle import registered, start, complete


@pytest.mark.parametrize("name", ["keys/fake.txt", "apis/fake.txt", ".env", "hf_token.txt"])
def test_admission_never_accepts_a_declared_secret_path(registered, name):
    from tradingagents.research.admission import local_path
    with pytest.raises(ValueError, match="secret"):
        local_path(registered[0], name)


def test_admission_rejects_in_root_secret_alias_before_reading(registered):
    from tradingagents.research.admission import local_path
    root = registered[0]
    (root / "keys").mkdir()
    (root / "alias").symlink_to(root / "keys", target_is_directory=True)
    with pytest.raises(ValueError, match="secret"):
        local_path(root, "alias/fake.txt")


def alter(claim, field):
    if field == "windows":
        claim["windows"][0]["identity"] = "different-dataset-identity"
    elif field == "inputs":
        claim["inputs"]["sample"]["path"] = "different-input.json"
    else:
        claim["program_id"] = "different-program"


@pytest.mark.parametrize("field", ["windows", "inputs", "program_id"])
def test_run_cannot_bless_a_changed_start_claim(registered, field):
    run = start(registered)
    path = run.directory / "claim.json"
    claim = json.loads(path.read_text())
    alter(claim, field)
    path.write_text(json.dumps(claim))
    with pytest.raises(ValueError, match="claim"):
        complete(run)
    assert not (run.directory / "complete.json").exists()


@pytest.mark.parametrize("field", ["windows", "inputs", "program_id"])
def test_verifier_binds_derived_claim_fields_to_committed_contract(registered, field):
    from tradingagents.research.verify import verify_run
    run = start(registered)
    complete(run)
    claim_path = run.directory / "claim.json"
    claim = json.loads(claim_path.read_text())
    alter(claim, field)
    raw = json.dumps(claim).encode()
    claim_path.write_bytes(raw)
    receipt_path = run.directory / "complete.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["claim_sha256"] = hashlib.sha256(raw).hexdigest()
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError):
        verify_run(run.directory)


@pytest.mark.parametrize("path", ["keys/fake.txt", ".env", "../outside", "/absolute"])
def test_verifier_rejects_untrusted_blob_paths_before_git(tmp_path, monkeypatch, path):
    from tradingagents.research.verify import _blob
    def forbidden(*args, **kwargs):
        raise AssertionError("git must not read this untrusted path")
    monkeypatch.setattr("tradingagents.research.verify.subprocess.check_output", forbidden)
    with pytest.raises(ValueError, match="path"):
        _blob(tmp_path, "0" * 40, path)


@pytest.mark.parametrize("commit", ["HEAD", "--sentinel-option", "a" * 39, None])
def test_verifier_rejects_non_commit_identity_before_git(tmp_path, monkeypatch, commit):
    from tradingagents.research.verify import _blob
    def forbidden(*args, **kwargs):
        raise AssertionError("git must not receive an untrusted revision argument")
    monkeypatch.setattr("tradingagents.research.verify.subprocess.check_output", forbidden)
    with pytest.raises(ValueError, match="commit identity"):
        _blob(tmp_path, commit, "registration.json")
