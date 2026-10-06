"""Independent bounded delivery verification; stdlib and metadata dispatch only."""
from pathlib import Path
import ast, difflib, hashlib, json, subprocess, sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
C=HERE.parent/'real-data-pilot-feature-integration-successor01-2026-10-06'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_bytes())
def need(v,m):
    if not v: raise AssertionError(m)
need(sha(C/'MANIFEST01.json')=='ae1f353e25a63780b41292d1c5b6faaf96fcf5874d0266153b28e67a9b4a02c0','wrong candidate manifest')
need(sha(C/'INSTALL_MAP01.json')=='3931ea50a094d0ac9403e43e038961877b2910f9242afa4a34f1cbb4e2a86f3b','wrong map')
for name, pin in read(C/'MANIFEST01.json')['members'].items():
    p=C/name; need(p.stat().st_size==pin['bytes'] and sha(p)==pin['sha256'],'manifest member '+name)
rows=read(C/'INSTALL_MAP01.json')['sources'];runtime=[x for x in rows if x['kind']=='runtime']
need(len(rows)==17 and len(runtime)==14,'delivery count')
need(len({x['candidate'] for x in rows})==17 and len({x['root_install_path'] for x in runtime})==14,'overlap')
need(sum(x['before_sha256'] is None for x in runtime)==3,'addition count')
patch=''
for x in rows:
    p=ROOT/x['candidate'];parent=ROOT/x['accepted_parent']
    need(p.read_bytes()==parent.read_bytes() and sha(p)==x['sha256'] and p.stat().st_size==x['bytes'],'copy mismatch')
    compile(p.read_bytes(),str(p),'exec')
    if x in runtime:
        before=ROOT/x['root_install_path']; old=before.read_text() if before.exists() else ''
        need((sha(before) if before.exists() else None)==x['before_sha256'],'baseline changed')
        patch+=''.join(difflib.unified_diff(old.splitlines(True),p.read_text().splitlines(True),fromfile=x['root_install_path'] if old else '/dev/null',tofile=x['root_install_path']))
need(patch.encode()==(C/'integration01.patch').read_bytes(),'patch differs from exact overlay')
for item in read(C/'PARENTS01.json').values(): need(sha(ROOT/item['manifest'])==item['sha256'],'parent manifest')
for path,item in read(C/'REUSED_ACCEPTANCE01.json').items(): need(sha(ROOT/path)==item['sha256'],'accepted parent review')
for path,pin in read(C/'UNCHANGED_SOURCE01.json').items(): need(sha(ROOT/path)==pin,'unchanged scientific/helper source')
old=read(C/'DEPENDENCIES_BEFORE01.json');new=read(C/'DEPENDENCIES01.json')
need(set(old)==set(new),'dependency keys')
changed=[]
for key in new:
    need(old[key]['sha256']==new[key]['sha256'] and (ROOT/old[key]['path']).read_bytes()==(ROOT/new[key]['path']).read_bytes(),'dependency body changed')
    if new[key]!=old[key]: changed.append(key)
need(set(changed)=={'builder','controls','history','durability'},'dependency path delta')
# Actual CLI dispatch must reach its specific early metadata refusal; no arrays or package imports.
draft=HERE.parent/'real-data-pilot-feature-policy-successor-preparation01-2026-10-06/draft01/INPUT_DRAFT01.json'
call=subprocess.run([sys.executable,'-B',str(C/'successor01.py'),'--prepare',str(draft)],capture_output=True,text=True)
expected='ValueError: missing genuine graph/count metadata: 2022-05-30T00:00:00Z, 2022-06-06T00:00:00Z'
need(call.returncode==1 and call.stderr.strip().endswith(expected),'actual metadata dispatch refusal differs')
# Static ordering checks complement accepted actual callback synthetic evidence.
caller=(C/'candidate/real_pilot_import_caller.py').read_text()
fn=next(n for n in ast.parse(caller).body if isinstance(n,ast.FunctionDef) and n.name=='execute')
s=ast.get_source_segment(caller,fn)
markers=['verify(run,graph,role)','from .real_pilot_partial_progress import MCMProgress','archive_dispatch.preflight(','resource_binding.open_first(','original_import_stage.attach(','activate(execution,']
positions=[s.index(m) for m in markers];need(positions==sorted(positions),'startup order')
stream=(C/'candidate/mcm_score_stream.py').read_text()
need(stream.index('terminal = self.active.finish()')<stream.index('head = tail.seal(')<stream.index('self.active = None',stream.index('head = tail.seal(')),'closed callback lifetime')
seal=(C/'candidate/score_tail.py').read_text();part=seal[seal.index('def _terminal'):seal.index('def finish')]
need(part.index('self.durability_barrier()')<part.index("batch._write(self.fd, 'terminal.json'")<part.index('self.close()'),'durable before closed tail')
report={'schema_version':1,'status':'PASS_BOUNDED_SOURCE_COMPOSITION','exact_bodies':17,'runtime_replacements':11,'runtime_additions':3,'metadata_bodies':3,'destination_overlaps':0,'exact_patch_reconstructed':True,'dependency_path_only_rebinds':sorted(changed),'candidate_manifest_sha256':sha(C/'MANIFEST01.json'),'install_map_sha256':sha(C/'INSTALL_MAP01.json'),'author_focused_check_sha256':sha(C/'CHECK01.json'),'author_actual_check':read(C/'ACTUAL_CHECK01.json'),'actual_cli_refusal':{'exit_code':call.returncode,'last_stderr_line':call.stderr.strip().splitlines()[-1]},'startup_marker_order':markers,'source_only_no_numerical_imports':True,'reused_parent_reviews':read(C/'REUSED_ACCEPTANCE01.json')}
(HERE/'CHECK01.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:report[k] for k in ('status','exact_bodies','runtime_replacements','runtime_additions','exact_patch_reconstructed','actual_cli_refusal')},sort_keys=True))
