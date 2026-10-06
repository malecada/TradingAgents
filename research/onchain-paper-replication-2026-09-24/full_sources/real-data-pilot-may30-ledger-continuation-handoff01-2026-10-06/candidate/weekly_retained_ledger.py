"""Original post-ingestion weekly method on an externally authenticated read-only DB.
No decoding, sampling, source ingestion, or main-database mutation.
"""
from datetime import timedelta
import numpy as np
from .contracts import GraphSnapshot,validate_graph
from .provenance import utc
from .cache import cache_key
from .weekly import stamp,week_start,_complete

def graphs_from_ledger(db,graph_config,coverage):
    observed=db.execute('SELECT DISTINCT asset,week FROM events ORDER BY asset,week').fetchall()
    if not observed:raise ValueError('empty source stream')
    expected_weeks=set()
    for first,last in coverage:
        cursor=utc(week_start(first,graph_config['week_anchor']))
        while cursor<utc(last):
            end=cursor+timedelta(days=7)
            if _complete(cursor,end,coverage):expected_weeks.add(stamp(cursor))
            cursor=end
    for asset in {a for a,w in observed}:
        missing=expected_weeks-{w for a,w in observed if a==asset}
        if missing:raise ValueError('empty expected week: '+','.join(sorted(missing)))
    for asset,start in observed:
        end=utc(start)+timedelta(days=7)
        if not _complete(utc(start),end,coverage):raise ValueError('complete week coverage required: '+start)
        params=(asset,start)
        counts=dict(db.execute('SELECT category,count(*) FROM events WHERE asset=? AND week=? GROUP BY category',params))
        admitted=counts.pop('admitted',0)
        ids=[r[0] for r in db.execute("SELECT sender FROM events WHERE asset=? AND week=? AND category='admitted' UNION SELECT recipient FROM events WHERE asset=? AND week=? AND category='admitted' ORDER BY 1",params+params)]
        node_map={v:i for i,v in enumerate(ids)}
        # Ordered identity scan makes value accumulation reproducible; SQLite
        # sums are floating-point under the declared source precision.
        db.execute('DROP TABLE IF EXISTS temp.pairs')
        db.execute("CREATE TEMP TABLE pairs AS SELECT sender,recipient,count(*) AS count,sum(value) AS value FROM (SELECT * FROM events WHERE asset=? AND week=? AND category='admitted' ORDER BY id) GROUP BY sender,recipient",params)
        edges=[];attributes=[];nodes=np.zeros((len(ids),4),dtype=np.float64)
        for sender,recipient,count,value in db.execute('SELECT * FROM pairs ORDER BY sender,recipient'):
            a,b=node_map[sender],node_map[recipient]
            edges.append((a,b));attributes.append((count,value))
            nodes[a,1]+=count;nodes[a,3]+=value;nodes[b,0]+=count;nodes[b,2]+=value
        sources=tuple(r[0] for r in db.execute('SELECT DISTINCT source FROM events WHERE asset=? AND week=? ORDER BY source',params))
        g=GraphSnapshot(asset,start,stamp(end),stamp(end+timedelta(days=1)),sources,cache_key(graph_config),tuple(ids),np.log1p(nodes),np.asarray(edges,dtype=np.int64).reshape(-1,2).T,np.log1p(np.asarray(attributes,dtype=np.float64).reshape(-1,2)),admitted+sum(counts.values()),admitted,counts,np.asarray(attributes,dtype=np.float64).reshape(-1,2))
        validate_graph(g)
        yield g
