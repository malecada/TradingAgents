"""Prospective metadata and file-stat preparation; never opens empirical bodies."""
from pathlib import Path
import datetime
import hashlib
import json
import math
import subprocess
ROOT=Path.cwd();HERE=Path(__file__).resolve().parent
BASE=ROOT/'research/onchain-paper-replication-2026-09-24'

def sha(p):
    assert p.is_file() and not p.is_symlink() and p.stat().st_size<2_000_000
    return hashlib.sha256(p.read_bytes()).hexdigest()

def ref(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}

def pages(spans):
    total=0;end=0
    for a,b in sorted((s['start']//4096,(s['end']+4095)//4096) for s in spans):
        assert 0<=a<b
        total+=max(0,b-max(a,end));end=max(end,b)
    return total*4096

def write(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')

def main():
    index_path=BASE/'pilot_successor_02/source-index.json'
    assert sha(index_path)=='18f2548bdec2602995935d951075162537b6369b8bf18647cdc7a96962cffc1a'
    index=json.loads(index_path.read_bytes())
    old=BASE/'full_sources/graph-successor-07-2026-09-30'
    prior=json.loads((old/'metadata-preparation.json').read_bytes())
    # Confirm the page-union rule against every previously reviewed March day.
    for day in prior['days']:
        mapping=ROOT/day['mapping']['path'];assert sha(mapping)==day['mapping']['sha256']
        assert pages(json.loads(mapping.read_bytes())['spans'])==day['projected_page_bytes']
    projection=json.loads((old/'storage-projection.json').read_bytes())
    result={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'source_index':ref(index_path),'projection_reference':ref(old/'storage-projection.json'),
            'page_rule_reference':ref(old/'metadata-preparation.json'),
            'scope':'Compact mappings and original raw file stat only; no raw body, array, SQLite, price or remote read. No registration, claim or release.',
            'weeks':{}}
    for week in ('2024-08-05','2024-12-23'):
        source=index['weeks'][week];assert source['expected_members']==7 and len(source['members'])==7
        directory=HERE/week;directory.mkdir(exist_ok=False)
        days=[];previous=week+'T00:00:00Z'
        for i,member in enumerate(source['members']):
            assert member['start_utc']==previous
            start=datetime.datetime.fromisoformat(member['start_utc'].replace('Z','+00:00'))
            stop=datetime.datetime.fromisoformat(member['end_utc'].replace('Z','+00:00'))
            assert stop-start==datetime.timedelta(days=1);previous=member['end_utc']
            mapping=Path(member['path']);assert sha(mapping)==member['sha256']
            body=json.loads(mapping.read_bytes());spans=body['spans']
            for span in spans:
                p=Path(span['path']);assert p.is_file() and not p.is_symlink() and p.stat().st_size==span['stored_bytes']
                assert 0<=span['start']<span['end']<=body['size'] and span['raw_bytes']==span['end']-span['start']
            wrapper={k:member[k] for k in ('start_utc','end_utc','expected_rows')}
            wrapper.update(status='complete',expected_members=1,members=[member])
            write(directory/f'source-{i:02d}.json',wrapper)
            days.append({'day':member['start_utc'],'rows':member['expected_rows'],'mapping':ref(mapping),
                         'spans':len(spans),'stored_bytes':sum(s['stored_bytes'] for s in spans),'projected_page_bytes':pages(spans)})
        rows=sum(d['rows'] for d in days);assert rows==source['expected_rows'] and previous==source['end_utc']
        peak=math.ceil(rows*projection['synthetic_sampled_peak_allocated_bytes']/projection['synthetic_rows'])
        margin=math.ceil(peak*projection['planning_margin_fraction'])
        page=max(d['projected_page_bytes'] for d in days)
        incremental=peak+margin+page+projection['extra_metadata_guard_reserve_bytes']
        estimate={k:projection[k] for k in ('schema_version','synthetic_result','synthetic_rows','synthetic_sampled_peak_allocated_bytes','planning_margin_fraction','extra_metadata_guard_reserve_bytes','disk_floor_bytes')}
        estimate.update(target_rows=rows,projected_peak_bytes=peak,planning_margin_bytes=margin,projected_parquet_page_bytes=page,
                        projected_incremental_disk_requirement_bytes=incremental,required_free_at_launch_bytes=incremental+projection['disk_floor_bytes'],
                        qualification='Prior reviewed synthetic scaling and 30 percent margin; not a proven full-size peak bound or current free-space claim. Fresh capacity and finite runtime guard required.')
        write(directory/'storage-projection.json',estimate)
        plan=json.loads((old/'graph-plan.json').read_bytes());plan['coverage']=[[week+'T00:00:00Z',previous]];plan['expected_weeks']=[week+'T00:00:00Z']
        write(directory/'graph-plan.json',plan)
        result['weeks'][week]={'days':days,'total_rows':rows,'total_spans_stat_only':sum(d['spans'] for d in days),'required_free_at_launch_bytes':estimate['required_free_at_launch_bytes']}
    write(HERE/'metadata.json',result)
    print(json.dumps({k:{n:v[n] for n in ('total_rows','total_spans_stat_only','required_free_at_launch_bytes')} for k,v in result['weeks'].items()},indent=2))
if __name__=='__main__':main()
