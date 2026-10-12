"""Only the frozen core-reference correction and dependent metadata joins."""
import ast, copy, hashlib, json, re
from pathlib import Path
from check01 import ROOT,HERE,F,NEW,OLD,PUBLIC,NAME,OLD_NAME,load,sha,pin,refcheck

def restore(diff):
    lines=diff.splitlines(True); out={};i=0
    while i<len(lines):
        assert lines[i].startswith('--- ')
        source=lines[i][4:].strip();dest=lines[i+1][4:].strip();i+=2
        body=(NEW/source).read_text().splitlines(True); restored=[];pos=0
        while i<len(lines) and not lines[i].startswith('--- '):
            m=re.fullmatch(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@\n',lines[i]);assert m,lines[i]
            start=int(m[1])-1;restored.extend(body[pos:start]);pos=start;i+=1
            while i<len(lines) and not lines[i].startswith(('@@ ','--- ')):
                line=lines[i];i+=1
                if line[0] in ' -':assert body[pos]==line[1:];pos+=1
                if line[0] in ' +':restored.append(line[1:])
        restored.extend(body[pos:]);out[dest.removesuffix('.WITHHELD01')]=''.join(restored)
    return out

receipt=load(NEW/'CORE_REF_CORRECTION01.json'); restored=restore((NEW/'CORE_REF_CORRECTION_INVERSE01.diff').read_text())
for name,v in receipt['versions'].items():
    assert sha(NEW/name)==v['corrected_sha256']
    assert hashlib.sha256(restored[name].encode()).hexdigest()==v['withheld_sha256']
initial=load(HERE/'CHECK01.json');originalpins={Path(x['path']).name:x['sha256'] for x in initial['snapshot']}
for name in set(originalpins)&set(restored):assert hashlib.sha256(restored[name].encode()).hexdigest()==originalpins[name]
gate=load(NEW/'gate01.json');oldgate=json.loads(restored['gate01.json']); e=gate['experiments'][NAME];originale=oldgate['experiments'][NAME]
pinchanges={p:v for p,v in e['source_files'].items() if originale['source_files'][p]!=v}
assert {Path(p).name for p in pinchanges}=={'prepare_entry01.py','CORE_MANIFEST01.json','CAPACITY_DECLARATION_ROOT01.json'}
for p,v in pinchanges.items():assert sha(ROOT/p)==v
inverse=copy.deepcopy(gate);inverse['experiments'][NAME]['source_files']=originale['source_files'];assert inverse==oldgate
core=load(NEW/'CORE_MANIFEST01.json');oldcore=json.loads(restored['CORE_MANIFEST01.json'])
assert core['builder_sha256']==sha(PUBLIC/'build_public01.py')
assert core['source']==oldcore['source'] and core['status']==oldcore['status']
for role,ref in core['inputs'].items():
    refcheck(ref);assert ref['path']==e['inputs'][role]['path'] and ref['sha256']==e['inputs'][role]['sha256']
    current=load(ROOT/ref['path']);prior=load(ROOT/oldcore['inputs'][role]['path'])
    if role=='mcm_policy':current['entry_qualification']['experiment_id']=OLD_NAME
    assert current==prior
cap=load(NEW/'CAPACITY_DECLARATION_ROOT01.json');priorcap=json.loads(restored['CAPACITY_DECLARATION_ROOT01.json'])
assert cap==dict(priorcap,decision_scope=priorcap['decision_scope'].replace('fixed36','fixed38').replace('whole37','whole39'))
binding=load(NEW/'BINDING_DRAFT01.json');priorbinding=json.loads(restored['BINDING_DRAFT01.json'])
for role in ('core_manifest','capacity_observation','gate'):refcheck(binding[role]);priorbinding[role]=binding[role]
assert binding==priorbinding
assert all(binding[k] is None for k in ('binding_review','complete_increment_recovery','new_increment_recovery_review','prior_preservation_complete','prior_recovery_review'))
reg=load(NEW/'REGISTRATION_DRAFT01.json');priorreg=json.loads(restored['REGISTRATION_DRAFT01.json']);refcheck(reg['new_gate']);priorreg['new_gate']=reg['new_gate'];priorreg['core_ref_correction']='Three core bodies unchanged. Actual38 mcm_policy differs from36 only in the registered entry-qualification experiment selector; fresh actual38 references required. Original withheld draft is losslessly retained by inversepatch01.';assert reg==priorreg
# No entry-control change was needed, and no other initially sampled body changed.
allowed={'prepare_entry01.py','CORE_MANIFEST01.json','CAPACITY_DECLARATION_ROOT01.json','gate01.json','BINDING_DRAFT01.json','REGISTRATION_DRAFT01.json','PROGRESS.md'}
assert all(sha(NEW/n)==d for n,d in originalpins.items() if n not in allowed)
body=(NEW/'prepare_entry01.py').read_text()
new="    core=load(OLD/'CORE_MANIFEST01.json')\n    core['inputs']={role:pin(ROOT/inputs[role]['path']) for role in core['inputs']}\n    core['builder_sha256']=pin(PUBLIC/'build_public01.py')['sha256']\n    core['scope']=core['scope'].replace('fixed36','fixed38')\n    save('CORE_MANIFEST01.json',core)\n"
old="    core_body=read(OLD/'CORE_MANIFEST01.json')\n    with (HERE/'CORE_MANIFEST01.json').open('xb') as stream:stream.write(core_body)\n"
assert new in body; inverse=body.replace(new,old)
extra="    capacity['decision_scope']=capacity['decision_scope'].replace('fixed36','fixed38').replace('whole37','whole39')\n"
assert extra not in inverse  # capacity wording was a recorded metadata-only correction
assert hashlib.sha256(inverse.encode()).hexdigest()==originalpins['prepare_entry01.py'];ast.parse(inverse)
result={'decision':'accepted','scope':'Corrected source and registration draft metadata only; no release','closed_finding':'P1 core mcm_policy selector mismatch','literal_inverse_preserves_withheld_bodies':True,'corrected_core_roles':sorted(core['inputs']),'gate_source_pins':len(e['source_files']),'changed_dependent_source_pins':pinchanges,'six_numerical_sources_and_preflight_rootio_unchanged':True,'recovery_and_binding_review_still_null':True,'final_snapshot':[pin(p) for p in sorted(NEW.iterdir()) if p.is_file()]}
print(json.dumps(result,indent=2,sort_keys=True))
