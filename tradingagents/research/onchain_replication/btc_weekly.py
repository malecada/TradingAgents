"""Disk-backed BTC graph assembly with exact projection and value sidecars.

Inputs are normalized transactions plus source-resolved prevouts. The caller must
admit the source decoder and complete coverage first. Duplicate spends and
overlapping prevout values are checked across the entire supplied stream before
any graph is yielded. This is not proof of unobserved chain history.
"""
from dataclasses import dataclass
from datetime import timedelta
from fractions import Fraction
from pathlib import Path
import json
import sqlite3
import tempfile
import numpy as np
from .btc import project_transaction, _amount
from .cache import cache_key
from .contracts import GraphSnapshot, validate_graph
from .provenance import require_hash, utc
from .weekly import week_start, stamp, _complete


@dataclass(frozen=True)
class ExactBTCGraph:
    graph: GraphSnapshot
    edge_satoshis: tuple[Fraction, ...]
    incident_satoshis: tuple[Fraction, ...]
    fee_satoshis: int


def _bind_output(db, key, output):
    _amount(output)
    payload=json.dumps({'address':output.get('address'),'satoshis':output['satoshis']},sort_keys=True)
    old=db.execute('SELECT payload FROM outputs WHERE txid=? AND vout=?',key).fetchone()
    if old is not None and old[0]!=payload:raise ValueError('conflicting observed prevout value/address')
    if old is None:db.execute('INSERT INTO outputs VALUES(?,?,?)',(*key,payload))


