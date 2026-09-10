"""Isolation regressions: invented subprocess tests only, never a financial replay."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def isolated_repo(tmp_path):
    root = tmp_path / "repo"
    (root / "scripts").mkdir(parents=True)
    (root / "tests").mkdir()
    shutil.copy2(ROOT / "conftest.py", root / "conftest.py")
    shutil.copy2(ROOT / "scripts/verify_offline.py", root / "scripts/verify_offline.py")
    return root


def invoke(root, *args):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(root),
               PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    env.pop("PYTEST_ADDOPTS", None)
    return subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                           "--import-mode=importlib", *args], cwd=root, env=env,
                          capture_output=True, text=True, timeout=30)


def test_unreviewed_module_is_not_imported(isolated_repo):
    (isolated_repo / "tests/test_unreviewed.py").write_text(
        "from pathlib import Path\nPath('imported').write_text('bad')\n"
        "def test_unreviewed(): pass\n")
    result = invoke(isolated_repo, "tests")
    assert result.returncode == 5, result.stdout + result.stderr
    assert not (isolated_repo / "imported").exists()
    assert "withheld" in result.stdout


@pytest.mark.parametrize("path", ["tests/regression/test_v2_unchanged.py",
                                  "tests/execution/test_exchange_smoke.py"])
def test_external_module_is_not_imported_by_default(isolated_repo, path):
    file = isolated_repo / path
    file.parent.mkdir(parents=True)
    file.write_text("raise RuntimeError('external module imported')\n")
    result = invoke(isolated_repo, path)
    assert result.returncode == 4, result.stdout + result.stderr
    assert "not admitted" in result.stderr
    assert "external module imported" not in result.stdout


@pytest.mark.parametrize("body,reason", [
    ("import socket\nsocket.getaddrinfo('example.invalid', 443)", "network access"),
    ("import socket\nsocket.socket().connect(('127.0.0.1', 9))", "network access"),
    ("from pathlib import Path\nPath('data/retained').write_text('changed')", "retained store"),
])
def test_guard_applies_during_collection(isolated_repo, body, reason):
    (isolated_repo / "data").mkdir()
    (isolated_repo / "data/retained").write_text("original")
    (isolated_repo / "tests/test_offline_workflow.py").write_text(body)
    result = invoke(isolated_repo, "tests/test_offline_workflow.py")
    assert result.returncode == 2, result.stdout + result.stderr
    assert reason in result.stdout
    assert (isolated_repo / "data/retained").read_text() == "original"


def test_directory_fd_cleanup_does_not_resolve_against_repository_cwd(isolated_repo):
    (isolated_repo / "tests/test_offline_workflow.py").write_text(
        "import os\nimport tempfile\nfrom pathlib import Path\n"
        "def test_temporary_cleanup():\n"
        "    with tempfile.TemporaryDirectory() as tmp:\n"
        "        (Path(tmp) / 'data').mkdir()\n"
        "        fd = os.open(tmp, os.O_RDONLY)\n"
        "        try: os.rmdir('data', dir_fd=fd)\n"
        "        finally: os.close(fd)\n")
    result = invoke(isolated_repo, "tests/test_offline_workflow.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout


def test_empirical_flag_is_required_even_for_marked_reviewed_module(isolated_repo):
    (isolated_repo / "tests/test_offline_workflow.py").write_text(
        "import pytest\n@pytest.mark.empirical\ndef test_external():\n"
        "    raise RuntimeError('external test executed')\n")
    result = invoke(isolated_repo, "tests/test_offline_workflow.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 skipped" in result.stdout
    assert "external test executed" not in result.stdout


def test_v2_replay_uses_copied_inputs_without_running_backtest(tmp_path, monkeypatch):
    # Load function definitions only: importing/running the legacy test is not admission.
    import ast
    source = ROOT / "tests/regression/test_v2_unchanged.py"
    tree = ast.parse(source.read_text())
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_isolated_replay_command"]
    assert len(functions) == 1
    namespace = {"Path": Path, "shutil": shutil, "sys": sys, "REPO_ROOT": ROOT}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(source), "exec"), namespace)
    original = tmp_path / "original"
    original.mkdir()
    for horizon in (7, 14):
        (original / f"preds_lgb_h{horizon}.csv").write_text("fabricated fixture\n")
    before = {p.name: p.read_bytes() for p in original.iterdir()}
    command, copy = namespace["_isolated_replay_command"](original, tmp_path / "run")
    assert Path(command[command.index("--pred-dir") + 1]) == copy
    assert copy != original and copy.is_relative_to(tmp_path / "run")
    assert {p.name: p.read_bytes() for p in copy.iterdir()} == before
    (copy / "report_v2").mkdir()
    (copy / "report_v2/metrics.json").write_text("fabricated output")
    assert {p.name: p.read_bytes() for p in original.iterdir()} == before
