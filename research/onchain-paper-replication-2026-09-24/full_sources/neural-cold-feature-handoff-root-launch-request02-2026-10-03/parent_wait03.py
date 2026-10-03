"""Retain an actual one-use root-wrapper command, child identity and wait.

This stdlib parent neither admits a research claim nor synthesizes a child
terminal. The exact reviewed wrapper remains responsible for native execution.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import stat
import subprocess
import sys
import time

MAX = 4 * 1024**2
GIB = 1024**3


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    p = Path(path)
    require(p.is_absolute() and p.resolve() == p, "canonical absolute file required")
    for parent in (p, *p.parents):
        require(not parent.is_symlink(), "redirected parent file")
    s = p.lstat()
    require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and s.st_size <= MAX,
            "bounded single-link parent file required")
    b = p.read_bytes()
    require(p.lstat() == s and len(b) == s.st_size, "parent file changed")
    return b


def ref(path):
    return {"path": str(path), "sha256": hashlib.sha256(read(path)).hexdigest()}


def write(root, name, value):
    data = (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode()
    require(len(data) <= MAX, "parent receipt exceeds file limit")
    fd = os.open(root / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    primary = None
    try:
        offset = 0
        while offset < len(data):
            n = os.write(fd, data[offset:offset + 65536])
            require(n > 0, "parent receipt short write")
            offset += n
        os.fsync(fd)
    except BaseException as error:
        primary = error
    finally:
        try:
            os.close(fd)
        except BaseException as error:
            primary = select(primary, error)
    if primary is not None:
        raise primary
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(directory)
    except BaseException as error:
        primary = error
    finally:
        try:
            os.close(directory)
        except BaseException as error:
            primary = select(primary, error)
    if primary is not None:
        raise primary


def select(first, later):
    # A first fatal exception cannot be replaced by a later cleanup exception.
    if first is not None and (not isinstance(first, Exception) or
                              isinstance(first, (MemoryError, RecursionError))):
        return first
    return later if first is None or not isinstance(later, Exception) or isinstance(
        later, (MemoryError, RecursionError)) else first


def wait_owned(command, cwd, stdout, stderr, on_child, monitor, seconds=2700):
    child = None
    primary = None
    previous = {}
    started = time.monotonic()

    def interrupted(number, frame):
        raise InterruptedError("actual root parent interrupted")

    try:
        for sig in (signal.SIGTERM, signal.SIGINT):
            previous[sig] = signal.signal(sig, interrupted)
        child = subprocess.Popen(command, cwd=cwd, stdout=stdout, stderr=stderr,
                                 start_new_session=True)
        on_child(child)
        while child.poll() is None:
            require(time.monotonic() - started < seconds, "parent active wait deadline")
            monitor()
            time.sleep(0.25)
    except BaseException as error:
        primary = error
    finally:
        if child is not None:
            try:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=150)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait(timeout=5)
                    raise RuntimeError("root wrapper required forced kill; descendant closure is uncertain")
            except BaseException as error:
                primary = select(primary, error)
        for sig, handler in previous.items():
            try:
                signal.signal(sig, handler)
            except BaseException as error:
                primary = select(primary, error)
    return child, primary


def finish_wait(output, child, primary, request, identity, command, fds):
    # Close all stdio before publishing the wait. Every later close/publication
    # is independently attempted and reduced against the original failure.
    for fd in fds:
        try:
            os.close(fd)
        except BaseException as error:
            primary = select(primary, error)
    if child is not None and child.returncode is not None:
        try:
            require(not Path("/proc", str(child.pid)).exists(), "actual wrapper PID remains or reused")
        except BaseException as error:
            primary = select(primary, error)
        try:
            write(output, "wait.json", {"schema_version": 1, "identity": identity,
                  "source": request["source"], "wrapper_pid": child.pid,
                  "wrapper_exit_code": child.returncode, "command": command,
                  "request": request["request_reference"],
                  "output_root": str(Path(request["output_parent"]) / identity)})
        except BaseException as error:
            primary = select(primary, error)
        if child.returncode != 0:
            primary = select(primary, RuntimeError("actual root wrapper failed; original nonzero wait retained"))
    else:
        primary = select(primary, RuntimeError("no actual wrapper wait was observed"))
    if primary is not None:
        try:
            write(output, "failure.json", {"schema_version": 1, "kind": "actual-root-parent-failure",
                  "error_type": type(primary).__name__,
                  "wrapper_exit_code": None if child is None else child.returncode,
                  "child_terminal_synthesized": False, "automatic_retry": False})
        except BaseException as error:
            primary = select(primary, error)
    return primary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--command", required=True)
    parser.add_argument("--command-sha256", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    body = read(args.command)
    require(hashlib.sha256(body).hexdigest() == args.command_sha256, "exact command changed")
    document = json.loads(body)
    command = document["argv"]
    request_ref = document["request"]
    require(ref(request_ref["path"]) == request_ref, "original request changed")
    request = json.loads(read(request_ref["path"]))
    identity = document["allowed_identity"]
    require(identity == "compact-cold-inputs-20261003-01" and request["phase"] == "materialize",
            "this exact parent selects only materialization")
    require(command == [sys.executable, "-B", document["launcher"]["path"], "--request",
                        request_ref["path"], "--request-sha256", request_ref["sha256"]],
            "actual locked wrapper command differs")
    require(ref(document["launcher"]["path"]) == document["launcher"], "wrapper source changed")
    require(Path.cwd() == Path(document["cwd"]) == Path(request["capsule"]), "actual capsule cwd differs")
    output = Path(args.output)
    require(output.is_absolute() and output.resolve() == output and not output.is_relative_to(Path.cwd()),
            "separate canonical parent output required")
    for p in (output, *output.parents):
        require(not p.is_symlink(), "redirected parent output")
    require(not os.path.lexists(output), "parent attempt already reserved; never retry")
    require(shutil.disk_usage(output.parent).free >= 10 * GIB, "parent disk floor unavailable")
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX, MAX))
    output.mkdir(mode=0o700, exist_ok=False)
    write(output, "intent.json", {"schema_version": 1, "kind": "actual-root-parent-intent-not-research-claim",
          "command_document": {"path": args.command, "sha256": args.command_sha256},
          "command": command, "request": request_ref, "source": request["source"],
          "identity": identity, "parent_pid": os.getpid(), "python": sys.executable,
          "python_version": sys.version, "cwd": str(Path.cwd()), "file_limit": list(resource.getrlimit(resource.RLIMIT_FSIZE)),
          "selected_inherited_environment": {k: os.environ[k] for k in
             ("PYTHONDONTWRITEBYTECODE", "PYTHONPATH", "TMPDIR", "XDG_CACHE_HOME", "TORCH_HOME", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS") if k in os.environ},
          "automatic_retry": False, "no_hard_whole_invocation_deadline": True})
    fds = []
    child = None
    primary = None
    try:
        for name in ("wrapper.stdout", "wrapper.stderr"):
            fds.append(os.open(output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600))
        def on_child(child):
            ticks = Path("/proc", str(child.pid), "stat").read_text().rsplit(")", 1)[1].split()[19]
            write(output, "child.json", {"schema_version": 1, "pid": child.pid,
                                        "start_ticks": ticks, "command": command})

        def monitor():
            rows = list(output.iterdir())
            require(len(rows) <= 16, "parent output count exceeded")
            total = 0
            for p in rows:
                s = p.lstat()
                require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and s.st_size < MAX,
                        "parent output file limit/type differs")
                total += s.st_blocks * 512
            require(total <= 16 * 1024**2 and shutil.disk_usage(output).free >= 10 * GIB,
                    "parent output storage floor exceeded")

        child, primary = wait_owned(command, Path.cwd(), fds[0], fds[1], on_child, monitor)
    except BaseException as error:
        primary = select(primary, error)
    finally:
        joined = {**request, "request_reference": request_ref}
        primary = finish_wait(output, child, primary, joined, identity, command, fds)
    if primary is not None:
        raise primary



if __name__ == "__main__":
    main()
