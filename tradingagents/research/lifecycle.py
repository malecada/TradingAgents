"""Exclusive new-run claims and immutable JSON evidence, without financial logic."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import uuid

from .admission import admit, digest, local_path


def _now():
    return datetime.now(timezone.utc).isoformat()


def _encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def _fsync_dir(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _immutable(path: Path, value):
    """Publish complete bytes atomically; hard-link publication never overwrites."""
    data = _encode(value)
    temporary = path.parent / (".pending-" + uuid.uuid4().hex)
    try:
        with temporary.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
        _fsync_dir(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def _lock(root):
    directory = root / "research_runs"
    directory.mkdir(exist_ok=True)
    with (directory / ".lock").open("a") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        yield


class ResearchRun:
    """A claim consumes one budget attempt, even if the run later fails.

    complete.json files form an append-only sharded completion ledger. There is
    no second mutable index whose update could diverge after a crash. SIGKILL
    can leave only claim.json/partial outputs; that state blocks automatic retry.
    """
    def __init__(self, admission):
        self.admission = admission
        self.directory = admission.root / "research_runs" / admission.experiment_id
        self._published_outputs = {}
        self._claim_sha256 = None

    @classmethod
    def start(cls, *, root, registration, experiment, source, design_source=None, bindings=None):
        arguments = dict(root=root, registration=registration, experiment=experiment, source=source,
                         design_source=design_source, bindings=bindings)
        admitted = admit(**arguments)
        if not admitted.ready:
            raise ValueError("registered sample window/bindings are not complete; prospective evaluation must wait")
        with _lock(admitted.root):
            admitted = admit(**arguments)
            run = cls(admitted)
            run.directory.mkdir(exist_ok=False)
            (run.directory / "outputs").mkdir()
            exposures = [{**item, "identity": info["identity"]}
                         for info in admitted.spec["datasets"].values() for item in info["exposures"]]
            claim = {"schema_version": 1, "program_id": admitted.spec["program_id"],
                     "experiment_id": experiment, "started_at": _now(), "source": source,
                     "registration": registration, "registration_sha256": admitted.registration_sha256,
                     "design_source": admitted.design_source, "bindings": admitted.bindings,
                     "bindings_sha256": admitted.bindings_sha256, "inputs": admitted.inputs,
                     "family": admitted.family, "experiment": admitted.experiment,
                     "windows": admitted.windows, "prior_exposures": exposures}
            _immutable(run.directory / "claim.json", claim)
            run._claim_sha256 = digest((run.directory / "claim.json").read_bytes())
            try:
                run._check_inputs()
            except Exception as exc:
                run._fail_unlocked(type(exc).__name__ + ": " + str(exc))
                raise
            return run

    def _active(self):
        if digest((self.directory / "claim.json").read_bytes()) != self._claim_sha256:
            raise ValueError("own run claim changed after exclusive start")
        if any((self.directory / name).exists() for name in ("complete.json", "failed.json")):
            raise ValueError("run is terminal; output/completion cannot be repeated")

    def _check_inputs(self):
        for name, info in self.admission.inputs.items():
            if digest(local_path(self.admission.root, info["path"]).read_bytes()) != info["sha256"]:
                raise ValueError(f"input hash differs: {name}")

    def _check_source(self):
        current = admit(root=self.admission.root, registration=self.admission.registration,
                        experiment=self.admission.experiment_id, source=self.admission.source,
                        design_source=self.admission.design_source, bindings=self.admission.bindings,
                        _own_claim=self.admission.experiment_id)
        if current.registration_sha256 != self.admission.registration_sha256:
            raise ValueError("registration changed during run")
        if (current.experiment != self.admission.experiment or current.inputs != self.admission.inputs
                or current.bindings_sha256 != self.admission.bindings_sha256):
            raise ValueError("admitted contract changed during run")

    def read_input(self, name):
        """Return registered bytes only; validity of clocks/schema is runner-owned."""
        with _lock(self.admission.root):
            self._active()
            self._check_source()
            if name not in self.admission.inputs:
                raise ValueError("unregistered input")
            info = self.admission.inputs[name]
            data = local_path(self.admission.root, info["path"]).read_bytes()
            if digest(data) != info["sha256"]:
                self._fail_unlocked("input hash changed after admission")
                raise ValueError("input hash changed after admission")
            return data

    def write_json(self, name, value):
        with _lock(self.admission.root):
            self._active()
            if name not in self.admission.experiment["outputs"]:
                raise ValueError("unregistered output")
            self._check_source()
            _immutable(self.directory / "outputs" / name, value)
            self._published_outputs[name] = digest((self.directory / "outputs" / name).read_bytes())

    def _outputs(self):
        return {p.name: digest(p.read_bytes()) for p in sorted((self.directory / "outputs").iterdir()) if p.is_file()}

    def _fail_unlocked(self, reason):
        if not any((self.directory / name).exists() for name in ("complete.json", "failed.json")):
            _immutable(self.directory / "failed.json", {"status": "failed", "experiment_id": self.admission.experiment_id,
                "ended_at": _now(), "reason": reason, "output_sha256": self._outputs(),
                "claim_sha256": self._claim_sha256})

    def fail(self, reason):
        with _lock(self.admission.root):
            self._active()
            self._fail_unlocked(reason)

    def finish(self, cells):
        with _lock(self.admission.root):
            self._active()
            try:
                self._check_source()
                self._check_inputs()
                expected = self.admission.experiment["cells"]
                actual = [cell["id"] for cell in cells]
                if len(actual) != len(set(actual)) or set(actual) != set(expected):
                    raise ValueError("registered cells missing, duplicated or extra")
                if any(c["status"] not in {"complete", "unavailable"} for c in cells):
                    raise ValueError("cell status must be complete or unavailable")
                if any(c["status"] == "unavailable" and not c.get("reason") for c in cells):
                    raise ValueError("unavailable cells require a reason")
                outputs = self._outputs()
                if outputs != self._published_outputs:
                    raise ValueError("published output bytes changed outside the run helper")
                if set(outputs) != set(self.admission.experiment["outputs"]):
                    raise ValueError("declared outputs are missing or unregistered files exist")
                receipt = {"schema_version": 1, "status": "complete", "experiment_id": self.admission.experiment_id,
                    "ended_at": _now(), "source": self.admission.source, "cells": cells, "cell_count": len(cells),
                    "unavailable_count": sum(c["status"] == "unavailable" for c in cells),
                    "output_sha256": outputs, "claim_sha256": digest((self.directory / "claim.json").read_bytes()),
                    "registration_sha256": self.admission.registration_sha256}
                _immutable(self.directory / "complete.json", receipt)
                return receipt
            except Exception as exc:
                self._fail_unlocked(type(exc).__name__ + ": " + str(exc))
                raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        with _lock(self.admission.root):
            self._fail_unlocked("context exited without completion" if exc_type is None else exc_type.__name__ + ": " + str(exc_value))
        return False
