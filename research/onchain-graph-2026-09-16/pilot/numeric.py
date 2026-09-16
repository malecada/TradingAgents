"""Count-only daily integrity and completion-window features; no market data."""
from collections import Counter
import gc
import hashlib
import importlib.util
import io
from itertools import combinations
import json
from pathlib import Path
import tempfile
import time

import pyarrow as pa
import pyarrow.parquet as pq

HERE=Path(__file__).resolve().parent


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


prototype=load('pilot_original_projection',HERE.parent/'prototype/run.py')
boundary=load('pilot_boundary',HERE.parent/'panel_readiness/boundary.py')
oracle=load('pilot_oracle',HERE.parent/'motifs/oracle.py')
COLUMNS=['hash','block_hash','block_number','block_timestamp','transaction_index',
         'from_address','to_address','value','receipt_status']


def projection(obj,footer,limits,required_types):
    meta=pq.read_metadata(io.BytesIO(b'PAR1'+footer))
    if obj['size']>limits['max_logical_bytes'] or len(footer)>limits['max_footer_bytes']+8:
        raise ValueError('logical object/footer bound exceeded')
    if not 0<meta.num_rows<=2_000_000 or not 0<meta.num_row_groups<=32:
        raise ValueError('row or row-group limit exceeded')
    schema={f.name:str(f.type) for f in meta.schema.to_arrow_schema()}
    if any(schema.get(k)!=v for k,v in required_types.items()):raise ValueError('required schema changed')
    ranges=[]
    for group in range(meta.num_row_groups):
        rg=meta.row_group(group)
        for j in range(rg.num_columns):
            col=rg.column(j)
            if col.file_path:raise ValueError('external column reference')
            if col.path_in_schema not in COLUMNS:continue
            offsets=[x for x in [col.dictionary_page_offset,col.data_page_offset] if x is not None and x>=4]
            if not offsets or col.total_compressed_size<=0:raise ValueError('invalid column offsets')
            begin=min(offsets);end=begin+col.total_compressed_size-1
            if end>=obj['size']-len(footer):raise ValueError('column overlaps footer')
            ranges.append({'group':group,'column':col.path_in_schema,'start':begin,'end':end,'bytes':col.total_compressed_size})
    if len(ranges)!=meta.num_row_groups*9:raise ValueError('column denominator differs')
    ordered=sorted(ranges,key=lambda r:r['start'])
    if any(a['end']>=b['start'] for a,b in zip(ordered,ordered[1:])):raise ValueError('overlapping columns')
    if sum(r['bytes'] for r in ranges)>limits['max_projection_bytes'] or any(r['bytes']>limits['max_response_bytes'] for r in ranges):
        raise ValueError('projection exceeds fixed byte allowance')
    return {'object':obj,'rows':meta.num_rows,'groups':[meta.row_group(i).num_rows for i in range(meta.num_row_groups)],
            'columns':COLUMNS,'footer_start':obj['size']-len(footer),'ranges':ranges}


