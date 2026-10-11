"""Root source-only successor; no binder, admission, numerical imports or claim."""
from pathlib import Path
import ast, datetime, difflib, hashlib, json, subprocess, sys

ROOT=Path.cwd().resolve(); HERE=Path(__file__).resolve().parent; F=HERE.parent
OLD=F/'real-data-pilot-full33-entry-preparation01-2026-10-11'
T=F/'real-data-pilot-full34-binding-preparation01-2026-10-11'
NAME='eth-paper-real-data-end-to-end-resource-20261011-34'
assert len(sys.argv)==2
ANCHOR=sys.argv[1]
assert len(ANCHOR)==40 and all(c in '0123456789abcdef' for c in ANCHOR)

def load(p): return json.loads(p.read_bytes())
def ref(p):
    body=p.read_bytes()
    return {'path':str(p.relative_to(ROOT)), 'sha256':hashlib.sha256(body).hexdigest(), 'bytes':len(body)}
def save(p,value):
    with p.open('xb') as stream: stream.write((json.dumps(value,sort_keys=True,indent=2)+'\n').encode())
def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==ANCHOR
    assert not (ROOT/'research_runs'/NAME).exists()
    before=(OLD/'preflight33_01.py').read_text(); after=before
    changes=[('20261011-33','20261011-34'),('effective_attempt_budget!=104','effective_attempt_budget!=105'),
             ("'effective_attempt_budget':104","'effective_attempt_budget':105"),
             ('genuine budget104','genuine budget105'),('exact reviewed full33','exact reviewed full34')]
    for old,new in changes:
        assert old in after,old
        after=after.replace(old,new)
    # The immutable preparation is a complete literal dict, not just a new path.
    old_line=next(line for line in before.splitlines() if line.startswith('FROZEN_PREPARATION='))
    moved_line=old_line.replace('20261011-33','20261011-34')
    assert moved_line in after
    after=after.replace(moved_line,'FROZEN_PREPARATION='+repr(ref(T/'PREPARED01.json')))
    ast.parse(after)
    with (HERE/'preflight34_01.py').open('x') as stream: stream.write(after)
    oldio=(OLD/'root_io33_01.py').read_text()
    newio=oldio.replace('from preflight33_01 import check','from preflight34_01 import check')
    assert oldio!=newio
    ast.parse(newio)
    with (HERE/'root_io34_01.py').open('x') as stream: stream.write(newio)
    for oldname,newname in [('preflight33_01.py','preflight34_01.py'),('root_io33_01.py','root_io34_01.py')]:
        a=(OLD/oldname).read_text().splitlines(True); b=(HERE/newname).read_text().splitlines(True)
        with (HERE/(newname+'.diff')).open('x') as stream:
            stream.write(''.join(difflib.unified_diff(a,b,fromfile=str(OLD/oldname),tofile=str(HERE/newname))))
    mapping=load(OLD/'CAPACITY_SOURCE_MAP01.json'); pins=mapping['source_files']
    changed=[]
    for path,old in list(pins.items()):
        actual=ref(ROOT/path)['sha256']
        if actual!=old: changed.append({'path':path,'old':old,'new':actual}); pins[path]=actual
    assert len(pins)==421 and len(changed)==1
    assert changed[0]['path']=='tradingagents/research/onchain_replication/compact_mcm.py'
    assert changed[0]['new']=='abd86e24681f0df4ef3ca82cfb016662d9af5a46a38a32bafc65e7c92f2dacf8'
    # Authenticate all 421 real bodies at the actual committed source once.
    output=subprocess.check_output(['git','-c','core.packedGitWindowSize=16m','-c','core.packedGitLimit=64m','cat-file','--batch'],input=('\n'.join(ANCHOR+':'+p for p in pins)+'\n').encode())
    pos=0
    for path,digest in pins.items():
        end=output.index(b'\n',pos); fields=output[pos:end].split(); pos=end+1
        assert len(fields)==3 and fields[1]==b'blob',path
        count=int(fields[2]); body=output[pos:pos+count]; pos+=count
        assert output[pos:pos+1]==b'\n'; pos+=1
        assert body==(ROOT/path).read_bytes() and hashlib.sha256(body).hexdigest()==digest,path
    assert pos==len(output)
    mapping['source_anchor']=ANCHOR
    mapping['qualification']='Actual421 Git/local body joins at '+ANCHOR+'; only independently reviewed imported-only inter-phase validation changed. New entry files excluded. Not live resource eligibility.'
    save(HERE/'CAPACITY_SOURCE_MAP01.json',mapping)
    capacity=load(OLD/'CAPACITY_DECLARATION_ROOT01.json')
    capacity['identity']=NAME; capacity['at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    capacity['source_anchor']=ANCHOR; capacity['source_body_pins']=pins
    capacity['owned_paths']=[p.replace('20261011-33','20261011-34') for p in capacity['owned_paths']]
    capacity['qualification']='Successor34 prospective declaration reuses all unchanged growth terms and caps; reviewed cadence source bytes are read-only outside writable union. Original failed33 retained bytes remain in actual baseline. Existing additional1MiB metadata headroom retained. Not whole capacity, external reservation or empirical saving.'
    save(HERE/'CAPACITY_DECLARATION_ROOT01.json',capacity)
    core=load(OLD/'CORE_MANIFEST01.json')
    core['inputs']={role:ref(T/'public01'/(role+'.json')) for role in core['inputs']}
    core['source']={p:ref(ROOT/p)['sha256'] for p in core['source']}
    core['scope']='Exact unchanged four scientific policy bodies and current installed source after independently accepted imported-only preparation validation cadence correction; all three lease boundaries remain; no empirical speed or capacity claim.'
    save(HERE/'CORE_MANIFEST01.json',core)
    save(HERE/'SOURCE_PREPARATION01.json',{'status':'DRAFT_NOT_RELEASED','identity':NAME,'source_anchor':ANCHOR,'capacity_source_bodies':421,'changed_source':changed,'baseline_preflight':ref(OLD/'preflight33_01.py'),'baseline_root_io':ref(OLD/'root_io33_01.py'),'numerical_imports':False,'admission':False,'claim':False,'launch':False})
    files={p.name:ref(p) for p in HERE.iterdir() if p.is_file()}
    save(HERE/'SOURCE_MANIFEST01.json',{'status':'DRAFT_NOT_RELEASED','identity':NAME,'files':files})
    print(json.dumps({'status':'SOURCE_DRAFT_NOT_RELEASED','source_bodies':421,'changed_source':len(changed),'claim':False}))
if __name__=='__main__': main()
