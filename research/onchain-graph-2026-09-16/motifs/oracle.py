"""Small exhaustive specification oracle; never used for whole-day counting."""
from itertools import combinations


def brute_local(events, delta):
    """Events are (integer seconds, unique secondary order, source, destination)."""
    events = sorted(events)
    result = {n: [0] * 40 for e in events for n in e[2:]}
    for triple in combinations(events, 3):
        if triple[-1][0] - triple[0][0] > delta:
            continue
        edges = [(e[2], e[3]) for e in triple]
        nodes = set(n for edge in edges for n in edge)
        if len(nodes) == 2:
            for node in nodes:
                bits = sum((u == node) << (2-i) for i, (u, v) in enumerate(edges))
                result[node][24 + bits] += 1
        elif len(nodes) == 3:
            common = set(edges[0]).intersection(*map(set, edges[1:]))
            if common:
                center, = common
                leaves = [v if u == center else u for u, v in edges]
                base = 0 if leaves[0] == leaves[1] else (8 if leaves[0] == leaves[2] else 16)
                bits = sum((u == center) << (2-i) for i, (u, v) in enumerate(edges))
                result[center][base + bits] += 1
            else:
                i, j = edges[0]
                k, = nodes - {i, j}
                patterns = [((k,j),(i,k)), ((k,j),(k,i)), ((j,k),(i,k)), ((j,k),(k,i)),
                            ((k,i),(j,k)), ((k,i),(k,j)), ((i,k),(j,k)), ((i,k),(k,j))]
                index = patterns.index(tuple(edges[1:]))
                for node in nodes:
                    result[node][32 + index] += 1
    return result
