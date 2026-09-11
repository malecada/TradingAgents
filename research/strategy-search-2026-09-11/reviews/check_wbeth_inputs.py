"""Independent WBETH saved-source check. No collector imports or network."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
import base64
import json
import subprocess
from check_bitrue_metadata import read, strict, sha, same, clock

ROOT=Path(__file__).resolve().parents[3]
PROGRAM=ROOT/'research/strategy-search-2026-09-11'
RUN=ROOT/'research_runs/wbeth-inputs-20260911'
SOURCE='ea63d7b1aa9176faeddd7640eef09af1a2bdecc5'

def main():
    gate_path=PROGRAM/'gates-wbeth-inputs.json'
    assert sha(gate_path.read_bytes())=='38f0038210d7e368c7bf807473500f1accb723c9741b2ef7e322cb6fa1a0d4ea'
    gate=read(gate_path);exp=gate['experiments']['wbeth-inputs-20260911']
    claim=read(RUN/'claim.json');done=read(RUN/'complete.json')
    assert claim['design_source']==done['source']==SOURCE
    same(claim['experiment'],exp)
    assert done['claim_sha256']==sha((RUN/'claim.json').read_bytes())
    assert done['registration_sha256']==sha(gate_path.read_bytes())
    pinned=dict(exp['source_files'])
    for item in [exp['charter'],*exp['inputs'].values()]:pinned[item['path']]=item['sha256']
    for n,h in exp['runtime_hashes'].items():pinned['tradingagents/research/'+n]=h
    pinned[str(gate_path.relative_to(ROOT))]=sha(gate_path.read_bytes())
    for path,h in pinned.items():
        assert sha((ROOT/path).read_bytes())==h
        assert sha(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT))==h
    output=RUN/'outputs'
    assert set(done['output_sha256'])==set(exp['outputs'])=={p.name for p in output.iterdir()}
    for name,h in done['output_sha256'].items():assert sha((output/name).read_bytes())==h
    spec=read(ROOT/exp['inputs']['request_spec']['path'])
    capture=read(output/'wbeth-capture.json');admission=read(output/'wbeth-admission.json')
    same(capture['request_spec'],spec)
    assert len(capture['requests'])==len(admission['cells'])==2
    bodies=[];previous=None;total=0
    for request,receipt,cell in zip(spec['requests'],capture['requests'],admission['cells']):
        same(receipt,read(output/(request['id']+'-receipt.json')))
        for k,v in request.items():assert receipt[k]==v
        assert receipt['attempted'] is True and receipt['body_complete'] is True and receipt['error'] is None
        assert type(receipt['http_status']) is int and receipt['http_status']==200
        raw=base64.b64decode(receipt['body_base64'],validate=True)
        assert type(receipt['body_bytes']) is int and len(raw)==receipt['body_bytes']<=spec['max_response_bytes']
        assert sha(raw)==receipt['body_sha256']
        start,end=clock(receipt['request_utc']),clock(receipt['retrieval_utc'])
        assert start<=end and (previous is None or previous<=start)
        assert 0<=receipt['elapsed_seconds']<=20
        previous=end;total+=len(raw);bodies.append(strict(raw))
        assert cell['id']==request['id'] and cell['status']=='complete'
    metadata,bars=bodies
    assert isinstance(metadata,dict) and 'code' not in metadata
    assert isinstance(metadata['symbols'],list) and len(metadata['symbols'])==1
    symbol=metadata['symbols'][0]
    for k,v in {'symbol':'WBETHUSDT','baseAsset':'WBETH','quoteAsset':'USDT','status':'TRADING'}.items():assert symbol[k]==v
    assert symbol['isSpotTradingAllowed'] is True
    filters=symbol['filters']
    assert isinstance(filters,list) and filters and all(isinstance(f,dict) and isinstance(f.get('filterType'),str) for f in filters)
    assert len({f['filterType'] for f in filters})==len(filters)
    same(symbol,admission['cells'][0]['symbol_metadata'])
    start_ms=int(datetime(2026,4,1,tzinfo=timezone.utc).timestamp()*1000)
    assert isinstance(bars,list) and len(bars)==91
    zero=[]
    for index,row in enumerate(bars):
        assert isinstance(row,list) and len(row)==12
        assert type(row[0]) is int and type(row[6]) is int
        assert row[0]==start_ms+index*86400000 and row[6]==row[0]+86400000-1
        numbers={}
        for k in (1,2,3,4,5,7,9,10):
            assert type(row[k]) in (str,int,float)
            numbers[k]=Decimal(str(row[k]));assert numbers[k].is_finite() and numbers[k]>=0
            if k in (1,2,3,4):assert numbers[k]>0
        assert numbers[3]<=min(numbers[1],numbers[4])<=max(numbers[1],numbers[4])<=numbers[2]
        assert type(row[8]) is int and row[8]>=0
        if numbers[5]==0 or row[8]==0:zero.append(index)
    barcell=admission['cells'][1]
    for k,v in {'observations':91,'expected_days':91,'start_ms':start_ms,'end_exclusive_ms':start_ms+91*86400000,'row_index_base':0,'zero_activity_row_indices':zero}.items():same(barcell[k],v)
    assert total==capture['total_body_bytes']
    same(done['cells'],[{'id':r['id'],'status':'complete'} for r in spec['requests']])
    assert done['cell_count']==2 and done['unavailable_count']==0 and clock(done['ended_at'])>=previous
    sizes={p.name:p.stat().st_size for p in output.iterdir()}
    assert sum(sizes.values())<=spec['max_output_bytes'] and sizes['wbeth-admission.json']<=spec['max_admission_bytes']
    guard=read(PROGRAM/'reviews/wbeth-resource-execution.json')
    assert guard['child_exit_code']==0 and guard['limit_reason'] is None
    assert guard['elapsed_seconds']<=120 and guard['peak_sampled_tree_rss_bytes']<=512*1024**2
    result={'review':'PASS source schema only','source':SOURCE,'requests':2,'complete':2,'unavailable':0,'bar_rows':91,
      'zero_activity_row_indices':zero,'raw_bytes':total,'output_bytes':sum(sizes.values()),
      'first_request_utc':capture['requests'][0]['request_utc'],'last_retrieval_utc':capture['requests'][-1]['retrieval_utc'],
      'literal_current_filters':filters,'resource':guard,
      'limitations':['Current filters are not historical authority','Trade bars are not executable fills','No return, ratio, hedge quantity, PnL or staking attribution computed']}
    (PROGRAM/'reviews/wbeth-inputs-review.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('literal_current_filters','resource')}))

if __name__=='__main__':main()