def build_btc_weekly(events, graph_config, *, coverage, scratch):
    """Yield complete weeks; no fractional transfers are rounded to satoshis.

    Per-edge counts count contributing transactions after same-address merging.
    Fees retain integer satoshis, including known excluded nonunique-script
    transactions. Exact sidecars follow the graph node/edge order.
    """
    coverage=tuple(coverage)
    intervals=tuple((utc(a),utc(b)) for a,b in coverage)
    if not intervals or any(b<=a for a,b in intervals):raise ValueError('invalid coverage')
    Path(scratch).mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='btc-weekly-',dir=scratch) as directory:
        db=sqlite3.connect(str(Path(directory)/'ledger.sqlite'))
        try:
            db.execute('PRAGMA cache_size=-32768');db.execute('PRAGMA temp_store=FILE')
            db.executescript('''
                CREATE TABLE transactions(id TEXT PRIMARY KEY,week TEXT,status TEXT,source TEXT,fee INTEGER,output_count INTEGER);
                CREATE TABLE spent(txid TEXT,vout INTEGER,PRIMARY KEY(txid,vout)) WITHOUT ROWID;
                CREATE TABLE outputs(txid TEXT,vout INTEGER,payload TEXT,PRIMARY KEY(txid,vout)) WITHOUT ROWID;
                CREATE TABLE transfers(week TEXT,sender TEXT,recipient TEXT,id TEXT,numerator TEXT,denominator TEXT);
            ''')
            for event in events:
                source=event['source_hash'];require_hash(source)
                transaction=event['transaction'];require_hash(transaction['id'])
                timestamp=utc(event['timestamp'])
                if not any(a<=timestamp<b for a,b in intervals):raise ValueError('transaction outside admitted coverage')
                week=week_start(event['timestamp'],graph_config['week_anchor'])
                if db.execute('SELECT 1 FROM transactions WHERE id=?',(transaction['id'],)).fetchone():raise ValueError('duplicate transaction identity')
                if transaction['coinbase'] is False:
                    for item in transaction['inputs']:
                        key=(item['txid'],item['vout'])
                        require_hash(key[0])
                        if type(key[1]) is not int or key[1]<0:raise ValueError('invalid prevout index')
                        if key[0]==transaction['id']:raise ValueError('self-referencing transaction')
                        try:db.execute('INSERT INTO spent VALUES(?,?)',key)
                        except sqlite3.IntegrityError as error:raise ValueError('duplicate spent prevout across source stream') from error
                        if key not in event['prevouts']:raise ValueError('unavailable prevout')
                        _bind_output(db,key,event['prevouts'][key])
                for index,output in enumerate(transaction['outputs']):_bind_output(db,(transaction['id'],index),output)
                result=project_transaction(transaction,event['prevouts'])
                db.execute('INSERT INTO transactions VALUES(?,?,?,?,?,?)',(result.transaction_id,week,result.status,source,result.fee_satoshis,len(transaction['outputs'])))
                db.executemany('INSERT INTO transfers VALUES(?,?,?,?,?,?)',
                    ((week,a,b,result.transaction_id,str(value.numerator),str(value.denominator)) for (a,b),value in result.edges.items()))
            db.commit()
            if db.execute('SELECT 1 FROM spent JOIN transactions ON spent.txid=transactions.id WHERE spent.vout>=transactions.output_count LIMIT 1').fetchone():raise ValueError('prevout index absent from observed creator transaction')
            db.execute('CREATE INDEX edge_order ON transfers(week,sender,recipient,id)')
            observed={x[0] for x in db.execute('SELECT DISTINCT week FROM transactions')}
            if not observed:raise ValueError('empty source stream')
            expected=set()
            for first,last in coverage:
                cursor=utc(week_start(first,graph_config['week_anchor']))
                while cursor<utc(last):
                    if _complete(cursor,cursor+timedelta(days=7),coverage):expected.add(stamp(cursor))
                    cursor+=timedelta(days=7)
            if expected-observed:raise ValueError('empty expected week: '+','.join(sorted(expected-observed)))
            if observed-expected:raise ValueError('complete week coverage required: '+','.join(sorted(observed-expected)))
            for start in sorted(observed):
                import itertools
                counts=dict(db.execute('SELECT status,count(*) FROM transactions WHERE week=? GROUP BY status',(start,)))
                admitted=counts.pop('admitted',0)
                ids=tuple(x[0] for x in db.execute('SELECT sender FROM transfers WHERE week=? UNION SELECT recipient FROM transfers WHERE week=? ORDER BY 1',(start,start)))
                positions={node:i for i,node in enumerate(ids)}
                node_counts=np.zeros((len(ids),2),dtype=np.int64)
                node_volumes=[[Fraction(0),Fraction(0)] for _ in ids]
                edges=[];weights=[];exact=[]
                cursor=db.execute('SELECT sender,recipient,numerator,denominator FROM transfers WHERE week=? ORDER BY sender,recipient,id',(start,))
                for (sender,recipient),rows in itertools.groupby(cursor,lambda row:row[:2]):
                    value=Fraction(0);count=0
                    for _,_,numerator,denominator in rows:value+=Fraction(int(numerator),int(denominator));count+=1
                    a,b=positions[sender],positions[recipient]
                    edges.append((a,b));exact.append(value);weights.append((count,float(value/100000000)))
                    node_counts[a,1]+=count;node_counts[b,0]+=count
                    node_volumes[a][1]+=value;node_volumes[b][0]+=value
                features=np.zeros((len(ids),4));features[:,:2]=node_counts
                for i,(incoming,outgoing) in enumerate(node_volumes):features[i,2:]=float(incoming/100000000),float(outgoing/100000000)
                end=utc(start)+timedelta(days=7)
                sources=tuple(x[0] for x in db.execute('SELECT DISTINCT source FROM transactions WHERE week=? ORDER BY source',(start,)))
                weights=np.asarray(weights,dtype=np.float64).reshape(-1,2)
                graph=GraphSnapshot('BTC',start,stamp(end),stamp(end+timedelta(days=1)),sources,cache_key(graph_config),ids,np.log1p(features),np.asarray(edges,dtype=np.int64).reshape(-1,2).T,np.log1p(weights),admitted+sum(counts.values()),admitted,counts,weights)
                validate_graph(graph)
                fee=sum(row[0] for row in db.execute('SELECT fee FROM transactions WHERE week=? AND fee IS NOT NULL',(start,)))
                yield ExactBTCGraph(graph,tuple(exact),tuple(a+b for a,b in node_volumes),fee)
        finally:db.close()
