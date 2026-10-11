"""Root-only fresh35 source builder; requires actual Root capacity, never launches."""
from pathlib import Path
import ast, datetime, difflib, hashlib, json, subprocess, sys

ROOT=Path.cwd().resolve(); HERE=Path(__file__).resolve().parent; F=HERE.parent
OLD=F/'real-data-pilot-full34-entry-preparation01-2026-10-11'
T=F/'real-data-pilot-full35-binding-preparation01-2026-10-11'
EXPECTED_HERE=F/'real-data-pilot-full35-entry-preparation01-2026-10-11'
NAME='eth-paper-real-data-end-to-end-resource-20261011-35'
SOURCE='53b8890630765d06f8a44e3e8fbaee1f4b00bdfb'
assert len(sys.argv)==3, 'actual source anchor and actual Root capacity SHA required'
ANCHOR,CAPACITY_SHA=sys.argv[1:]
assert ANCHOR==SOURCE and len(CAPACITY_SHA)==64 and all(c in '0123456789abcdef' for c in CAPACITY_SHA)

def load(p): return json.loads(p.read_bytes())
def ref(p):
    body=p.read_bytes()
    return {'path':str(p.relative_to(ROOT)), 'sha256':hashlib.sha256(body).hexdigest(), 'bytes':len(body)}
def save(p,value):
    with p.open('xb') as stream: stream.write((json.dumps(value,sort_keys=True,indent=2)+'\n').encode())
