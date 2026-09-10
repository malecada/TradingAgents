"""Independent synthetic functional checks for the fixed effort-evaluation packet.

Run only after inspecting the candidate source. Outputs and child processes use
temporary invented ledgers; no trading data or production package is imported.
"""
from __future__ import annotations
import argparse
import json
import multiprocessing as mp
from pathlib import Path
import tempfile


def evaluate(answer: Path) -> dict:
    code = json.loads(answer.read_text())["code"]
    namespace = {}
    exec(compile(code, str(answer), "exec"), namespace)
    append = namespace["append_once"]
    results = []

    def case(name, function):
        try:
            function()
        except Exception as exc:
            results.append({"check": name, "passed": False, "error": f"{type(exc).__name__}: {exc}"})
        else:
            results.append({"check": name, "passed": True})

    with tempfile.TemporaryDirectory(prefix="effort-eval-") as folder:
        root = Path(folder)

        def standard():
            path = root / "standard.jsonl"
            assert append(path, {"id": "a", "value": 1}) is True
            before = path.read_bytes()
            assert append(path, {"value": 1, "id": "a"}) is False
            assert path.read_bytes() == before
            try:
                append(path, {"id": "a", "value": 2})
            except ValueError:
                pass
            else:
                raise AssertionError("same-ID conflict accepted")
            assert path.read_bytes() == before
            assert append(path, {"id": "b", "value": "ž"}) is True
            assert len(path.read_text().splitlines()) == 2

        case("new_id_idempotence_conflict_unicode", standard)
        bad_rows = [b"{", b'{"id":"old"}\n{"id":"old"}\n',
                    b'{"id":"old","v":NaN}\n', b'{"id":"old","v":1e999}\n',
                    b'[]\n', b'{"id":""}\n', b'\xff\n']
        for index, content in enumerate(bad_rows):
            def invalid(content=content, index=index):
                path = root / f"bad-{index}.jsonl"
                path.write_bytes(content)
                try:
                    append(path, {"id": "new"})
                except ValueError:
                    pass
                else:
                    raise AssertionError("malformed existing ledger accepted")
                assert path.read_bytes() == content
            case(f"malformed_existing_{index}_preserved", invalid)

        for index, value in enumerate([float("nan"), float("inf"), object()]):
            def serialization(value=value, index=index):
                path = root / f"serial-{index}.jsonl"
                path.write_bytes(b'{"id":"old"}\n')
                before = path.read_bytes()
                try:
                    append(path, {"id": "new", "value": value})
                except (ValueError, TypeError):
                    pass
                else:
                    raise AssertionError("invalid new JSON accepted")
                assert path.read_bytes() == before
            case(f"serialization_failure_{index}_preserved", serialization)

        def concurrent():
            path = root / "concurrent.jsonl"
            context = mp.get_context("fork")
            event = context.Event()
            def worker(index):
                event.wait(10)
                append(path, {"id": "shared", "value": 1})
                append(path, {"id": str(index), "value": index})
            processes = [context.Process(target=worker, args=(i,)) for i in range(12)]
            try:
                for process in processes:
                    process.start()
                event.set()
                for process in processes:
                    process.join(10)
                    assert not process.is_alive() and process.exitcode == 0
                rows = [json.loads(line) for line in path.read_text().splitlines()]
                assert len(rows) == 13
                assert {row["id"] for row in rows} == {"shared", *(str(i) for i in range(12))}
            finally:
                for process in processes:
                    if process.is_alive():
                        process.terminate()
                    if process.pid is not None:
                        process.join()
        case("concurrent_cooperating_writers", concurrent)
    return {"answer": answer.name, "checks": results, "passed": all(r["passed"] for r in results)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("answers", nargs="+", type=Path)
    args = parser.parse_args()
    reports = [evaluate(path) for path in args.answers]
    print(json.dumps(reports, indent=2))
    raise SystemExit(int(not all(report["passed"] for report in reports)))
