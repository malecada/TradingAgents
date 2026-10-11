"""Root source-only successor; no binder, admission, numerical imports or claim."""
from pathlib import Path
import ast, datetime, difflib, hashlib, json, subprocess

ROOT=Path.cwd().resolve(); HERE=Path(__file__).resolve().parent; F=HERE.parent
OLD=F/'real-data-pilot-full30-entry-preparation01-2026-10-11'
T=F/'real-data-pilot-full31-binding-preparation02-2026-10-11'
NAME='eth-paper-real-data-end-to-end-resource-20261011-31'
ANCHOR='b87a3c226ea5af74fab37c48e3884340b11d2458'

def load(p): return json.loads(p.read_bytes())
def ref(p):
    body=p.read_bytes()
    return {'path':str(p.relative_to(ROOT)), 'sha256':hashlib.sha256(body).hexdigest(), 'bytes':len(body)}
def save(p,value):
    with p.open('xb') as stream: stream.write((json.dumps(value,sort_keys=True,indent=2)+'\n').encode())
def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==ANCHOR
    assert not (ROOT/'research_runs'/NAME).exists()
    before=(OLD/'preflight30_05.py').read_text(); after=before
    changes=[('20261011-30','20261011-31'),("gate03.json","gate01.json"),
             ('BINDING03.json','BINDING01.json'),('RELEASE_REVIEW03.json','RELEASE_REVIEW01.json'),
             ('effective_attempt_budget!=101','effective_attempt_budget!=102'),
             ("'effective_attempt_budget':101","'effective_attempt_budget':102"),
             ('genuine budget101','genuine budget102'),('exact reviewed full30','exact reviewed full31')]
    for old,new in changes:
        assert old in after,old
        after=after.replace(old,new)
    # The immutable preparation is a complete literal dict, not just a new path.
    old_line=next(line for line in before.splitlines() if line.startswith('FROZEN_PREPARATION='))
    moved_line=old_line.replace('20261011-30','20261011-31')
    assert moved_line in after
    after=after.replace(moved_line,'FROZEN_PREPARATION='+repr(ref(T/'PREPARED01.json')))
    ast.parse(after)
    with (HERE/'preflight31_01.py').open('x') as stream: stream.write(after)
    oldio=(OLD/'root_io30_05.py').read_text()
    newio=oldio.replace('from preflight30_05 import check','from preflight31_01 import check')
    assert oldio!=newio
    ast.parse(newio)
    with (HERE/'root_io31_01.py').open('x') as stream: stream.write(newio)
    for oldname,newname in [('preflight30_05.py','preflight31_01.py'),('root_io30_05.py','root_io31_01.py')]:
        a=(OLD/oldname).read_text().splitlines(True); b=(HERE/newname).read_text().splitlines(True)
        with (HERE/(newname+'.diff')).open('x') as stream:
            stream.write(''.join(difflib.unified_diff(a,b,fromfile=str(OLD/oldname),tofile=str(HERE/newname))))
    mapping=load(OLD/'CAPACITY_SOURCE_MAP01.json'); pins=mapping['source_files']
    changed=[]
    for path,old in list(pins.items()):
        actual=ref(ROOT/path)['sha256']
        if actual!=old: changed.append({'path':path,'old':old,'new':actual}); pins[path]=actual
    assert len(pins)==421 and len(changed)==1
    assert changed[0]['path']=='tradingagents/research/onchain_replication/compact_mcm_batched.py'
    assert changed[0]['new']=='e93d3b7073c8de5d1c3e7f5f30b55ba613b47a014f8fe449a0fe7e8a746941dd'
    # Authenticate all 421 real bodies at the actual committed source once.
    output=subprocess.check_output(['git','cat-file','--batch'],input=('\n'.join(ANCHOR+':'+p for p in pins)+'\n').encode())
    pos=0
    for path,digest in pins.items():
        end=output.index(b'\n',pos); fields=output[pos:end].split(); pos=end+1
        assert len(fields)==3 and fields[1]==b'blob',path
        count=int(fields[2]); body=output[pos:pos+count]; pos+=count
        assert output[pos:pos+1]==b'\n'; pos+=1
        assert body==(ROOT/path).read_bytes() and hashlib.sha256(body).hexdigest()==digest,path
    assert pos==len(output)
    mapping['source_anchor']=ANCHOR
    mapping['qualification']='Actual 421 Git/local body joins at b87; only installed timing correction changed. New entry files excluded. Not live resource eligibility.'
    save(HERE/'CAPACITY_SOURCE_MAP01.json',mapping)
    capacity=load(F/'real-data-pilot-full30-preparation01-2026-10-11/CAPACITY_DECLARATION_ROOT01.json')
    capacity['identity']=NAME; capacity['at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    capacity['source_anchor']=ANCHOR; capacity['source_body_pins']=pins
    capacity['owned_paths']=[p.replace('20261011-30','20261011-31') for p in capacity['owned_paths']]
    capacity['qualification']+=' Successor31 reuses all unchanged growth terms and caps; 659 extra read-only source bytes are outside writable union. Prior30 failed bytes remain in actual baseline. Existing additional1MiB metadata headroom retained; prospective declaration, not measured whole capacity or external reservation.'
    save(HERE/'CAPACITY_DECLARATION_ROOT01.json',capacity)
    core=load(OLD/'CORE_MANIFEST02.json')
    core['inputs']={role:ref(T/'public01'/(role+'.json')) for role in core['inputs']}
    core['source']={p:ref(ROOT/p)['sha256'] for p in core['source']}
    core['scope']='Exact unchanged four scientific policy bodies and current installed source after independently accepted three lease boundaries; no empirical speed or capacity claim.'
    save(HERE/'CORE_MANIFEST01.json',core)
    save(HERE/'SOURCE_PREPARATION01.json',{'status':'DRAFT_NOT_RELEASED','identity':NAME,'source_anchor':ANCHOR,'capacity_source_bodies':421,'changed_source':changed,'baseline_preflight':ref(OLD/'preflight30_05.py'),'baseline_root_io':ref(OLD/'root_io30_05.py'),'numerical_imports':False,'admission':False,'claim':False,'launch':False})
    files={p.name:ref(p) for p in HERE.iterdir() if p.is_file()}
    save(HERE/'SOURCE_MANIFEST01.json',{'status':'DRAFT_NOT_RELEASED','identity':NAME,'files':files})
    print(json.dumps({'status':'SOURCE_DRAFT_NOT_RELEASED','source_bodies':421,'changed_source':len(changed),'claim':False}))
if __name__=='__main__': main()
