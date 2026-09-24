"""Map existing retained ETH metadata, without decoding/refetching raw bodies."""
from datetime import date,timedelta
from pathlib import Path
import importlib.util,json,sys
from tradingagents.research.lifecycle import _immutable
from tradingagents.research.onchain_replication.resources import assert_guarded_worker
from tradingagents.research.onchain_replication.provenance import file_hash,durable_mkdir,sync_directory

ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
STUDY=HERE.parent;OUTPUT=HERE/'retained-ETH-2022-2024-01'


def main():
    assert_guarded_worker(HERE/'retained-eth-metadata-01-guard',sys.orig_argv,required_paths=[ROOT,Path('/home/malecada/Data')],wall_seconds=600,memory_max_bytes=512*1024**2,memory_high_bytes=384*1024**2)
    helper=STUDY/'prepare_pilot_sources.py';helper_hash=file_hash(helper)
    spec=importlib.util.spec_from_file_location('retained_source_mapping',helper);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    legacy=ROOT/'research/onchain-graph-2026-09-16/fullpanel/plan.json'
    plan=module.load(legacy,'19f3716454216afc172aec2939a9908ba3b57921e99249951e1860b995d1d691')
    OUTPUT.mkdir(exist_ok=False);sync_directory(OUTPUT.parent);durable_mkdir(OUTPUT/'maps')
    _immutable(OUTPUT/'intent.json',{'operation':'read retained metadata and stat existing blobs only',
        'legacy_plan_sha256':file_hash(legacy),'helper_sha256':helper_hash,'script_sha256':file_hash(Path(__file__)),
        'transaction_bodies_decoded':0,'source_requests':0,'historical_job_relaunch':False})
    days={};current=date(2022,1,1);end=date(2025,1,1)
    while current<end:
        day=current.isoformat();row={'date':day,'status':'unavailable'}
        try:
            rows=plan['expected_rows'][day]
            mapping=module.special(rows) if day=='2024-01-01' else module.ordinary(plan['captures'][day],day,rows)
            path=OUTPUT/'maps'/(day+'.json');_immutable(path,mapping)
            row.update(status='retained_metadata_verified',member={'path':str(path),'sha256':file_hash(path),
                'format':'projected_zstd','expected_rows':rows,'start_utc':day+'T00:00:00Z',
                'end_utc':(current+timedelta(days=1)).isoformat()+'T00:00:00Z'},
                retained_blob_bytes=sum(s['stored_bytes'] for s in mapping['spans']))
        except (ValueError,KeyError,OSError) as error:row['reason']=type(error).__name__+': '+str(error)
        _immutable(OUTPUT/(day+'.json'),row);days[day]=row;current+=timedelta(days=1)
    weeks={};current=date(2022,1,3);used=set()
    while current+timedelta(days=7)<=end:
        dates=[(current+timedelta(days=i)).isoformat() for i in range(7)];used.update(dates)
        members=[days[d]['member'] for d in dates if days[d]['status']=='retained_metadata_verified']
        weeks[current.isoformat()]={'start_utc':current.isoformat()+'T00:00:00Z',
            'end_utc':(current+timedelta(days=7)).isoformat()+'T00:00:00Z','expected_members':7,
            'members':members,'expected_rows':sum(plan['expected_rows'][d] for d in dates),
            'status':'complete' if len(members)==7 else 'unavailable'}
        current+=timedelta(days=7)
    if len(days)!=1096 or len(weeks)!=156 or len(used)!=1092:raise ValueError('full retained calendar denominator differs')
    if file_hash(helper)!=helper_hash or file_hash(legacy)!=plan_hash(OUTPUT):raise ValueError('source mapping metadata changed')
    _immutable(OUTPUT/'source-index.json',{'schema_version':1,'asset':'ETH','dates':days,'weeks':weeks,
        'expected_schema':plan['required_types'],'boundary_exclusions':[{'date':d,'reason':'outside a complete Monday UTC week in retained2022–2024 source window'} for d in sorted(set(days)-used)],
        'transaction_data_admitted':False,'qualification':'retained metadata/declared sizes verified only; complete week status means seven mapped members, not newly decoded/admitted transaction rows',
        'total_declared_rows':sum(plan['expected_rows'].values()),
        'retained_blob_bytes':sum(x.get('retained_blob_bytes',0) for x in days.values()),
        'complete_mapped_weeks':sum(w['status']=='complete' for w in weeks.values())})
    _immutable(OUTPUT/'complete.json',{'days':len(days),'weeks':len(weeks),'mapped_days':sum(x['status']=='retained_metadata_verified' for x in days.values()),'index_sha256':file_hash(OUTPUT/'source-index.json'),'transaction_bodies_decoded':0,'source_requests':0})
    print((OUTPUT/'complete.json').read_text(),flush=True)


def plan_hash(output):return json.loads((output/'intent.json').read_bytes())['legacy_plan_sha256']


if __name__=='__main__':main()
