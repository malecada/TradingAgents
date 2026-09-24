"""Metadata-only mapping of retained sources; never decodes transaction bodies."""
from pathlib import Path
from datetime import date,timedelta
import json
import re
from tradingagents.research.onchain_replication.provenance import file_hash,canonical_bytes,digest

ROOT=Path(__file__).resolve().parents[2]
STUDY=Path(__file__).resolve().parent


def load(path,expected=None):
    path=Path(path);raw=path.read_bytes()
    if expected is not None and digest(raw)!=expected:raise ValueError('metadata hash mismatch '+str(path))
    return json.loads(raw)


def span(blob,start,end,base):
    path=base/blob['path']
    if path.stat().st_size!=blob['stored_bytes']:raise ValueError('stored size differs')
    if blob['raw_bytes']!=end-start or blob['codec']!='zstd':raise ValueError('range framing differs')
    return {'path':str(path),'start':start,'end':end,**{k:blob[k] for k in ('raw_bytes','raw_sha256','stored_bytes','stored_sha256','codec')}}


def ordinary(entry,day,expected_rows):
    manifest=load(ROOT/entry['manifest']['path'],entry['manifest']['sha256'])
    if manifest['status']!='complete' or manifest['date']!=day:raise ValueError('incomplete source')
    directory=Path(entry['directory']);files={f['path']:f for f in manifest['files']}
    def read(name):return load(directory/name,files[name]['sha256'])
    projection=read('projection.json');obj=projection['object'];spans=[]
    requests={}
    for name in files:
        if re.fullmatch(r'request-\d+\.json',name):
            receipt=read(name)
            if receipt['url'].endswith(obj['key']) and receipt['status']==206:
                a,b=map(int,receipt['request_headers']['Range'].removeprefix('bytes=').split('-'))
                if receipt['request_headers'].get('If-Match')!=obj['etag'] or receipt['response_headers']['etag']!=obj['etag']:raise ValueError('object ETag differs')
                if (a,b+1) in requests:raise ValueError('duplicate range')
                requests[(a,b+1)]=receipt
    ranges=[(r['start'],r['end']+1) for r in projection['ranges']]+[(projection['footer_start'],obj['size'])]
    for a,b in ranges:
        receipt=requests[(a,b)];blob=receipt['blob'];registered=files[blob['path']]
        if registered['sha256']!=blob['stored_sha256'] or registered['bytes']!=blob['stored_bytes']:raise ValueError('blob inventory differs')
        spans.append(span(blob,a,b,directory))
    if sum(projection['groups'])!=expected_rows:raise ValueError('row denominator differs')
    return {'size':obj['size'],'spans':spans,'object':obj,'provenance':entry['manifest']}


def special(expected_rows):
    prefix=ROOT/'research/onchain-graph-2026-09-16'
    plan=load(prefix/'prototype/plan.json');receipt=load(prefix/'pilot/artifacts/results/context-2024-01-01.json')
    if receipt['plan_sha256']!=file_hash(prefix/'pilot/plan.json') or file_hash(prefix/'prototype/plan.json')!='4e3716ad928b43902b111e0c4a1e849bfd7c9b35cdbc32993dcc887ddcf07800' or plan['rows']!=expected_rows:raise ValueError('context binding differs')
    spans=[span(b,r['start'],r['end']+1,ROOT) for r,b in zip(plan['ranges'],receipt['benchmark']['blobs'],strict=True)]
    footer_path=ROOT/'research_runs/eth-graph-source-20260916/outputs/request-11.json';footer=load(footer_path,'4b568e9995a4d7cb234c6103dda1b4be55389b49e4252c6e8b65c8e007dec16e')
    if footer['response_headers']['etag']!=plan['object']['etag']:raise ValueError('footer object differs')
    spans.append({'path':str(footer_path),'start':plan['footer_start'],'end':plan['object']['size'],'raw_bytes':footer['bytes'],'raw_sha256':footer['sha256'],'stored_bytes':footer_path.stat().st_size,'stored_sha256':file_hash(footer_path),'codec':'receipt_base64'})
    return {'size':plan['object']['size'],'spans':spans,'object':plan['object'],'provenance':{'plan_hash':file_hash(prefix/'prototype/plan.json'),'receipt_hash':file_hash(prefix/'pilot/artifacts/results/context-2024-01-01.json')}}


def main():
    plan=load(ROOT/'research/onchain-graph-2026-09-16/fullpanel/plan.json','19f3716454216afc172aec2939a9908ba3b57921e99249951e1860b995d1d691')
    resources=load(STUDY/'config/resources.json');weeks=resources['pilot_weeks']+['2022-07-25']
    output=STUDY/'pilot/source-maps-v2';output.mkdir(parents=True,exist_ok=False)
    index={'selection':'eight frozen dispersed weeks plus largest complete training week by declared transaction count; no outcome selection','weeks':{},'total_rows':0,'expected_schema':plan['required_types'],'index_sha256':file_hash(ROOT/'research/onchain-graph-2026-09-16/fullpanel/plan.json')}
    for week in weeks:
        members=[];total=0
        for offset in range(7):
            day=(date.fromisoformat(week)+timedelta(days=offset)).isoformat();rows=plan['expected_rows'][day]
            mapping=special(rows) if day=='2024-01-01' else ordinary(plan['captures'][day],day,rows)
            target=output/(day+'.json');target.write_bytes(canonical_bytes(mapping)+b'\n')
            members.append({'path':str(target),'sha256':file_hash(target),'format':'projected_zstd','expected_rows':rows,'start_utc':day+'T00:00:00Z','end_utc':(date.fromisoformat(day)+timedelta(days=1)).isoformat()+'T00:00:00Z'})
            total+=rows
        index['weeks'][week]={'start_utc':week+'T00:00:00Z','end_utc':(date.fromisoformat(week)+timedelta(days=7)).isoformat()+'T00:00:00Z','status':'complete','expected_members':7,'expected_rows':total,'members':members}
        index['total_rows']+=total
    (output.parent/'source-index.json').write_bytes(canonical_bytes(index)+b'\n')
    print({'weeks':len(weeks),'days':sum(len(x['members']) for x in index['weeks'].values()),'declared_rows':index['total_rows'],'decoded_rows':0})

if __name__=='__main__':main()
