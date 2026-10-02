"""Fresh disposable Git repos; invented bytes only, no owner or market fixtures."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
from pathlib import Path
import subprocess

import pytest

from tradingagents.research import admission as a


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.PIPE).strip()


def commit(root):
    git(root, "add", "--all")
    git(root, "-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid",
        "commit", "--allow-empty", "-qm", "synthetic")
    return git(root, "rev-parse", "HEAD").decode()


def repository(root, files, object_format="sha1"):
    git(root, "init", "-q", f"--object-format={object_format}")
    for name, body in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    source = commit(root)
    return source, {name: hashlib.sha256(body).hexdigest() for name, body in files.items()}


def check(root, source, files, design=None):
    assert hasattr(a, "_source_files"), "bounded fresh source-file verification is missing"
    return a._source_files(root, source, design or source, files)


@pytest.mark.parametrize("object_format", ["sha1", "sha256"])
@pytest.mark.parametrize("distinct", [False, True])
def test_binary_paths_and_fresh_distinct_commits(tmp_path, object_format, distinct):
    files = {"empty": b"", "space name": b"a\x00b\n", "tab\tname": b"\xff\xfe",
             "unicode-π": b"a" * 40 + b" blob 9\nheader\n", "line\nbreak": b"line",
             "raw-\udcff": b"raw"}
    source, hashes = repository(tmp_path, files, object_format)
    design = source
    if distinct:
        source = commit(tmp_path)
    assert check(tmp_path, source, hashes, design) is None


@pytest.mark.parametrize("mutation, message", [
    ("worktree-size", "committed source differs"),
    ("worktree-bytes", "committed source differs"),
    ("hash", "registered source hash differs"),
    ("design", "source differs from design freeze"),
    ("missing-source", "cannot be verified"),
    ("missing-design", "cannot be verified"),
])
def test_source_rejections(tmp_path, mutation, message):
    design, hashes = repository(tmp_path, {"file": b"old"})
    source = design
    if mutation == "worktree-size":
        (tmp_path / "file").write_bytes(b"longer")
    elif mutation == "worktree-bytes":
        (tmp_path / "file").write_bytes(b"new")
    elif mutation == "hash":
        hashes["file"] = "0" * 64
    elif mutation == "design":
        (tmp_path / "file").write_bytes(b"new")
        source = commit(tmp_path)
        hashes["file"] = hashlib.sha256(b"new").hexdigest()
    elif mutation == "missing-source":
        (tmp_path / "file").unlink()
        source = commit(tmp_path)
        (tmp_path / "file").write_bytes(b"old")
    else:
        (tmp_path / "extra").write_bytes(b"extra")
        source = commit(tmp_path)
        hashes["extra"] = hashlib.sha256(b"extra").hexdigest()
    with pytest.raises(ValueError, match=message):
        check(tmp_path, source, hashes, design)


@pytest.mark.parametrize("name", ["keys/a", "apis/a", ".env", ".env.local", "hf_token.txt",
                                  "../outside", "/absolute", "nul\x00path"])
def test_forbidden_names_are_refused_before_batch_process(tmp_path, monkeypatch, name):
    def forbidden(*args, **kwargs):
        pytest.fail("invalid path reached Git")
    monkeypatch.setattr(a.subprocess, "run", forbidden)
    with pytest.raises(ValueError):
        check(tmp_path, "a" * 40, {name: "0" * 64})


def test_symlink_to_secret_is_refused(tmp_path):
    (tmp_path / "keys").mkdir()
    (tmp_path / "alias").symlink_to("keys/a")
    with pytest.raises(ValueError, match="secret"):
        check(tmp_path, "a" * 40, {"alias": "0" * 64})


def test_original_design_name_is_not_normalized(tmp_path):
    source, hashes = repository(tmp_path, {"dir/file": b"body"})
    with pytest.raises(ValueError, match="cannot be verified"):
        check(tmp_path, source, {"dir//file": hashes["dir/file"]})


def test_count_and_byte_thresholds_bound_processes_and_oversize_falls_back(tmp_path, monkeypatch):
    source, hashes = repository(tmp_path, {str(i): b"abcd" for i in range(7)} | {"big": b"x" * 20})
    monkeypatch.setattr(a, "_SOURCE_BATCH_FILES", 2, raising=False)
    monkeypatch.setattr(a, "_SOURCE_BATCH_BYTES", 16, raising=False)
    real_run = subprocess.run
    calls = []
    def observe(*args, **kwargs):
        result = real_run(*args, **kwargs)
        if "cat-file" in args[0]:
            calls.append((args[0], kwargs["input"], result.stdout))
        return result
    monkeypatch.setattr(a.subprocess, "run", observe)
    assert check(tmp_path, source, hashes) is None
    sizes, bodies = [c for c in calls if "--batch-check" in c[0]], [c for c in calls if "--batch" in c[0]]
    assert len(sizes) == 4
    assert len(bodies) == 4
    assert all(len(request.splitlines()) <= 4 for _, request, _ in calls)
    assert all(len(output) <= 16 + 4 * 100 for _, _, output in bodies)
    assert all(b"x" * 20 not in output for _, _, output in bodies)


@pytest.mark.parametrize("phase", ["--batch-check", "--batch"])
@pytest.mark.parametrize("bad", [b"", b"missing missing\n", b"ambiguous ambiguous\n",
    b"a" * 40 + b" tree 0\n", b"g" * 40 + b" blob 0\n", b"a" * 41 + b" blob 0\n",
    b"a" * 40 + b" blob -1\n", b"a" * 40 + b" blob 1.0\n",
    b"a" * 40 + b" blob 0\nextra\n"])
def test_malformed_git_responses_fail_closed(tmp_path, monkeypatch, phase, bad):
    source, hashes = repository(tmp_path, {"file": b"body"})
    real_run = subprocess.run
    def corrupt(*args, **kwargs):
        result = real_run(*args, **kwargs)
        if phase in args[0]:
            result.stdout = bad
        return result
    monkeypatch.setattr(a.subprocess, "run", corrupt)
    with pytest.raises(ValueError, match="cannot be verified"):
        check(tmp_path, source, hashes)


@pytest.mark.parametrize("corruption", ["truncated", "extra", "delimiter", "oid", "size"])
def test_body_framing_matches_size_query(tmp_path, monkeypatch, corruption):
    source, hashes = repository(tmp_path, {"file": b"body"})
    real_run = subprocess.run
    def corrupt(*args, **kwargs):
        result = real_run(*args, **kwargs)
        if "--batch" in args[0]:
            if corruption == "truncated":
                result.stdout = result.stdout[:-1]
            elif corruption == "extra":
                result.stdout += b"extra"
            elif corruption == "delimiter":
                result.stdout = result.stdout[:-1] + b"x"
            elif corruption == "oid":
                result.stdout = b"0" * 40 + result.stdout[40:]
            else:
                result.stdout = result.stdout.replace(b" blob 4\n", b" blob 5\n", 1)
        return result
    monkeypatch.setattr(a.subprocess, "run", corrupt)
    with pytest.raises(ValueError, match="cannot be verified"):
        check(tmp_path, source, hashes)


@pytest.mark.parametrize("phase", ["--batch-check", "--batch"])
@pytest.mark.parametrize("error", [OSError("synthetic process unavailable"),
                                     subprocess.CalledProcessError(1, "git")])
def test_process_failures_are_converted(tmp_path, monkeypatch, phase, error):
    source, hashes = repository(tmp_path, {"file": b"body"})
    real_run = subprocess.run
    def fail(*args, **kwargs):
        if phase in args[0]:
            raise error
        return real_run(*args, **kwargs)
    monkeypatch.setattr(a.subprocess, "run", fail)
    with pytest.raises(ValueError, match="cannot be verified"):
        check(tmp_path, source, hashes)


def test_size_mismatch_refuses_body_fetch(tmp_path, monkeypatch):
    source, hashes = repository(tmp_path, {"file": b"body"})
    (tmp_path / "file").write_bytes(b"short")
    real_run = subprocess.run
    def observe(*args, **kwargs):
        assert "--batch" not in args[0], "body fetched despite mismatched extent"
        return real_run(*args, **kwargs)
    monkeypatch.setattr(a.subprocess, "run", observe)
    with pytest.raises(ValueError, match="committed source differs"):
        check(tmp_path, source, hashes)


def test_mutation_during_body_fetch_is_detected(tmp_path, monkeypatch):
    source, hashes = repository(tmp_path, {"file": b"body"})
    real_run = subprocess.run
    def mutate(*args, **kwargs):
        result = real_run(*args, **kwargs)
        if "--batch" in args[0]:
            (tmp_path / "file").write_bytes(b"evil")
        return result
    monkeypatch.setattr(a.subprocess, "run", mutate)
    with pytest.raises(ValueError, match="committed source differs"):
        check(tmp_path, source, hashes)


def test_checks_are_fresh_and_concurrent_calls_are_independent(tmp_path):
    source, hashes = repository(tmp_path, {"file": b"body"})
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(lambda _: check(tmp_path, source, hashes), range(8))) == [None] * 8
    (tmp_path / "file").write_bytes(b"evil")
    with pytest.raises(ValueError, match="committed source differs"):
        check(tmp_path, source, hashes)
