from pathlib import Path
import json,hashlib,importlib.util,os
D=Path(__file__).resolve().parent;F=D.parent.parent;M=F.parents[2];C=F/'real-data-pilot-fourth-graph-get-duplicates-retirement01-2026-10-06'
def h(p):
 assert p.stat().st_size<=4*1024**2
 return hashlib.sha256(p.read_bytes()).hexdigest()
request=C/'RELEASE_REQUEST01.json';assert h(request)=='8ce5a908d34b2747fc6e6b396a5e6ddbf061f6704f18ba9476e524d5dd40e5ad';r=json.loads(request.read_bytes())
p=C/'retire01.py';assert h(p)==h(F/'real-data-pilot-fourth-graph-get-duplicates-retirement-preparation01-2026-10-06/retire01.py')==r['entry_sha256']=='4aa566c261529e8e1e665f3b40edc59f06d1d6ddf1dc56ac7a7b3f1fa0dc9fa7'
spec=importlib.util.spec_from_file_location('reviewed_five_get_source',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert m.ROOT==M and m.HERE==C
assert r['decision'] is r['retire_only_five_verified_array_get_duplicates'] is None and r['retirement_identity']==m.ID
c=json.loads(m.metadata(M,r['selection']['path'],r['selection']['sha256']));assert r['selection']['sha256']=='858057233ff574ceecdaf463be15abb9d129eb8fcdfd054c0b9f8fbe2735bdf3'
for rel,sha in r['evidence'].items():m.metadata(M,rel,sha)
for rel,sha in c['evidence'].items():assert r['evidence'][rel]==sha
m.recovery(M,c); originals,gets=m.selected(M,c)
proof=json.loads((D.parent/'RECOVERED_PAYLOAD_HASH01.json').read_bytes());proofs={x['index']:x for x in proof['files']}
for row in c['rows']:
 q=proofs[row['index']];assert q['sha256']==row['recovered']['sha256'] and q['bytes']==row['recovered']['bytes'] and q['stat_identity']==row['recovered']['stat_identity'] and q['recovered_path']==row['recovered']['path'] and q['original_path']==row['original']['path']
assert not any(os.path.lexists(M/x) for x in c['removed_ledger_paths'])
assert not any(os.path.lexists(C/x) for x in ['attempt01.json','complete01.json','failed01.json'])
root=json.loads(m.metadata(M,c['recovery_basis']['ledger_root']['path']));assert root['actual_root_tool_session']==35126 and root['actual_root_completion_chunk']=='cc49b4' and root['actual_remote_head']==root['source_commit']=='a328c30899dc30ef8ad99d200571b5be3d216a65' and root['actual_push_exit_code']==root['actual_remote_readback_exit_code']==0 and root['actual_root_exit_code']==0
S=M/m.BACKUP;final=json.loads(m.metadata(M,m.BACKUP+'/guard01/final.json'));terminal=json.loads(m.metadata(M,m.BACKUP+'/ROOT_TERMINAL01.json'));assert not Path(final['cgroup']).exists() and final['cleanup_verified'] is True and all(not Path('/proc',str(x)).exists() for x in terminal['actual_selected_recorded_pids'])
result={'request_sha256':h(request),'entry_sha256':h(p),'selection_sha256':r['selection']['sha256'],'evidence_hashes_matched':len(r['evidence']),'actual_source_predicates':['recovery','selected'],'original_array_count':len(originals),'recovered_get_count':len(gets),'retirement_bytes':c['retire_bytes'],'retirement_paths':[str(x.relative_to(M)) for x in gets],'ledger_terminal':root,'independent_six_body_proof_reused_sha256':h(D.parent/'RECOVERED_PAYLOAD_HASH01.json'),'payload_reads':0,'retirement_execution':False,'inactive_native_subprocess_not_run_by_review':True,'one_use_namespace_absent':True}
(D/'BINDING_CHECK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':True,'evidence':len(r['evidence']),'retirement_bytes':c['retire_bytes'],'payload_reads':0}))
