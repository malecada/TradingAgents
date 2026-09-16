"""Independent retained-byte pilot review. No production numeric/storage imports."""
import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile

import pyarrow as pa
import pyarrow.parquet as pq
import zstandard as zstd
from tradingagents.research.verify import verify_run, verify_claim

HERE = Path(__file__).resolve().parent
COLUMNS = ['hash','block_hash','block_number','block_timestamp','transaction_index',
           'from_address','to_address','value','receipt_status']
HEX = re.compile(r'0x[0-9a-fA-F]{64}\Z')
ADDRESS = re.compile(r'0x[0-9a-fA-F]{40}\Z')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def old_body(record):
    raw = base64.b64decode(record['body_base64'],validate=True)
    assert not record.get('error') and len(raw)==record['bytes'] and sha(raw)==record['sha256']
    return raw


def plain_blob(root, metadata, parent=None):
    relative = metadata['path']
    path = ((parent/relative) if '/' not in relative else root/relative).resolve()
    path.relative_to((root/'research/onchain-graph-2026-09-16/pilot/artifacts').resolve())
    assert not Path(relative).is_absolute() and '..' not in Path(relative).parts
    n = metadata['raw_bytes']; stored_n = metadata['stored_bytes']
    assert type(n) is int and 0 <= n <= 64*1024**2
    assert type(stored_n) is int and 0 <= stored_n <= 65*1024**2
    assert metadata['codec']=='zstd' and metadata['level']==3
    with path.open('rb') as stream:
        compressed = stream.read(stored_n+1)
    assert len(compressed)==stored_n and sha(compressed)==metadata['stored_sha256']
    assert zstd.frame_content_size(compressed)==n
    assert zstd.get_frame_parameters(compressed).has_checksum
    raw = zstd.ZstdDecompressor().decompress(compressed,max_output_size=max(1,n),allow_extra_data=False)
    assert len(raw)==n and sha(raw)==metadata['raw_sha256']
    assert metadata['base64_theoretical_bytes']==4*((n+2)//3)
    return raw


def check_tree(root, manifest, strict=True):
    base = root/'research/onchain-graph-2026-09-16/pilot/artifacts'
    actual = sorted(p for p in base.rglob('*') if p.is_file())
    assert all(not p.is_symlink() for p in base.rglob('*'))
    registered = {r['path']:r for r in manifest['files']}
    assert len(registered)==len(manifest['files'])
    assert set(registered)=={str(p.relative_to(root)) for p in actual}
    assert sum(r['bytes'] for r in registered.values())==manifest['bytes']
    bound = set(); missing_intents=[]
    def visit(value, parent):
        if isinstance(value,dict):
            if {'path','raw_bytes','stored_bytes','raw_sha256','stored_sha256','codec','level'} <= value.keys():
                p = (parent/value['path'] if '/' not in value['path'] else root/value['path']).resolve()
                plain_blob(root,value,parent); bound.add(p)
            for child in value.values():
                visit(child,parent)
        elif isinstance(value,list):
            for child in value:
                visit(child,parent)
    for path in actual:
        row = registered[str(path.relative_to(root))]
        assert path.stat().st_size==row['bytes'] and file_sha(path)==row['sha256']
        if path.suffix=='.json':
            visit(load(path),path.parent)
        if path.name.endswith('-intent.json') and not path.with_name(path.name.replace('-intent.json','.json')).is_file():
            missing_intents.append(str(path.relative_to(root)))
    blobs={p.resolve() for p in actual if p.suffix=='.zst'}
    unbound=sorted(str(p.relative_to(root)) for p in blobs-bound)
    assert bound<=blobs
    if strict:assert not unbound and not missing_intents
    return {'files':len(actual),'bytes':manifest['bytes'],'roundtripped_blobs':len(bound),
            'unbound_blobs':unbound,'unresolved_intents':missing_intents}


class AcquiredOnly(io.RawIOBase):
    """Independent sparse-reader guard: no unacquired interval may be read."""
    def __init__(self, file, spans):
        self.file = file; self.spans = []
        for start,end in sorted(spans):
            if self.spans and start <= self.spans[-1][1]+1:
                self.spans[-1][1] = max(end,self.spans[-1][1])
            else:
                self.spans.append([start,end])
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.file.tell()
    def seek(self,where,whence=0): return self.file.seek(where,whence)
    def read(self,size=-1):
        start = self.tell()
        assert size >= 0 and any(a <= start and start+size <= b+1 for a,b in self.spans)
        return self.file.read(size)
    def readinto(self, buffer):
        raw = self.read(len(buffer)); buffer[:len(raw)] = raw; return len(raw)


def block_rows(raw,start,end):
    frame = pq.read_table(io.BytesIO(raw),columns=['number','hash','parent_hash','timestamp','transaction_count'],use_threads=False)
    rows = sorted(zip(frame['number'].to_pylist(),frame['hash'].to_pylist(),frame['parent_hash'].to_pylist(),
                      frame['timestamp'].cast(pa.int64()).to_pylist(),frame['transaction_count'].to_pylist()))
    seen,heights = set(),set()
    for i,(number,bhash,parent,timestamp,count) in enumerate(rows):
        assert type(number) is int and type(count) is int and count>=0
        assert HEX.fullmatch(bhash) and HEX.fullmatch(parent) and start*10**9<=timestamp<end*10**9
        assert number not in heights and bhash.lower() not in seen
        heights.add(number); seen.add(bhash.lower())
        if i:
            old = rows[i-1]
            assert number==old[0]+1 and parent.lower()==old[1].lower() and timestamp>old[3]
    assert rows and sum(r[4] for r in rows)<=2_000_000
    return rows


def static_summary(pairs):
    indegree,outdegree,in_events,out_events = Counter(),Counter(),Counter(),Counter()
    fingerprint = hashlib.sha256()
    for (a,b),count in sorted(pairs.items()):
        assert a!=b and count>0
        indegree[b]+=1;outdegree[a]+=1;in_events[b]+=count;out_events[a]+=count
        fingerprint.update(f'{a},{b},{count}\n'.encode())
    nodes = indegree.keys()|outdegree.keys(); edges=len(pairs); events=sum(pairs.values())
    reciprocal=sum((b,a) in pairs for a,b in pairs)
    return {'nodes':len(nodes),'directed_pairs':edges,'events':events,'repeated_events':events-edges,
        'repeated_event_fraction':(events-edges)/events if events else None,
        'reciprocal_dyads':reciprocal//2,'reciprocal_directed_pairs':reciprocal,
        'reciprocal_directed_pair_fraction':reciprocal/edges if edges else None,
        'in_degree_histogram':{str(k):v for k,v in sorted(Counter(indegree[n] for n in nodes).items())},
        'out_degree_histogram':{str(k):v for k,v in sorted(Counter(outdegree[n] for n in nodes).items())},
        'in_degree_sum':sum(indegree.values()),'out_degree_sum':sum(outdegree.values()),
        'max_in_degree':max(indegree.values(),default=0),'max_out_degree':max(outdegree.values(),default=0),
        'sender_event_square_sum':sum(v*v for v in out_events.values()),
        'recipient_event_square_sum':sum(v*v for v in in_events.values()),
        'sender_event_hhi':sum(v*v for v in out_events.values())/events**2 if events else None,
        'recipient_event_hhi':sum(v*v for v in in_events.values())/events**2 if events else None,
        'pair_count_sha256':fingerprint.hexdigest()}


def decode_day(plan,footer,blocks,read_range,start,end):
    """Reconstruct all nine columns and independently admit rows; no graph library."""
    rows = block_rows(blocks,start,end)
    block_map={r[0]:(r[1].lower(),r[3],r[4]) for r in rows}
    positions={r[0]:bytearray(r[4]) for r in rows}
    meta = pq.read_metadata(io.BytesIO(b'PAR1'+footer))
    calculated=[]
    for group in range(meta.num_row_groups):
        for col_i in range(meta.row_group(group).num_columns):
            col=meta.row_group(group).column(col_i)
            assert not col.file_path
            if col.path_in_schema not in COLUMNS:continue
            offset=min(v for v in (col.dictionary_page_offset,col.data_page_offset) if v is not None and v>=4)
            calculated.append((group,col.path_in_schema,offset,offset+col.total_compressed_size-1,col.total_compressed_size))
    assert calculated==[(r['group'],r['column'],r['start'],r['end'],r['bytes']) for r in plan['ranges']]
    assert meta.num_rows==plan['rows'] and [meta.row_group(i).num_rows for i in range(meta.num_row_groups)]==plan['groups']
    spans=sorted((r['start'],r['end']) for r in plan['ranges'])
    assert all(a[1]<b[0] for a,b in zip(spans,spans[1:]))
    assert spans[0][0]>=4 and spans[-1][1]<plan['footer_start']==plan['object']['size']-len(footer)
    categories=Counter();flags=Counter();pairs=Counter();events=[];hashes=set();sentinels=inversions=total=0;previous=None
    with tempfile.TemporaryFile() as sparse:
        sparse.truncate(plan['object']['size']);sparse.write(b'PAR1');sparse.seek(plan['footer_start']);sparse.write(footer)
        for i,span in enumerate(plan['ranges']):
            raw=read_range(i);assert len(raw)==span['bytes'];sparse.seek(span['start']);sparse.write(raw)
        sparse.flush()
        reader=AcquiredOnly(sparse,spans+[(0,3),(plan['footer_start'],plan['object']['size']-1)])
        file=pq.ParquetFile(reader,metadata=meta,pre_buffer=False)
        for group,nrows in enumerate(plan['groups']):
            table=file.read_row_group(group,columns=COLUMNS,use_threads=False)
            assert table.num_rows==nrows
            arrays=[(table[n].cast(pa.int64()) if n=='block_timestamp' else table[n]).to_pylist() for n in COLUMNS]
            for tx,bhash,number,timestamp,index,sender,recipient,value,status in zip(*arrays,strict=True):
                total+=1
                assert HEX.fullmatch(tx) and HEX.fullmatch(bhash) and ADDRESS.fullmatch(sender)
                identity=bytes.fromhex(tx[2:]);assert identity not in hashes;hashes.add(identity)
                if recipient=='None':recipient=None;sentinels+=1
                assert recipient is None or ADDRESS.fullmatch(recipient)
                assert type(status) is int and status in (0,1)
                assert type(value) in (int,float) and math.isfinite(value) and value>=0
                assert type(timestamp) is int and start*10**9<=timestamp<end*10**9
                assert type(number) is int and number in block_map
                block=block_map[number];assert bhash.lower()==block[0] and timestamp==block[1]
                assert type(index) is int and 0<=index<block[2] and not positions[number][index]
                positions[number][index]=1
                position=(number,index);inversions+=previous is not None and position<previous;previous=position
                self_transfer=recipient is not None and sender.lower()==recipient.lower()
                flags['failed_receipt']+=status==0;flags['null_recipient']+=recipient is None
                flags['zero_value']+=value==0;flags['self_transfer']+=self_transfer
                category=('reverted' if status==0 else 'null_recipient' if recipient is None else
                          'zero_value' if value==0 else 'self_transfer' if self_transfer else 'graph_event')
                categories[category]+=1
                if category=='graph_event':
                    assert timestamp%10**9==0 and index<2**32
                    event=(timestamp//10**9,(number<<32)|index,sender.lower(),recipient.lower())
                    events.append(event);pairs[event[2:]]+=1
            del arrays,table
    assert total==sum(r[4] for r in rows)==plan['rows'] and all(all(p) for p in positions.values())
    events.sort(key=lambda e:e[1]);assert all(a[0]<=b[0] and a[1]<b[1] for a,b in zip(events,events[1:]))
    fingerprint=hashlib.sha256()
    for event in events:fingerprint.update((json.dumps(event,separators=(',',':'))+'\n').encode())
    integrity={'admitted':True,'rows':total,'expected_rows':total,'missing_block_positions':0,
        'unique_transaction_hashes':len(hashes),'errors':{},'flags_nonexclusive':dict(flags),
        'categories':{k:categories[k] for k in ['invalid','reverted','null_recipient','zero_value','self_transfer','graph_event']},
        'source_order_inversions':inversions,'exact_sentinels_normalized':sentinels,
        'ordered_events_sha256':fingerprint.hexdigest(),'first_block':list(rows[0]),'last_block':list(rows[-1])}
    return events,integrity,static_summary(pairs),hashes


def shard_rows(root,metadata):
    rows=[]
    for item in metadata:
        raw=plain_blob(root,item)
        part=[json.loads(line) for line in raw.splitlines()]
        assert len(part)==item['rows']
        assert raw==b''.join((json.dumps(row,separators=(',',':'))+'\n').encode() for row in part)
        rows.extend(part)
    return rows


def reviewer_math():
    path=HERE.parent/'motifs8gib/check_independent.py'
    assert file_sha(path)=='cfb464b4b6b3c8ab98e5265d885c476f4b49064cd1f0748dc2e92892e73dc98c'
    spec=importlib.util.spec_from_file_location('prior_independent_motif_math',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def verify_counts(root,result,prefix,events,start,end,math_module):
    selected=[e for e in prefix if e[0]>=start-3600]+events
    local=shard_rows(root,result['counts'])
    assert [r[0] for r in local]==sorted({n for e in selected for n in e[2:]})
    before=math_module.two_node(list(prefix));total=math_module.two_node(list(selected))
    isolated=math_module.two_node(list(events))
    sums=[0]*40;squares=[0]*40;maximum=[0]*40;nonzero=[0]*40;active=0;dyad_cross=[0]*8
    for node,values in local:
        assert len(values)==40 and all(type(v) is int and v>=0 for v in values)
        dyads=[a-b for a,b in zip(total.get(node,[0]*8),before.get(node,[0]*8))]
        assert values[24:32]==dyads
        active+=any(values)
        for i,v in enumerate(values):sums[i]+=v;squares[i]+=v*v;maximum[i]=max(maximum[i],v);nonzero[i]+=v>0
        for i,v in enumerate(dyads):dyad_cross[i]+=v-isolated.get(node,[0]*8)[i]
    summary=result['features']
    assert summary['overlap_node_count']==len(local) and summary['nonzero_nodes']==active
    for name,value in [('local40_sums',sums),('local40_square_sums',squares),('local40_maxima',maximum),('local40_nonzero_nodes',nonzero)]:
        assert summary[name]==value,name
    assert summary['local40_top_node_shares']==[a/b if b else None for a,b in zip(maximum,sums)]
    def unique(values):
        assert all(values[24+i]==values[31-i] for i in range(4)) and all(v%3==0 for v in values[32:])
        return sum(values[:24])+sum(values[24:32])//2+sum(values[32:])//3
    assert summary['unique_occurrences']==unique(sums)
    cross=summary['cross_midnight_local40_sums'];assert all(0<=v<=s for v,s in zip(cross,sums))
    assert cross[24:32]==dyad_cross and summary['cross_midnight_unique_occurrences']==unique(cross)
    if 'isolated_day_local40_sums' in summary:
        assert [s-c for s,c in zip(sums,cross)]==summary['isolated_day_local40_sums']
    prior_incidence,current_incidence=Counter(),Counter()
    for t,_,a,b in selected:
        if t<start:prior_incidence.update((a,b))
        elif t<start+3600:current_incidence.update((a,b))
    centers=sorted(prior_incidence.keys()&current_incidence.keys(),key=lambda n:(-min(prior_incidence[n],current_incidence[n]),n))[:3]
    checks=result['checks']['samples'];assert len(checks)==len(centers)
    for row,center in zip(checks,centers):
        sample=[e for e in selected if e[0]<start and center in e[2:]][-15:]+[e for e in selected if start<=e[0]<start+3600 and center in e[2:]][:15]
        assert row['center']==center and row['events']==[list(e) for e in sample] and row['matched']
        all_counts=math_module.brute(sample);old_counts=math_module.brute([e for e in sample if e[0]<start])
        expected={n:[a-b for a,b in zip(v,old_counts.get(n,[0]*40))] for n,v in all_counts.items()}
        assert expected==row['local_counts']
    return {'nodes':len(local),'unique_occurrences':summary['unique_occurrences'],
        'cross_midnight_unique_occurrences':summary['cross_midnight_unique_occurrences'],
        'full_completion_and_cross_midnight_dyads_recounted':True,'bounded_subsets_recounted':len(checks),
        'full_day_star_triangle_recounted':False}


def object_for(inventory,table,day):
    rows=[r for group in inventory['inventories'] for r in group['dates'] if (r['table'],r['date'])==(table,day)]
    assert len(rows)==1 and rows[0]['status']=='complete' and len(rows[0]['objects'])==1
    return rows[0]['objects'][0]


def check_response(record,raw,obj,url,start=None,end=None):
    assert record['url']==url and record['request_headers']['If-Match']==obj['etag']
    assert not record.get('error') and record['response_headers']['etag']==obj['etag']
    if start is None:
        assert record['status']==200 and len(raw)==obj['size'] and 'Range' not in record['request_headers']
    else:
        assert record['status']==206 and record['request_headers']['Range']==f'bytes={start}-{end}'
        assert record['response_headers']['content-range']==f'bytes {start}-{end}/{obj["size"]}'
        assert len(raw)==end-start+1


def phase_receipts(root,phase,started,ended,limits):
    directory=root/'research/onchain-graph-2026-09-16/pilot/artifacts'/f'{phase["mode"]}-{phase["date"]}'
    records=[];total=0;denied=False
    for i,path in enumerate(sorted(directory.glob('request-????.json')),1):
        record=load(path);intent=load(path.with_name(path.stem+'-intent.json'))
        assert record['request_number']==i and intent['request_number']==i and intent['status']=='intent'
        assert intent['method']=='GET' and intent['url']==record['url'] and intent['request_headers']==record['request_headers']
        assert intent['requested_at']==record['requested_at']
        assert started<=datetime.fromisoformat(record['requested_at'])<=datetime.fromisoformat(record['retrieved_at'])<=ended
        raw=plain_blob(root,record['blob'],directory)
        assert len(raw)==record['bytes'] and sha(raw)==record['sha256'] and len(raw)<=limits['max_response_bytes']+1
        if denied:assert record['status'] is None and record.get('error') and not raw
        denied|=record['status'] in (401,403,429)
        total+=len(raw);records.append((record,record['blob'],directory))
    assert total==phase['raw_bytes'] and 0<=phase['requests']<=len(records)
    assert denied==phase['denied']
    if phase['status']=='complete':assert phase['requests']==len(records) and all(not r[0].get('error') for r in records)
    assert phase['requests']<=limits['max_day_requests'] and total<=limits['max_day_bytes']
    return records


def verify_success(root,run,claim,terminal,plan):
    output=lambda n:load(run/'outputs'/n)
    base=root/'research/onchain-graph-2026-09-16/pilot/artifacts'
    inputs=lambda n:load(root/plan['inputs'][n]['path'])
    inventory=inputs(plan['inventory_input'])
    started=datetime.fromisoformat(claim['started_at']);ended=datetime.fromisoformat(terminal['ended_at'])
    assert started<ended
    all_days=['2024-01-01',*plan['dates']]
    statuses={c['id']:c['status'] for c in terminal['cells']}
    context=output('context.json');closing=output('boundary.json')
    phases=[context,closing,*[output(f'source-{day}.json') for day in plan['dates']]]
    observed_requests=observed_bytes=0;denied=False;records_by_day={}
    for phase in phases:
        assert phase['status'] in ('complete','unavailable')
        if phase.get('mode') in ('source','boundary'):
            if denied:assert phase['requests']==0
            records_by_day[phase['date']]=phase_receipts(root,phase,started,ended,plan['limits'])
        observed_requests+=phase.get('requests',0);observed_bytes+=phase.get('raw_bytes',0);denied|=phase.get('denied',False)
        for item in phase.get('artifacts',[]):
            p=root/item['path'];assert p.stat().st_size==item['bytes'] and file_sha(p)==item['sha256']
    root_summary=output('summary.json')
    assert observed_requests==root_summary['requests']<=plan['limits']['max_requests']
    assert observed_bytes==root_summary['raw_bytes']<=plan['limits']['max_total_bytes'] and denied==root_summary['denied']
    assert {r['id']:r['status'] for r in root_summary['cells']}==statuses
    if closing['status']=='complete':
        records=records_by_day['2024-01-09'];assert len(records)==1
        obj=object_for(inventory,'blocks','2024-01-09');record,blob,parent=records[0];raw=plain_blob(root,blob,parent)
        check_response(record,raw,obj,plan['base_url']+obj['key'])
        start=int(datetime(2024,1,9,tzinfo=timezone.utc).timestamp());rows=block_rows(raw,start,start+86400)
        assert closing['integrity']['first_block']==list(rows[0]) and closing['integrity']['last_block']==list(rows[-1])
        assert closing['integrity']['blocks']==len(rows) and not closing['integrity']['transactions_checked']
    math_module=reviewer_math();global_hashes=set();total_rows=0;duplicate_days=[];decoded={};count_reports={};previous_prefix=None
    for day in all_days:
        phase=context if day=='2024-01-01' else output(f'source-{day}.json')
        if phase['status']!='complete':previous_prefix=None;continue
        start=int(datetime.fromisoformat(day+'T00:00:00+00:00').timestamp());end=start+86400
        if day=='2024-01-01':
            old=inputs(plan['context']['plan_input']);footer=old_body(inputs(plan['context']['footer_input']))
            blocks=old_body(inputs(plan['context']['blocks_input']));projection=old
            b=phase['benchmark'];assert b['ranges']==117 and b['roundtrip_verified'] and len(b['blobs'])==117
            totals={'receipt_json_bytes':0,'raw_bytes':0,'base64_theoretical_bytes':0,'zstd_bytes':0}
            for i,name in enumerate(plan['context']['range_inputs']):
                receipt_raw=(root/plan['inputs'][name]['path']).read_bytes();record=json.loads(receipt_raw);raw=old_body(record)
                span=projection['ranges'][i];check_response(record,raw,projection['object'],plan['base_url']+projection['object']['key'],span['start'],span['end'])
                assert plain_blob(root,b['blobs'][i])==raw
                totals['receipt_json_bytes']+=len(receipt_raw);totals['raw_bytes']+=len(raw)
                totals['base64_theoretical_bytes']+=4*((len(raw)+2)//3);totals['zstd_bytes']+=b['blobs'][i]['stored_bytes']
            for key,value in totals.items():assert b[key]==value
            assert b['zstd_to_raw_ratio']==totals['zstd_bytes']/totals['raw_bytes']
            assert b['zstd_to_receipt_json_ratio']==totals['zstd_bytes']/totals['receipt_json_bytes']
            reader=lambda i:plain_blob(root,b['blobs'][i])
        else:
            records=records_by_day[day]
            projection=load(base/f'source-{day}/projection.json')
            block_obj=object_for(inventory,'blocks',day);obj=object_for(inventory,'transactions',day)
            assert projection['object']==obj and len(records)==3+len(projection['ranges'])
            block_record,blob,parent=records[0];blocks=plain_blob(root,blob,parent)
            check_response(block_record,blocks,block_obj,plan['base_url']+block_obj['key'])
            tr,tm,tp=records[1];tail=plain_blob(root,tm,tp);check_response(tr,tail,obj,plan['base_url']+obj['key'],obj['size']-8,obj['size']-1)
            fr,fm,fp=records[2];footer=plain_blob(root,fm,fp)
            check_response(fr,footer,obj,plan['base_url']+obj['key'],obj['size']-len(footer),obj['size']-1)
            assert footer[-8:]==tail and tail[4:]==b'PAR1' and len(footer)==int.from_bytes(tail[:4],'little')+8
            assert len(footer)<=plan['limits']['max_footer_bytes']+8 and len(blocks)<=plan['limits']['max_block_bytes']
            assert projection['rows']<=2_000_000 and len(projection['groups'])<=32 and obj['size']<=plan['limits']['max_logical_bytes']
            assert sum(r['bytes'] for r in projection['ranges'])<=plan['limits']['max_projection_bytes']
            def reader(i):
                record,meta,parent=records[i+3];raw=plain_blob(root,meta,parent);span=projection['ranges'][i]
                check_response(record,raw,obj,plan['base_url']+obj['key'],span['start'],span['end']);return raw
        events,integrity,activity,hashes=decode_day(projection,footer,blocks,reader,start,end)
        for key,value in integrity.items():assert phase['integrity'][key]==value,(day,key)
        for key,value in activity.items():assert phase['activity'][key]==value,(day,key)
        assert shard_rows(root,phase['events'])==[list(e) for e in events]
        prefix=[e for e in events if e[0]>=end-3600]
        assert shard_rows(root,phase['prefix'])==[list(e) for e in prefix]
        hash_bytes=b''.join(plain_blob(root,m) for m in phase['transaction_hashes'])
        assert hash_bytes==b''.join(sorted(hashes)) and len(hash_bytes)==32*integrity['rows']
        if not global_hashes.isdisjoint(hashes):duplicate_days.append(day)
        global_hashes.update(hashes);total_rows+=len(hashes)
        decoded[day]={'integrity':integrity,'activity':activity}
        if day!='2024-01-01':
            counted=output(f'features-{day}.json')
            if counted['status']=='complete':
                assert previous_prefix is not None
                previous_day=(datetime.fromtimestamp(start-86400,timezone.utc)).date().isoformat()
                previous_mode='context' if previous_day=='2024-01-01' else 'source'
                assert counted['source_result_sha256']==file_sha(base/'results'/f'source-{day}.json')
                assert counted['previous_result_sha256']==file_sha(base/'results'/f'{previous_mode}-{previous_day}.json')
                count_reports[day]=verify_counts(root,counted,previous_prefix,events,start,end,math_module)
        previous_prefix=prefix
        del events,hashes,hash_bytes
    unique=output('cross-day-integrity.json')
    assert unique['rows']==total_rows and unique['unique_hashes']==len(global_hashes)
    assert unique['covered_days']==list(decoded) and unique['duplicate_days']==duplicate_days
    assert unique['unavailable_days']==[d for d in all_days if d not in decoded]
    assert unique['all_eight_sources_checked']==(len(decoded)==8)
    assert unique['status']==('unavailable' if duplicate_days else 'complete')
    if duplicate_days:assert not count_reports
    for day in count_reports:
        index=all_days.index(day);before=decoded[all_days[index-1]]['integrity'];current=decoded[day]['integrity']
        following=closing['integrity'] if index==len(all_days)-1 else decoded[all_days[index+1]]['integrity']
        for left,right in ((before,current),(current,following)):
            a,b=left['last_block'],right['first_block']
            assert b[0]==a[0]+1 and b[2].lower()==a[1].lower() and b[3]>a[3]
    assert root_summary['complete_motif_days']==len(count_reports)
    compact=output('features.json');assert not compact['historical_publication_verified'] and not compact['prices_or_targets_opened']
    assert len(compact['days'])==7
    for row,day in zip(compact['days'],plan['dates']):
        expected={k:v for k,v in output(f'features-{day}.json').items() if k not in ('counts','artifacts','checks')}
        assert row==expected
    return {'requests':observed_requests,'raw_bytes':observed_bytes,'decoded_days':decoded,
        'unique_transactions_across_available_days':len(global_hashes),'counted_days':count_reports,
        'baseline_storage':output('storage-benchmark.json'),'complete_motif_days':len(count_reports),
        'full_day_star_triangle_recounted':False}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True)
    parser.add_argument('--source',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();root=Path(args.root).resolve();here=root/'research/onchain-graph-2026-09-16/pilot'
    run=root/'research_runs/eth-seven-day-pilot-20260916'
    assert len(os.sched_getaffinity(0))<=2
    terminals=[p for p in (run/'complete.json',run/'failed.json') if p.exists()]
    assert len(terminals)==1,'Do not inspect empirical artifacts before unique terminal receipt.'
    structural=verify_run(run);claim=verify_claim(run);terminal=load(terminals[0])
    source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    assert source==claim['source']==args.source
    assert claim['family']['prior_attempts']==5 and claim['family']['attempt_budget']==6
    exp=claim['experiment'];assert len(exp['inputs'])==134 and len(exp['source_files'])==27
    for name,digest in exp['source_files'].items():assert file_sha(root/name)==digest
    for name,digest in exp['runtime_hashes'].items():assert file_sha(root/'tradingagents/research'/name)==digest
    for info in claim['inputs'].values():assert file_sha(root/info['path'])==info['sha256']
    history=load(here/'history.json');assert history['local_claim_count']==42
    for name,digest in history['metadata_hashes'].items():assert file_sha(root/name)==digest
    assert len(list((root/'research_runs').glob('*/claim.json')))==43
    resource=load(here/'resource.json')
    assert resource['source']==source and resource['rss_limit_bytes']==8*1024**3 and not resource['elapsed_time_kill']
    plan=load(here/'plan.json')
    if structural['status']=='complete':
        assert structural['cell_count']==17 and structural['output_count']==21
        assert resource['child_exit_code']==0 and resource['limit_reason'] is None
        assert resource['peak_sampled_tree_rss_bytes']<=resource['rss_limit_bytes']
        manifest=load(run/'outputs/manifest.json');tree=check_tree(root,manifest)
        result=verify_success(root,run,claim,terminal,plan)
    else:
        files=[{'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':file_sha(p)}
               for p in sorted((here/'artifacts').rglob('*')) if p.is_file()]
        manifest={'files':files,'bytes':sum(p['bytes'] for p in files)}
        tree=check_tree(root,manifest,strict=False)
        result={'failed_run_evidence_only':True,'numerical_reconstruction_performed':False,
                'observed_partial_artifacts':manifest,'production_terminal_manifest_present':(run/'outputs/manifest.json').exists()}
    result.update(passed=True,source=source,reviewed_at=datetime.now(timezone.utc).isoformat(),
        structural_verification=structural,artifact_verification=tree,execution_resource=resource,
        claim_sha256=file_sha(run/'claim.json'),terminal_sha256=file_sha(terminals[0]),
        gate_sha256=file_sha(here/'gates.json'),reviewer_script_sha256=file_sha(Path(__file__)),
        artifact_manifest_sha256=file_sha(run/'outputs/manifest.json') if (run/'outputs/manifest.json').exists() else None,
        output_sha256={p.name:file_sha(p) for p in sorted((run/'outputs').iterdir())},
        financial_admission=False,historical_availability_verified=False,new_network_requests=0,
        qualification='Independent retained-byte/source/dyad/export reconciliation only. No full-day star/triangle recount, canonical-chain verification, publication-time proof, forecasting or financial evaluation.')
    with Path(args.output).open('x') as stream:json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps({'passed':True,'status':structural['status'],'artifact_files':tree['files'],
                      'complete_motif_days':result.get('complete_motif_days')}))


if __name__=='__main__':main()