def decode(plan,footer,blocks,read_range,start,end,hash_sink=None):
    block_list=list(prototype.block_rows(blocks))
    state=prototype.math.Integrity(block_list,start*10**9,end*10**9)
    ordered_blocks=sorted(block_list)
    events=[];normalized=0
    with tempfile.TemporaryFile() as sparse:
        sparse.truncate(plan['object']['size']);sparse.write(b'PAR1')
        sparse.seek(plan['footer_start']);sparse.write(footer)
        for i,span in enumerate(plan['ranges']):
            body=read_range(i)
            if len(body)!=span['bytes']:raise ValueError('projected body length changed')
            sparse.seek(span['start']);sparse.write(body)
        sparse.flush()
        reader=prototype.AcquiredReader(sparse,[(r['start'],r['end']) for r in plan['ranges']]+[(0,3),(plan['footer_start'],plan['object']['size']-1)])
        meta=pq.read_metadata(io.BytesIO(b'PAR1'+footer))
        parquet=pq.ParquetFile(reader,metadata=meta,pre_buffer=False)
        for group,rows in enumerate(plan['groups']):
            frame=parquet.read_row_group(group,columns=COLUMNS,use_threads=False)
            if frame.num_rows!=rows:raise ValueError('row count changed')
            cols=[(frame[n].cast(pa.int64()) if n=='block_timestamp' else frame[n]).to_pylist() for n in COLUMNS]
            for row in zip(*cols,strict=True):
                if row[6]=='None':row=(*row[:6],None,*row[7:]);normalized+=1
                before=state.categories['graph_event'];state.add(row)
                if state.categories['graph_event']>before:
                    if row[3]%10**9 or row[4]>=2**32:raise ValueError('timestamp or stable order ID invalid')
                    events.append((row[3]//10**9,(row[2]<<32)|row[4],row[5].lower(),row[6].lower()))
            del cols,frame
    integrity=state.finish()
    if not integrity['admitted']:raise ValueError('row integrity failed: '+json.dumps(integrity))
    if hash_sink is not None:hash_sink(sorted(state.seen_hashes))
    activity=prototype.math.graph_features(state.pairs)
    events.sort(key=lambda e:e[1])
    if any(a[0]>b[0] or a[1]>=b[1] for a,b in zip(events,events[1:])):raise ValueError('event order or clock changed')
    order_hash=hashlib.sha256()
    for event in events:order_hash.update((json.dumps(event,separators=(',',':'))+'\n').encode())
    integrity.update(exact_sentinels_normalized=normalized,ordered_events_sha256=order_hash.hexdigest(),
        stable_event_id='(block_number << 32) | transaction_index',
        first_block=list(ordered_blocks[0]),last_block=list(ordered_blocks[-1]))
    return events,integrity,activity


def linked(previous,current):
    if current[0]!=previous[0]+1 or current[2].lower()!=previous[1].lower() or current[3]<=previous[3]:
        raise ValueError('cross-day block-number, parent-hash or clock discontinuity')


def bounded_checks(events,start,end,delta):
    before,after=Counter(),Counter()
    for t,_,a,b in events:
        counter=before if t<start else after if t<start+delta else None
        if counter is not None:counter.update((a,b))
    centers=sorted(before.keys()&after.keys(),key=lambda n:(-min(before[n],after[n]),n))[:3]
    results=[]
    for center in centers:
        prior=[e for e in events if e[0]<start and center in e[2:]][-15:]
        current=[e for e in events if start<=e[0]<start+delta and center in e[2:]][:15]
        sample=prior+current
        actual=boundary.completion_window(sample,start=start,end=end,delta=delta,coverage_start=start-delta,coverage_end=end)['local_counts']
        expected={n:[0]*40 for e in sample for n in e[2:]}
        for triple in combinations(sample,3):
            if triple[-1][0]<start or triple[-1][0]-triple[0][0]>delta:continue
            for node,counts in oracle.brute_local(triple,delta).items():
                expected[node]=[a+b for a,b in zip(expected[node],counts,strict=True)]
        if actual!=expected:raise ValueError('bounded completion-time oracle differs')
        results.append({'center':center,'events':sample,'matched':True,'local_counts':expected})
    return {'selection':'top3 boundary addresses by minimum prior/following-hour incidence, address tie-break; last15 prior and first15 following events',
            'samples':results,'qualification':'Induced subsets only; not full-day recounts.'}


def summarize_rows(local,day_only):
    sums=[0]*40;squares=[0]*40;maxima=[0]*40;nonzero=[0]*40;cross=[0]*40;active=0
    for node,row in local.items():
        old=day_only.get(node,[0]*40)
        if len(row)!=40 or any(type(v)is not int or v<0 for v in row):raise ValueError('invalid Local40 row')
        if any(a<b for a,b in zip(row,old,strict=True)):raise ValueError('completion counts smaller than isolated day')
        active+=any(row)
        for i,n in enumerate(row):
            sums[i]+=n;squares[i]+=n*n;maxima[i]=max(maxima[i],n);nonzero[i]+=n>0;cross[i]+=n-old[i]
    def unique(values):
        if any(values[24+i]!=values[31-i] for i in range(4)) or any(n%3 for n in values[32:]):raise ValueError('motif role conservation failed')
        return sum(values[:24])+sum(values[24:32])//2+sum(values[32:])//3
    return {'overlap_node_count':len(local),'nonzero_nodes':active,'local40_sums':sums,'local40_square_sums':squares,
            'local40_maxima':maxima,'local40_nonzero_nodes':nonzero,'local40_top_node_shares':[m/s if s else None for m,s in zip(maxima,sums)],
            'isolated_day_local40_sums':[s-c for s,c in zip(sums,cross)],'unique_occurrences':unique(sums),'cross_midnight_local40_sums':cross,'cross_midnight_unique_occurrences':unique(cross)}


def count_day(prefix,events,start,end):
    begin=time.monotonic();selected=[e for e in prefix if e[0]>=start-3600]+events
    checks=bounded_checks(selected,start,end,3600);checked=time.monotonic()
    complete=boundary.completion_window(selected,start=start,end=end,delta=3600,coverage_start=start-3600,coverage_end=end)
    counted=time.monotonic();gc.collect()
    isolated=boundary.local(events,3600);isolated_at=time.monotonic()
    summary=summarize_rows(complete['local_counts'],isolated)
    return complete['local_counts'],summary,checks,{'bounded_checks_seconds':checked-begin,
        'completion_count_seconds':counted-checked,'isolated_day_count_seconds':isolated_at-counted,
        'summary_seconds':time.monotonic()-isolated_at}
