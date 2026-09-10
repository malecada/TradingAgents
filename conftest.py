"""Ensure pytest imports the worktree's tradingagents package.

The editable install (`pip install -e .`) points at the primary repo, so
without this shim pytest run from a worktree would import the primary
repo's package and miss any local changes (e.g. new submodules added on a
feature branch).
"""
from __future__ import annotations

import sys
from pathlib import Path

import os
import socket
import pytest

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.verify_offline import OFFLINE_FILES, OFFLINE_DIRECTORIES, EXTERNAL_FILES, requirements


def pytest_addoption(parser):
    group = parser.getgroup("research isolation")
    for kind in ("empirical", "network", "account"):
        group.addoption("--run-" + kind, action="store_true", default=False,
                        help=f"Explicitly admit reviewed {kind} tests; research authorization still applies")


def _admitted(relative, config):
    required = requirements(relative)
    return required is not None and all(config.getoption("--run-" + kind) for kind in required)


def pytest_configure(config):
    sys.dont_write_bytecode = True
    config._research_withheld = set()
    config._research_isolation_active = True
    for kind in ("empirical", "network", "account"):
        config.addinivalue_line("markers", f"{kind}: requires explicit --run-{kind}")
    # Explicit-file requests must not bypass pytest_ignore_collect.
    for arg in config.args:
        path = Path(str(arg).split("::", 1)[0])
        if not path.is_absolute():
            path = Path.cwd() / path
        if path.is_file() and path.name.startswith("test_"):
            try:
                relative = path.resolve().relative_to(_ROOT).as_posix()
            except ValueError:
                raise pytest.UsageError("test path outside the reviewed checkout is not admitted")
            if not _admitted(relative, config):
                raise pytest.UsageError(f"{relative} is not admitted by the reviewed profile; see docs/TESTING.md")

    def audit(event, args):
        if not config._research_isolation_active:
            return
        if not config.getoption("--run-network"):
            if event in {"socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr"}:
                raise RuntimeError("offline verification forbids network access")
            if event in {"socket.connect", "socket.sendto"} and args[0].family in {socket.AF_INET, socket.AF_INET6}:
                raise RuntimeError("offline verification forbids network access")
        write_paths = []
        if event == "open" and len(args) >= 3:
            path, mode, flags = args[:3]
            if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                    isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)):
                write_paths = [(path, None)]
        elif event in {"os.remove", "os.rmdir", "os.mkdir", "os.chmod", "os.truncate"}:
            index = 1 if event in {"os.remove", "os.rmdir"} else 2
            write_paths = [(args[0], args[index] if len(args) > index else None)]
        elif event in {"os.rename", "os.link"}:
            write_paths = [(args[0], args[2]), (args[1], args[3])]
        elif event == "os.symlink":
            write_paths = [(args[1], args[2])]
        for raw, directory_fd in write_paths:
            if not isinstance(raw, (str, bytes, os.PathLike)):
                continue
            path = Path(os.fsdecode(raw))
            if not path.is_absolute() and isinstance(directory_fd, int) and directory_fd >= 0:
                path = Path(os.readlink(f"/proc/self/fd/{directory_fd}")) / path
            path = path.resolve()
            protected = path.is_relative_to(_ROOT / "data")
            try:
                sibling = path.relative_to(_ROOT.parent).parts
                protected |= len(sibling) >= 2 and sibling[0].startswith("TradingAgents") and sibling[1] == "data"
            except ValueError:
                pass
            if protected:
                raise RuntimeError("verification cannot write a retained store; use temporary fixtures")
    sys.addaudithook(audit)


def pytest_ignore_collect(collection_path, config):
    try:
        relative = collection_path.resolve().relative_to(_ROOT).as_posix()
    except ValueError:
        return True
    if collection_path.is_dir():
        allowed = [name for name in (*OFFLINE_FILES, *EXTERNAL_FILES) if _admitted(name, config)]
        return not (relative == "." or any(name.startswith(relative + "/") for name in allowed)
                    or any(relative == d or relative.startswith(d + "/") or d.startswith(relative + "/") for d in OFFLINE_DIRECTORIES))
    if collection_path.name.startswith("test_") and collection_path.suffix == ".py":
        if not _admitted(relative, config):
            config._research_withheld.add(relative)
            return True
    return None


def pytest_collection_modifyitems(config, items):
    for item in items:
        for kind in ("empirical", "network", "account"):
            if item.get_closest_marker(kind) and not config.getoption("--run-" + kind):
                item.add_marker(pytest.mark.skip(reason="requires explicit --run-" + kind))
        if item.get_closest_marker("online") and not config.getoption("--run-network"):
            item.add_marker(pytest.mark.skip(reason="requires explicit --run-network"))


def pytest_terminal_summary(terminalreporter, config):
    count = len(config._research_withheld)
    terminalreporter.write_sep("-", f"reviewed profile: {count} encountered files withheld; this is not the full legacy suite")


def pytest_unconfigure(config):
    config._research_isolation_active = False
