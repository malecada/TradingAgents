"""Synthetic-tested completion-window Local40 adapter; no source acquisition."""
from raphtory import Graph, algorithms


def local(events, delta):
    if not events:
        return {}
    graph = Graph()
    for seconds, order, sender, recipient in events:
        graph.add_edge(seconds, sender, recipient, event_id=order)
    if graph.count_temporal_edges() != len(events):
        raise ValueError('event multiplicity changed')
    result = algorithms.local_temporal_three_node_motifs(graph, delta, threads=2)
    return {node.name: list(value['motif_counter']) for node, value in result.items()}


def completion_window(events, *, start, end, delta, coverage_start, coverage_end):
    """Attribute each motif to its last event in [start,end), using prior overlap.

    Coverage arguments are caller assertions, not proof of source completeness.
    Returned node universe includes the overlap; active-day nodes are separate.
    No price outcome or historical publication-time admission follows.
    """
    if any(type(v) is not int for v in (start, end, delta, coverage_start, coverage_end)):
        raise ValueError('integer-second bounds required')
    if delta < 0 or start >= end:
        raise ValueError('invalid interval or delta')
    if coverage_start > start - delta or coverage_end < end:
        raise ValueError('complete prior overlap and target coverage required')
    ids, selected, prefix, active = set(), [], [], set()
    previous = None
    for event in events:
        if len(event) != 4:
            raise ValueError('four-field event required')
        seconds, order, sender, recipient = event
        if type(seconds) is not int or type(order) is not int or order < 0:
            raise ValueError('integer timestamp and nonnegative event ID required')
        if not isinstance(sender, str) or not sender or not isinstance(recipient, str) or not recipient or sender == recipient:
            raise ValueError('distinct nonempty address strings required')
        if not coverage_start <= seconds < coverage_end:
            raise ValueError('event outside declared source coverage')
        if order in ids or (previous is not None and (seconds, order) <= previous):
            raise ValueError('unique event IDs and chronological order required')
        ids.add(order); previous = (seconds, order)
        if start - delta <= seconds < end:
            selected.append(event)
            if seconds < start:
                prefix.append(event)
            else:
                active.update((sender, recipient))
    combined = local(selected, delta)
    before = local(prefix, delta)
    for node, values in combined.items():
        combined[node] = [n - old for n, old in zip(values, before.get(node, [0]*40), strict=True)]
        if len(combined[node]) != 40 or any(n < 0 for n in combined[node]):
            raise ValueError('invalid nonnegative completion counts')
    return {'local_counts': combined, 'active_day_nodes': sorted(active),
            'selected_events': len(selected), 'prefix_events': len(prefix),
            'assignment': 'last-event timestamp in half-open target interval',
            'historical_availability_verified': False}
