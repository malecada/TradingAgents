"""Finite source-only checks. Never executes preservation helpers or Git."""
import ast
import hashlib
import json
from pathlib import Path
D=Path(__file__).resolve().parent;B=D.parent/'full35increment30';F=D.parent.parent;R=F.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name, condition):
    checks.append({'name':name,'passed':bool(condition)})
    if not condition:raise AssertionError(name)
def assignment(source,name):
    node=next(n for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
    return ast.literal_eval(node.value)
try:
    sources={stem:(D/(stem+'31.py')).read_text() for stem in ('select','capture','recover')}
    for stem,source in sources.items():compile(source,stem+'31.py','exec')
    check('three helper sources compile without execution',True)
    mapping=json.loads((D/'CAPTURE_RECOVERY_LITERAL_MAP01.json').read_bytes())
    for baseline,replacements in mapping.items():
        restored=sources[baseline.removesuffix('30.py')]
        for old,new in reversed(list(replacements.items())):restored=restored.replace(new,old)
        check(baseline+' exact literal inverse',(B/baseline).read_text()==restored)
    s=sources['select'];old=(B/'select30.py').read_text()
    check('unchanged selection typed/hash/mode/secret/nlink1/64MiB/before-after kernel',s[s.index('reused=[]'):s.index('selection = {')]==old[old.index('reused=[]'):old.index('selection = {')])
    roster=json.loads((D/'PROSPECTIVE_ROSTER01.json').read_bytes())
    check('exact finite roots and helper roster',assignment(s,'owned')==roster['public_roots'] and assignment(s,'helper_names')==tuple(roster['helper_names']))
    snap=json.loads((R/roster['source_snapshot']['path']).read_bytes())
    pins=assignment(s,'main_source_pins')
    check('all23 declared source pins current and snapshot authenticated',len(pins)==23 and pins=={r['path']:r['sha256'] for r in snap['files']} and sha(R/roster['source_snapshot']['path'])==roster['source_snapshot']['sha256'] and all(sha(R/p)==h for p,h in pins.items()))
    check('exact five present-scope declarations plus absent sixth',len(roster['raw_scope_states'])==6 and [r['exists'] for r in roster['raw_scope_states']]==[True]*5+[False] and "assert not root.exists() and not root.is_symlink()" in s and "allowed_roots=[F/name for name in owned]+scopes" in s)
    check('exact33 prior-generated paths; no invented staging receipt',len(roster['prior_generated_files'])==33 and 'STAGING_UNAVAILABLE01.json' not in roster['prior_generated_files'] and all((B/n).is_file() for n in roster['prior_generated_files']))
    check('actual30 lineage pins',sha(B/'FRESH_GIT_RECOVERY30.json')=='32023dba761dbdcfc0fccd9bb9749a5320bdd345efa26a22411ca58be0f15d62' and sha(F/'pilot35-preparation-increment-return-review01-2026-10-11/REVIEW01.json')=='170c85ab7eb08000467d7eeec098e1feb153ce8675b687d99f959728767dfbed')
    check('exact three baseline aliases; authentication retained',"('full35-preparation-increment30.tar','fresh-git-recovered-full35increment30.tar','actual_external_archive_blob_return.stdout')" in s and "path.stat().st_size==prior_receipt['returned_archive']['bytes'] and sha(path)==prior_receipt['returned_archive']['sha256']" in s)
    check('no declared operations have run',(not any((D/n).exists() for n in ('SELECTION31.json','CAPTURE31.json','FRESH_GIT_RECOVERY31.json','GIT_OPERATIONS31.json'))))
    pending=[name for name in roster['public_roots'] if not (F/name).is_dir()]
    status='PASS_SOURCE_ONLY_PENDING_ROOT_SCOPE_FREEZE'
except BaseException:
    (D/'AUTHOR_CHECK01.json').write_text(json.dumps({'status':'FAILED','checks':checks},indent=2)+'\n')
    raise
else:
    result={'status':status,'checks':checks,'missing_mandatory_public_roots':pending,'limits':'Source checks only; raw roots not traversed, archive aliases not read, no selection/capture/recovery/Git/network; Root must freeze completed evidence and independent review before selecting.'}
    (D/'AUTHOR_CHECK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':status,'checks':len(checks),'missing_mandatory_public_roots':pending}))
