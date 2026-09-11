"""Independent seven-path check; reads only the retained 13-byte CSV region."""
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess

ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).parent
RUN=ROOT/'research_runs/news-provenance-20260911'
read=lambda p:json.loads(p.read_bytes())
sha=lambda b:hashlib.sha256(b).hexdigest()


def safe_open(absolute,directory):
    path=Path(absolute);assert path.is_absolute() and '..' not in path.parts
    assert not any(p in {'keys','apis','hf_token.txt'} or p.startswith('.env') for p in path.parts)
    held=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
    try:
        for i,name in enumerate(path.parts[1:]):
            flags=os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK
            if directory or i<len(path.parts)-2:flags|=os.O_DIRECTORY
            child=os.open(name,flags,dir_fd=held);os.close(held);held=child
        mode=os.fstat(held).st_mode
        assert stat.S_ISDIR(mode) if directory else stat.S_ISREG(mode)
        return held
    except BaseException:
        os.close(held);raise


def identity(fd):
    s=os.fstat(fd)
    return {'device':s.st_dev,'inode':s.st_ino,'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns,
            'mtime_scope':'Local filesystem attribute only; not historical availability.'}


def verify():
    claim=read(RUN/'claim.json');done=read(RUN/'complete.json')
    assert claim['source']==done['source']=='7e5e8b1affb1feb4e729290b943c313a56493a46'
    assert done['registration_sha256']=='e85a08c4ee2878c38aa111506f5d179d83161a430e7aa925b242177bb41f5bee'
    assert sha((RUN/'claim.json').read_bytes())==done['claim_sha256']
    start,end=[datetime.fromisoformat(x) for x in (claim['started_at'],done['ended_at'])]
    committed=datetime.fromisoformat(subprocess.check_output(['git','show','-s','--format=%cI',claim['source']],cwd=ROOT,text=True).strip())
    assert committed<start<end
    spec_ref=claim['inputs']['request_spec'];spec_raw=(ROOT/spec_ref['path']).read_bytes();assert sha(spec_raw)==spec_ref['sha256'];spec=json.loads(spec_raw)
    assert len(spec['targets'])==7 and len({t['path'] for t in spec['targets']})==7
    assert spec['csv_max_bytes']==65536 and spec['footer_max_bytes']==1048576
    ids=[t['id'] for t in spec['targets']]
    assert claim['experiment']['cells']==ids and [c['id'] for c in done['cells']]==ids
    assert done['cell_count']==done['unavailable_count']==7 and all(c['status']=='unavailable' for c in done['cells'])
    expected=[name+'-receipt.json' for name in ids]+['inventory.json','admission.json']
    assert set(expected)==set(done['output_sha256'])=={p.name for p in (RUN/'outputs').iterdir()}
    output_bytes=0
    for name,h in done['output_sha256'].items():
        raw=(RUN/'outputs'/name).read_bytes();assert sha(raw)==h;output_bytes+=len(raw)
        if name.endswith('-receipt.json'):assert len(raw)<=131072
    assert output_bytes==19350 and output_bytes<=spec['max_output_bytes']==4194304
    inventory=read(RUN/'outputs/inventory.json');admission=read(RUN/'outputs/admission.json')
    assert inventory['source_count']==7 and inventory['schema_slot_count']==13
    assert len(inventory['sources'])==7 and len(inventory['subslots'])==13 and len(admission['schema_slots'])==13
    assert admission['cells']==done['cells'] and all(x['status']=='unavailable' for x in admission['schema_slots'])
    assert inventory['subslots']==[slot for r in inventory['sources'] for slot in r['schema_slots']]
    assert admission['schema_slots']==[{'id':r['id'],'status':r['status']} for r in inventory['subslots']]
    sources={r['id']:r for r in inventory['sources']};missing=[];previous=start;classification=None
    for target in spec['targets']:
        r=sources[target['id']];assert r==read(RUN/'outputs'/(target['id']+'-receipt.json'))
        observed=datetime.fromisoformat(r['observation_utc']);assert previous<=observed<=end;previous=observed
        assert r['historical_availability']=='unverified' and r['status']=='unavailable'
        if target['format']=='monthly-parquet':
            try:fd=safe_open(target['path'],True)
            except FileNotFoundError:missing.append(target['id'])
            else:os.close(fd);raise AssertionError('registered missing directory changed before review')
            assert r['inventory']=={'status':'missing','reason_code':'target_missing_or_forbidden','processed_entries':0,'overflow_probe':False}
            assert r['schema_slots']==[{'id':target['id']+'-footer-'+str(i),'status':'unavailable','reason_code':'no_fixed_selection','historical_availability':'unverified'} for i in (1,2)]
        else:
            assert target['id']=='external-csv' and r['inventory']=={'status':'complete'}
            slot=r['schema_slots'][0];assert slot['id']=='external-csv-header' and slot['status']=='unavailable' and 'schema' not in slot
            assert slot['regions']==[{'offset':0,'length':13,'sha256':'4f9151e43bb1edad6ff8a4115df39b31136a347d834be98dbdbf280f80dd2d99'}]
            fd=safe_open(target['path'],False);region=bytearray()
            try:
                before=identity(fd)
                # No read-ahead, no bytes beyond the already retained region.
                for _ in range(13):
                    one=os.read(fd,1);assert len(one)==1;region.extend(one)
                    if one in (b'\n',b'\r'):break
                after=identity(fd)
            finally:os.close(fd)
            second=safe_open(target['path'],False)
            try:current=identity(second)
            finally:os.close(second)
            assert before==after==current==slot['identity_before']==slot['identity_after']==slot['path_identity_after']
            assert before['bytes']==576048 and len(region)==13 and region[-1:] in (b'\n',b'\r')
            assert sha(region)==slot['regions'][0]['sha256']
            classification={'first_physical_line_bytes':13,'first_physical_line_sha256':sha(region),'file_bytes':576048,
                            'file_identity_unchanged_since_capture':True,'raw_text_emitted':False,'records_after_first_line_read':0}
            try:text=bytes(region).decode('utf-8-sig',errors='strict')
            except UnicodeDecodeError:classification.update(utf8_valid=False,reason='unsupported_utf8')
            else:
                classification['utf8_valid']=True
                try:rows=list(csv.reader(io.StringIO(text,newline=''),strict=True))
                except csv.Error:classification.update(csv_syntax_valid=False,reason='unsupported_single_line_csv')
                else:
                    classification['csv_syntax_valid']=True
                    assert len(rows)==1 and rows[0]
                    normalized=[x.strip().casefold() for x in rows[0]]
                    recognized=sorted({x for x in normalized if x in spec['field_whitelist']})
                    plausible=sorted({x for x in normalized if x in spec['plausible_header_fields']})
                    assert plausible==[]
                    classification.update(candidate_field_count=len(rows[0]),recognized_whitelist_fields=recognized,
                        plausible_id_or_time_fields=plausible,unknown_field_count=sum(x not in spec['field_whitelist'] for x in normalized),
                        unknown_name_sha256=[sha(x.encode('utf-8')) for x in rows[0] if x.strip().casefold() not in spec['field_whitelist']],
                        reason='first_line_lacks_frozen_plausible_id_or_time_field; header semantics remain unavailable')
            assert slot['reason_code']=='unsupported_or_invalid_metadata'
    assert len(missing)==6 and classification is not None
    for name,h in claim['experiment']['runtime_hashes'].items():
        path='tradingagents/research/'+name;assert sha((ROOT/path).read_bytes())==sha(subprocess.check_output(['git','show',claim['source']+':'+path],cwd=ROOT))==h
    for name,h in claim['experiment']['source_files'].items():
        assert sha((ROOT/name).read_bytes())==sha(subprocess.check_output(['git','show',claim['source']+':'+name],cwd=ROOT))==h
    guard=read(HERE/'news-provenance-resource-execution.json')
    assert guard['child_exit_code']==0 and guard['limit_reason'] is None
    assert guard['elapsed_seconds']<guard['wall_limit_seconds']==120 and guard['peak_sampled_tree_rss_bytes']<guard['rss_limit_bytes']==512*1024**2
    from tradingagents.research.verify import verify_run
    structural=verify_run(RUN);assert structural['cell_count']==structural['unavailable_count']==7 and structural['output_count']==9
    assert claim['family']['attempt_budget']==1 and claim['family']['prior_attempts']==0
    return {'status':'PASS source-only negative admission reconstruction','source':claim['source'],'registration_sha256':done['registration_sha256'],
        'source_cells':7,'unavailable_source_cells':7,'schema_slots':13,'unavailable_schema_slots':13,'outputs':9,'output_bytes':output_bytes,
        'missing_registered_roots':missing,'csv_first_line_classification':classification,'output_sha256':done['output_sha256'],
        'structural_verification':structural,'resource':guard,'reviewed_utc':datetime.now(timezone.utc).isoformat(),
        'access_scope':{'registered_paths_checked':7,'directory_entries_enumerated':0,'parquet_files_opened':0,'csv_bytes_read':13,'csv_records_after_first_line_read':0,
                        'whole_csv_hashed':False,'alternate_paths_checked':0,'network_requests':0,'inspector_imported':False},
        'limitations':['No authenticated corpus identity','No historical availability or revision semantics','No proof stores absent elsewhere or destroyed','No full corpus backup','No financial utility or news-family rejection','File identity checks are best effort, not atomic','Receipt verification does not establish pre-result remote push timing']}


if __name__=='__main__':
    result=verify()
    with (HERE/'news-provenance-review.json').open('x') as output:json.dump(result,output,indent=2,allow_nan=False);output.write('\n')
    print(json.dumps({k:result[k] for k in ('status','source_cells','unavailable_source_cells','schema_slots','outputs','csv_first_line_classification','access_scope')}))
