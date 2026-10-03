"""Freeze only local source candidate and complete selected origin map."""
import ast,copy,difflib,hashlib,json,pathlib
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[3];OLD=D.parent/'neural-cold-feature-handoff-proof-outer-preparation02-2026-10-03';BASE=D.parent/'neural-cold-feature-handoff-proof-source-composition02-2026-10-03'
def ref(p):
 raw=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(name,v):(D/name).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
assert not (D/'MANIFEST03.json').exists(),'preserve frozen successor'
inv=json.loads((BASE/'source_inventory02.json').read_text());rows=inv['source_inventory'];target='proof_tools/proof_release01.py';before=copy.deepcopy(next(r for r in rows if r['target']==target));after=next(r for r in rows if r['target']==target);r=ref(D/'proof_release01.py');after.update(origin=r['path'],snapshot=r['path'],bytes=r['bytes'],sha256=r['sha256'],git_commit=None,git_path=None)
for row in rows:
 path=ROOT/row.get('snapshot',row['origin']);v=ref(path);assert v['bytes']==row['bytes'] and v['sha256']==row['sha256']
 if row['target'].endswith('.py'):ast.parse(path.read_bytes())
inv.update(predecessor=ref(BASE/'source_inventory02.json'),logical_bytes=sum(r['bytes'] for r in rows),status='source-only-outer03-unreviewed',execution_admitted=False);write('source_inventory03.json',inv)
write('install-delta03.json',{'base_inventory':ref(BASE/'source_inventory02.json'),'changed_targets':[{'before':before,'after':after}],'unchanged_targets':194,'source_count':195,'package_count':147})
write('install-map03.json',{'files':[{'target':'proof_tools/'+n,'origin':ref(D/n)['path'],'bytes':ref(D/n)['bytes'],'sha256':ref(D/n)['sha256']} for n in ('proof_supervise01.py','proof_outer01.py','proof_raw01.py','proof_release01.py','runtime_gate01.py','build_release_draft01.py')],'source_closure_must_precede_materialization':True,'status':'not_released'})
(D/'proof_release01.py.patch').write_text(''.join(difflib.unified_diff((OLD/'proof_release01.py').read_text().splitlines(True),(D/'proof_release01.py').read_text().splitlines(True),fromfile=str((OLD/'proof_release01.py').relative_to(ROOT)),tofile=str((D/'proof_release01.py').relative_to(ROOT)))))
files=[ref(p) for p in sorted(D.iterdir()) if p.is_file()];write('MANIFEST03.json',{'schema_version':1,'status':'frozen-source-only-unreviewed','files':files,'file_count':len(files),'dependencies':[ref(OLD/'MANIFEST02.json'),ref(OLD/'REVIEW_OUTER_PREPARATION02.md'),ref(BASE/'MANIFEST02.json'),ref(BASE/'source_inventory02.json')],'actual_jobs':0,'actual_claims':0,'numeric_imports':False})
for n in ('MANIFEST03.json','source_inventory03.json','install-delta03.json','proof_release01.py','REPORT03.md'):print(n,ref(D/n)['sha256'])
print('source_count',len(rows),'package_count',inv['package_count'],'source_bytes',inv['logical_bytes'])
