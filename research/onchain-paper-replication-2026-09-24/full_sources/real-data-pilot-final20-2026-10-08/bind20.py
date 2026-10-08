"""Materialize the accepted diagnostic draft using the existing transport binder.

No network, numerical imports, admission or claim. Private path metadata stays
in the accounted private runtime directory; key bodies are never opened.
"""
import hashlib
import json
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
F = HERE.parent


def load(path):
    return json.loads(path.read_bytes())


def ref(path):
    body = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}


def save(path, value):
    with path.open("xb") as stream:
        stream.write((json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())


def main():
    review = F / 'real-data-pilot-residual-metadata-review01-2026-10-08/prefix-review04/MANIFEST04.json'
    assert ref(review)['sha256'] == 'f401b3e0bfb30d06a8a9c4f00b24b2b4f8aed951da569d71ccc6f6664f2c2ca2'
    assert load(review)['status'] == 'NARROW_DIAGNOSTIC_METADATA_ACCEPTED_NOT_ENTRY'
    old = F / 'real-data-pilot-final19-2026-10-08/TRANSPORT_REQUEST01.json'
    parent = ROOT / 'research_artifacts/real_pilot_runtime/pilot-transport-20261008-20-01'
    assert not parent.exists() and not (HERE / 'TRANSPORT_BINDING05.json').exists()
    request = dict(prepared=ref(HERE / 'PREPARATION_RESULT05.json'),
                   archive_policy=ref(HERE / 'templates02/archive_policy.json'),
                   connection=load(old)['connection'], private_parent=str(parent.relative_to(ROOT)),
                   private_leaf='archive_transport01.json')
    save(HERE / 'TRANSPORT_REQUEST05.json', request)
    parent.mkdir(mode=0o700)
    path = F / 'real-data-pilot-transport-binding-preparation01-2026-10-06/bind01.py'
    binder = types.ModuleType('accepted_transport_binder'); binder.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), 'exec'), vars(binder))
    bound = binder.bind(ROOT, request)
    save(HERE / 'TRANSPORT_BINDING05.json', bound)
    directory = HERE / 'inputs05'; directory.mkdir()
    refs = {}
    for role, value in bound['inputs'].items():
        target = directory / (role + '.json')
        with target.open('xb') as stream:
            stream.write(binder.raw(value))
        refs[role] = ref(target)
    refs.update(bound['private_input'])
    save(HERE / 'INPUT_REFS05.json', refs)
    save(HERE / 'BINDING_EXIT05.json', dict(status='BOUND_DRAFT_NOT_ADMITTED',
         public_documents=len(bound['inputs']), private_references=len(bound['private_input']),
         empirical_execution=False, claim=False, metadata_review=ref(review)))
    print(json.dumps(dict(status='BOUND_DRAFT_NOT_ADMITTED', inputs=len(refs), empirical_execution=False)))


if __name__ == '__main__':
    main()
