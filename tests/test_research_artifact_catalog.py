"""Synthetic corruption and containment checks; no retained data are opened."""
import hashlib
import json

import pytest

from scripts.check_research_artifacts import check, inspect_file


def test_catalogue_checks_manifest_members_and_detects_corruption(tmp_path):
    member = tmp_path / "raw.bin"
    member.write_bytes(b"retained raw bytes")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"files": {"raw.bin": hashlib.sha256(member.read_bytes()).hexdigest()}}))
    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps({"schema_version": 1, "artifacts": [{
        "id": "capture", "path": "manifest.json", "sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "manifest_map": "files", "git_tracked": False}]}))
    assert check(tmp_path, catalog)["ok"]
    member.write_bytes(b"changed")
    result = check(tmp_path, catalog)
    assert not result["ok"]
    assert [item["path"] for item in result["failures"]] == ["raw.bin"]


@pytest.mark.parametrize("path", ["../outside", "/etc/hosts", "keys/key", "apis/token", ".env", "hf_token.txt"])
def test_catalogue_rejects_unsafe_paths_before_reading(tmp_path, path):
    with pytest.raises(ValueError):
        inspect_file(tmp_path, {"path": path, "sha256": "0" * 64})


def test_catalogue_rejects_escaping_symlink(tmp_path):
    (tmp_path / "escape").symlink_to(tmp_path.parent)
    with pytest.raises(ValueError):
        inspect_file(tmp_path, {"path": "escape/file", "sha256": "0" * 64})


def test_catalogue_rejects_in_root_alias_to_secret(tmp_path):
    (tmp_path / "keys").mkdir()
    (tmp_path / "keys" / "token").write_text("synthetic secret")
    (tmp_path / "alias").symlink_to(tmp_path / "keys")
    with pytest.raises(ValueError, match="secret"):
        inspect_file(tmp_path, {"path": "alias/token", "sha256": "0" * 64})


def test_missing_external_files_are_explicitly_optional(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    catalogue = root / "catalog.json"
    catalogue.write_text(json.dumps({"schema_version": 1, "artifacts": [],
        "external_inputs": [{"id": "external", "path": "unavailable/file", "sha256": "0" * 64}]}))
    report = check(root, catalogue)
    assert report["ok"] and len(report["external_unverified"]) == 1
    assert not check(root, catalogue, require_external=True)["ok"]
    assert not report["external_inputs"][0]["remote_backup_verified"]


def test_existing_hash_without_git_blob_is_not_a_verified_backup(tmp_path):
    (tmp_path / "untracked").write_bytes(b"bytes")
    result = inspect_file(tmp_path, {"path": "untracked", "sha256": hashlib.sha256(b"bytes").hexdigest(),
                                   "git_tracked": True}, git_root=tmp_path)
    assert result["sha256_matches"]
    assert result["local_git_blob_matches"] is False
