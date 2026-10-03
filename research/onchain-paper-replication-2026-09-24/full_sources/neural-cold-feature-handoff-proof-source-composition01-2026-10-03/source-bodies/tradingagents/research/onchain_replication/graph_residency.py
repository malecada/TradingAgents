"""Admitted aggregate graph-file budgets and context-owned mapped populations.

File-byte and mapping-count bounds exclude validation, adjacency, matching,
model allocations and page cache. Backing files must remain frozen throughout.
"""
from contextlib import contextmanager, ExitStack
from dataclasses import dataclass, field
import json
from pathlib import Path

from .mapped_graph import _MappedGraphSnapshot, open_mapped_graph, preflight_mapped_graph


# Issued by the context owner, never reconstructed from caller-provided labels.
# Entries disappear on every context exit; the graph's scientific fields do not
# contain execution ownership. This is an in-process cooperative-owner boundary.
_LIVE_POPULATIONS = {}


class GraphPopulationCleanupError(RuntimeError):
    """Fatal at the job boundary: no model batch may follow unsafe cleanup."""


def read_graph_policy(run, input_name):
    if input_name is None:
        return None
    if not isinstance(input_name, str) or not input_name:
        raise ValueError('graph residency input name required')
    policy = json.loads(run.read_input(input_name))
    validate_graph_policy(policy)
    return policy


def validate_graph_policy(policy):
    if (not isinstance(policy, dict)
            or set(policy) != {'schema_version', 'mode', 'max_graph_file_bytes', 'max_open_arrays'}
            or type(policy['schema_version']) is not int or policy['schema_version'] != 1
            or policy['mode'] != 'mapped'
            or any(type(policy[k]) is not int or policy[k] <= 0
                   for k in ('max_graph_file_bytes', 'max_open_arrays'))):
        raise ValueError('graph residency policy differs')


def registered_graph_manifests(run, producer):
    """Resolve only existing hash-admitted input manifests; no output-path guess."""
    population = producer['descriptor']['graph_population']
    if len(population) != len(set(population)) or set(producer['graphs']) != set(population):
        raise ValueError('registered graph population differs')
    manifests = []
    for h in population:
        reference = producer['graphs'][h]
        if set(reference) != {'input'}:
            raise ValueError('mapped graph loader requires admitted immutable graph input')
        name = reference['input']
        metadata = json.loads(run.read_input(name))
        if metadata['graph_hash'] != h:
            raise ValueError('registered graph manifest identity differs')
        info = run.admission.inputs[name]
        manifests.append((str((run.admission.root / info['path']).resolve()), info['sha256'], h))
    return tuple(manifests)


@dataclass(frozen=True)
class MappedGraphPopulation:
    """Live borrowed objects and their verified storage provenance; not science."""
    graphs: tuple
    manifests: tuple
    mapped_file_bytes: int
    open_arrays: int
    _mappings: tuple = field(repr=False)
    _active: bool = field(default=True, repr=False)

    def validate(self, policy, manifests):
        validate_graph_policy(policy)
        # Do not inspect numeric values until lifetime and provenance pass.
        issued = _LIVE_POPULATIONS.get(id(self))
        if (issued is None or issued[0] is not self or issued[1] is not self.graphs
                or issued[2] is not self.manifests or issued[3] is not self._mappings
                or issued[4:] != (self.mapped_file_bytes, self.open_arrays)):
            raise ValueError('mapped graph population has no issued ownership')
        if not self._active or any(m.closed for m in self._mappings):
            raise ValueError('mapped graph population is no longer live')
        if sorted(self.manifests) != sorted(manifests):
            raise ValueError('mapped graph population differs from admitted manifests')
        if (len(self.graphs) != len(self.manifests) or self.open_arrays != len(self._mappings)
                or self.mapped_file_bytes > policy['max_graph_file_bytes']
                or self.open_arrays > policy['max_open_arrays']):
            raise ValueError('mapped graph population exceeds registered budget')
        owned = {id(m) for m in self._mappings}
        actual_count = actual_bytes = 0
        for graph in self.graphs:
            if not isinstance(graph, _MappedGraphSnapshot):
                raise ValueError('mapped graph population contains eager graph')
            for name in ('node_ids', 'node_features', 'edge_index', 'edge_features', 'edge_aggregates'):
                value = getattr(graph, name)
                if value is not None:
                    if id(value._mmap) not in owned or value._mmap.closed:
                        raise ValueError('unowned graph array mapping')
                    actual_count += 1
                    actual_bytes += value.offset + value.nbytes
        if actual_count != self.open_arrays or actual_bytes != self.mapped_file_bytes:
            raise ValueError('mapped graph population storage accounting differs')


@contextmanager
def open_graph_population(manifests, policy, *, max_graph_payload_bytes=None):
    """Admit an entire producer population before its first graph mapping."""
    validate_graph_policy(policy)
    cap = policy['max_graph_file_bytes']
    if max_graph_payload_bytes is not None:
        if type(max_graph_payload_bytes) is not int or max_graph_payload_bytes <= 0:
            raise ValueError('positive aggregate graph payload capacity required')
        cap = min(cap, max_graph_payload_bytes)
    manifests = tuple((str(Path(p).resolve()), sha, h) for p, sha, h in manifests)
    if not manifests or len({h for _, _, h in manifests}) != len(manifests):
        raise ValueError('empty or duplicate mapped graph population')
    total = count = 0
    for path, sha, h in manifests:
        metadata, members, size = preflight_mapped_graph(path, sha, max_mapped_bytes=cap)
        if metadata['graph_hash'] != h:
            raise ValueError('mapped graph population identity differs')
        total += size
        count += len(members)
        if total > cap or count > policy['max_open_arrays']:
            raise ValueError('aggregate graph residency capacity exceeded before mapping')
    stack = ExitStack()
    mappings = []
    lease = None
    failure = None
    try:
        graphs = tuple(stack.enter_context(open_mapped_graph(path, sha, max_mapped_bytes=cap,
                       _map_observer=mappings.append)) for path, sha, _ in manifests)
        lease = MappedGraphPopulation(graphs, manifests, total, count, tuple(mappings))
        _LIVE_POPULATIONS[id(lease)] = (lease, lease.graphs, lease.manifests, lease._mappings, total, count)
        lease.validate(policy, manifests)
        yield lease
    except BaseException as error:
        failure = error
        raise
    finally:
        if lease is not None:
            _LIVE_POPULATIONS.pop(id(lease), None)
            object.__setattr__(lease, '_active', False)
        try:
            stack.close()
        except BaseException as error:
            raise GraphPopulationCleanupError('graph population cleanup failed; fitting forbidden') from error
        if any(not m.closed for m in mappings):
            raise GraphPopulationCleanupError('graph mappings remain open; fitting forbidden') from failure