def main():
    assert HERE==EXPECTED_HERE, 'copy reviewed candidate into exact Root E35 before execution'
    assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==ANCHOR
    assert not (ROOT/'research_runs'/NAME).exists()
    # Root owns the declaration. Never manufacture an accepted capacity result.
    capacity_path=HERE/'CAPACITY_DECLARATION_ROOT01.json'
    assert ref(capacity_path)['sha256']==CAPACITY_SHA
    capacity=load(capacity_path)
    assert capacity['identity']==NAME and capacity['source_anchor']==ANCHOR and capacity['decision']=='accepted'
    before=(OLD/'preflight34_01.py').read_text(); after=before
    changes=[('20261011-34','20261011-35'),('effective_attempt_budget!=105','effective_attempt_budget!=106'),
             ("'effective_attempt_budget':105","'effective_attempt_budget':106"),
             ('genuine budget105','genuine budget106'),('exact reviewed full34','exact reviewed full35'),
             ('len(actual)==67','len(actual)==72'),("public['all_input_roles']==67","public['all_input_roles']==72"),
             ('exact genuine67-role','exact genuine72-role'),('len(pins)>=365','len(pins)==423')]
    for old,new in changes:
        assert old in after,old
        after=after.replace(old,new)
    old_line=next(line for line in before.splitlines() if line.startswith('FROZEN_PREPARATION='))
    moved_line=old_line.replace('20261011-34','20261011-35')
    assert moved_line in after
    after=after.replace(moved_line,'FROZEN_PREPARATION='+repr(ref(T/'PREPARED01.json')))
    selected=load(T/'public01/mcm_policy.json')['batched']['execution']
    edge_policy=selected['compiled_edge_policy'];edge_inputs=selected['compiled_edge_inputs']
    expected_inputs={kind:'compiled_edge_'+kind for kind in ('source','adapter','library','runtime','abi')}
    assert edge_inputs==expected_inputs and edge_policy['format']=='cpython-two-attribute-edge-owner-v1'
    literal=next(line for line in after.splitlines() if line.startswith('COMPILED_INPUTS='))
    after=after.replace(literal,literal+'\nEDGE_POLICY='+repr(edge_policy)+'\nEDGE_INPUTS='+repr(edge_inputs))
    seam="    need(execution['max_summary_bytes']==144998400,'original per-stage summary cap differs')"
    assert after.count(seam)==1
    added="""    need(execution.get('compiled_edge_policy')==EDGE_POLICY,'exact selected edge policy differs')
    need(execution.get('compiled_edge_inputs')==EDGE_INPUTS,'exact five edge roles differ')
    for kind,role in EDGE_INPUTS.items():
        need(actual[role]['sha256']==EDGE_POLICY[kind+'_sha256']
             and str(ROOT/actual[role]['path'])==EDGE_POLICY[kind+'_path'],
             'edge source/adapter/library/runtime/ABI role does not join policy')
"""
    after=after.replace(seam,added+seam)
    ast.parse(after)
    with (HERE/'preflight35_01.py').open('x') as stream: stream.write(after)
    oldio=(OLD/'root_io34_01.py').read_text()
    newio=oldio.replace('from preflight34_01 import check','from preflight35_01 import check')
    assert oldio!=newio
    ast.parse(newio)
    with (HERE/'root_io35_01.py').open('x') as stream: stream.write(newio)
    for oldname,newname in [('preflight34_01.py','preflight35_01.py'),('root_io34_01.py','root_io35_01.py')]:
        a=(OLD/oldname).read_text().splitlines(True); b=(HERE/newname).read_text().splitlines(True)
        with (HERE/(newname+'.diff')).open('x') as stream:
            stream.write(''.join(difflib.unified_diff(a,b,fromfile=str(OLD/oldname),tofile=str(HERE/newname))))
    mapping=load(OLD/'CAPACITY_SOURCE_MAP01.json'); pins=mapping['source_files'];assert len(pins)==421
    serializer=F/'pilot34-serializer-postclosure-install01-2026-10-11/INTEGRATION01.json'
    native=F/'pilot34-two-attribute-main-adoption01-2026-10-11/INTEGRATION01.json'
    assert ref(serializer)['sha256']=='bbab2992398b06cd8a9fd583f95cc973d7944364279ccfb2bffdf0a3f5b9da59'
    assert ref(native)['sha256']=='f33fb952c5115b440dce1eb8f1ee10449d1a76268379561ada23ade0594153ec'
    s=load(serializer)['modules'];n=load(native)['modules'];assert len(s)==5 and len(n)==10
    expected={m['destination']['path']:m['destination']['sha256'] for m in s}
    assert not set(expected)&{m['destination'] for m in n}
    expected.update({m['destination']:m['installed_sha256'] for m in n})
    added_paths={'tradingagents/research/onchain_replication/'+name for name in ('compiled_edge_owner.py','edge_chunk_adapter.py')}
    assert set(expected)-set(pins)==added_paths and len(expected)==15
    changed=[]
    for path,old in list(pins.items()):
        actual=ref(ROOT/path)['sha256']
        if actual!=old: changed.append({'path':path,'old':old,'new':actual}); pins[path]=actual
    assert len(changed)==13 and {x['path'] for x in changed}==set(expected)-added_paths
    assert all(x['new']==expected[x['path']] for x in changed)
    for path in sorted(added_paths):
        actual=ref(ROOT/path)['sha256'];assert actual==expected[path];pins[path]=actual
    assert len(pins)==423 and capacity['source_body_pins']==pins
    # Authenticate all423 actual bodies against the installed committed source.
    output=subprocess.check_output(['git','-c','core.packedGitWindowSize=16m','-c','core.packedGitLimit=64m','cat-file','--batch'],input=('\n'.join(ANCHOR+':'+p for p in pins)+'\n').encode())
    pos=0
    for path,digest in pins.items():
        end=output.index(b'\n',pos); fields=output[pos:end].split(); pos=end+1
        assert len(fields)==3 and fields[1]==b'blob',path
        count=int(fields[2]); body=output[pos:pos+count]; pos+=count
        assert output[pos:pos+1]==b'\n'; pos+=1
        assert body==(ROOT/path).read_bytes() and hashlib.sha256(body).hexdigest()==digest,path
    assert pos==len(output)
    numerical=load(T/'public01/pair_policy.json')['numerical_source']
    assert numerical['commit']==ANCHOR and len(numerical['files'])==200 and all(pins.get(p)==h for p,h in numerical['files'].items())
    assert len(load(T/'PUBLIC_INPUT_REFS_DRAFT01.json'))==71
    mapping['source_anchor']=ANCHOR
    mapping['qualification']='Actual423 Git/local body joins: original421 paths with13 accepted installed changes plus2 native helpers; exact5 serializer and10 native module adoption. Read-only source closure, not live capacity eligibility.'
    # The real Root map is already frozen; authenticate rather than republish.
    map_path=HERE/'CAPACITY_SOURCE_MAP01.json'
    assert ref(map_path)['sha256']=='713bfa99920959ce0807b2e3c987ad79a11aaa2fb39d767f39da5757210d37be'
    actual_map=load(map_path)
    assert actual_map['source_files']==pins and actual_map['source_anchor']==ANCHOR
    old_capacity=load(OLD/'CAPACITY_DECLARATION_ROOT01.json')
    for key in ('new_logical_growth_bytes','new_allocated_growth_bytes','non_directory_new_allocated_growth_bytes','new_entries','directory_allocated_bound_bytes','other_writer_reserved_bytes','allocation_semantics','directory_and_other_writers_included','runtime_residuals_included'):
        assert capacity[key]==old_capacity[key],key
    assert capacity['owned_paths']==[p.replace('20261011-34','20261011-35') for p in old_capacity['owned_paths']]
    core=load(OLD/'CORE_MANIFEST01.json')
    for role,pin in core['inputs'].items():
        original=load(ROOT/pin['path']);current=load(T/'public01'/(role+'.json'))
        if role=='mcm_policy':
            current['batched']['execution'].pop('compiled_edge_policy');current['batched']['execution'].pop('compiled_edge_inputs')
        assert current==original,'scientific core changed: '+role
    core['inputs']={role:ref(T/'public01'/(role+'.json')) for role in core['inputs']}
    core['source']={p:ref(ROOT/p)['sha256'] for p in core['source']}
    core['scope']='Four original scientific core policies preserved except explicit reviewed five-role native edge selection; accepted5 serializers and10 native source bodies installed; scientific method/resources/60s lease unchanged. No empirical speed or capacity claim.'
    save(HERE/'CORE_MANIFEST01.json',core)
    save(HERE/'SOURCE_PREPARATION01.json',{'status':'DRAFT_NOT_RELEASED','identity':NAME,'source_anchor':ANCHOR,'capacity_source_bodies':423,'numerical_source_bodies':200,'changed_source':changed,'added_source_paths':sorted(added_paths),'serializer_installation':ref(serializer),'native_installation':ref(native),'capacity_declaration':ref(capacity_path),'baseline_preflight':ref(OLD/'preflight34_01.py'),'baseline_root_io':ref(OLD/'root_io34_01.py'),'numerical_imports':False,'admission':False,'claim':False,'launch':False})
    files={p.name:ref(p) for p in HERE.iterdir() if p.is_file()}
    save(HERE/'SOURCE_MANIFEST01.json',{'status':'DRAFT_NOT_RELEASED','identity':NAME,'files':files})
    print(json.dumps({'status':'SOURCE_DRAFT_NOT_RELEASED','source_bodies':423,'changed_source':len(changed),'added_source':2,'claim':False}))
if __name__=='__main__': main()
