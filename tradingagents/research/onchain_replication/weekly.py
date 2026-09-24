"""Disk-backed event conservation and sparse weekly aggregation.

SQLite owns exact event identities and ordered edge sums; no whole-chain dense
adjacency or silently capped neighborhoods. Empirical callers supply complete
coverage evidence and a resource-guarded scratch volume.
"""
from __future__ import annotations
from collections import Counter
from datetime import timedelta
from pathlib import Path
import math
import sqlite3
import tempfile
import numpy as np
from .contracts import GraphSnapshot,validate_graph
from .provenance import utc,require_hash
from .cache import cache_key


def stamp(value):return value.isoformat().replace('+00:00','Z')


def week_start(timestamp: str,anchor: str) -> str:
    if anchor!='MON':raise ValueError('unsupported week anchor')
    t=utc(timestamp);return stamp((t-timedelta(days=t.weekday())).replace(hour=0,minute=0,second=0,microsecond=0))


def _complete(start,end,coverage):
    cursor=start
    for a,b in sorted((utc(a),utc(b)) for a,b in coverage):
        if b<=a:raise ValueError('invalid coverage interval')
        if a>cursor:break
        if b>cursor:cursor=b
        if cursor>=end:return True
    return False


def build_weekly(events,graph_config,*,coverage,scratch):
    Path(scratch).mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='weekly-',dir=scratch) as directory:
        db=sqlite3.connect(str(Path(directory)/'events.sqlite'))
        try:
            db.execute('PRAGMA cache_size=-32768')
            db.execute('PRAGMA temp_store=FILE')
            db.execute('CREATE TABLE events(asset TEXT,id TEXT,week TEXT,sender TEXT,recipient TEXT,value REAL,category TEXT,source TEXT,PRIMARY KEY(asset,id)) WITHOUT ROWID')
            for e in events:
                require_hash(e.source_hash)
                if e.asset not in ('ETH','BTC') or not isinstance(e.identity,str) or not e.identity:raise ValueError('invalid event identity')
                if not math.isfinite(e.value) or e.value<0:raise ValueError('invalid native value')
                if e.receipt_status not in (0,1):raise ValueError('invalid event status')
                if not isinstance(e.sender,str) or not e.sender:raise ValueError('invalid sender')
                category=('failed' if e.receipt_status==0 else 'null_recipient' if e.recipient is None else 'zero_value' if e.value==0 else 'admitted')
                try:db.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?,?)',(e.asset,e.identity,week_start(e.timestamp,graph_config['week_anchor']),e.sender,e.recipient,e.value,category,e.source_hash))
                except sqlite3.IntegrityError as error:raise ValueError('duplicate transaction identity') from error
            db.commit()
            db.execute('CREATE INDEX week_category ON events(asset,week,category)')
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
                db.execute('DROP TABLE IF EXISTS pairs')
                db.execute("CREATE TEMP TABLE pairs AS SELECT sender,recipient,count(*) AS count,sum(value) AS value FROM (SELECT * FROM events WHERE asset=? AND week=? AND category='admitted' ORDER BY id) GROUP BY sender,recipient",params)
                edges=[];attributes=[];nodes=np.zeros((len(ids),4),dtype=np.float64)
                for sender,recipient,count,value in db.execute('SELECT * FROM pairs ORDER BY sender,recipient'):
                    a,b=node_map[sender],node_map[recipient]
                    edges.append((a,b));attributes.append((count,value))
                    nodes[a,1]+=count;nodes[a,3]+=value;nodes[b,0]+=count;nodes[b,2]+=value
                sources=tuple(r[0] for r in db.execute('SELECT DISTINCT source FROM events WHERE asset=? AND week=? ORDER BY source',params))
                g=GraphSnapshot(asset,start,stamp(end),stamp(end+timedelta(days=1)),sources,cache_key(graph_config),tuple(ids),np.log1p(nodes),np.asarray(edges,dtype=np.int64).reshape(-1,2).T,np.log1p(np.asarray(attributes,dtype=np.float64).reshape(-1,2)),admitted+sum(counts.values()),admitted,counts)
                validate_graph(g)
                yield g
        finally:db.close()
