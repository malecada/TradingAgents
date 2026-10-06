from pathlib import Path
import json,hashlib,stat
D=Path(__file__).resolve().parent;F=D.parent.parent;M=F.parents[2];B=F.parent
C=F/'real-data-pilot-fourth-graph-post-recovery-retirement01-2026-10-06';R=C/'RELEASE_REQUEST01.json';S=B/'storage/real-pilot-fourth-graph-preservation-20261006-01'
def h(p):
 assert p.stat().st_size<=4*1024**2
 return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
 b=p.read_bytes();assert p.lstat()==s;return json.loads(b)
assert h(R)=='1165d0f9dfcccf5612a78469b679ff9e70c58441857e670cb447d5fb960e875a';r=read(R)
assert r['decision'] is r['full_scope_byte_recovery'] is r['retire_only_fourth_graph_ledger_and_successful_get'] is None
assert r['retirement_identity']=='real-pilot-fourth-graph-ledger-retirement-20261006-01'
assert h(C/'retire01.py')==h(F/'real-data-pilot-fourth-graph-post-recovery-retirement-preparation01-2026-10-06/retire01.py')==r['entry_sha256']=='ff206eb781a5755c85da234d5f6dd6d9fb2d6e85bb47aea64cb1bc246a27b4c1'
for rel,sha in r['evidence'].items():
 p=M/rel;assert not Path(rel).is_absolute() and '..' not in Path(rel).parts;assert h(p)==sha
out=read(M/r['backup_outcome_review']['path']);assert out['decision']=='accepted' and out['full_scope_byte_recovery'] is True and out['identity']==S.name
for rel,sha in r['evidence'].items():
 if rel.startswith(str(S.relative_to(M))):assert out['evidence'][rel]==sha
c=read(S/'complete.json');sel=read(S/'selection01.json');assert c==read(S/'recovered-complete.json') and c['selection']==sel and c['count']==len(c['files'])==36 and c['bytes_preserved']==sel['total_bytes']==3720766030
assert 'directories' not in c and len(sel['directories'])==8
row=sel['files'][11];kept=read(S/'11-kept.json');assert c['files'][11]==kept and all(kept[k]==v for k,v in row.items());assert row['bytes']==3218829312 and row['path']=='research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-real-pilot-graph-20220523-20261005-01/aggregation/ledger.sqlite'
original=M/row['path'];recovered=S/'11-recovered.bin'
def sig(p):
 s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1;return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
assert sig(original)==row['stat_identity'];hashproof=read(D.parent/'RECOVERED_PAYLOAD_HASH01.json');proof=next(x for x in hashproof['files'] if x['index']==11);assert sig(recovered)==proof['stat_identity'] and proof['sha256']==row['sha256'] and proof['bytes']==row['bytes']
assert not original.with_name(original.name+'.remote.json').exists();assert not any((C/n).exists() for n in ['attempt01.json','complete01.json','failed01.json'])
final=read(S/'guard01/final.json');outer=read(S/'outer-exit01.json');root=read(S/'ROOT_TERMINAL01.json');assert final['phase']=='complete' and final['child_exit_code']==outer['entry_selected_exit_code']==outer['guard_child_exit_code']==root['actual_root_tool_exit_code']==0 and final['cleanup_verified'] is outer['cleanup_verified'] is True
assert not Path(final['cgroup']).exists() and all(not Path('/proc',str(pid)).exists() for pid in root['actual_selected_recorded_pids']) and not (S/'failed.json').exists()
result={'request_sha256':h(R),'entry_sha256':r['entry_sha256'],'accepted_outcome_sha256':r['backup_outcome_review']['sha256'],'compact_evidence_hashes_matched':len(r['evidence']),'original_stat_identity':row['stat_identity'],'recovered_stat_identity':proof['stat_identity'],'recovered_body_sha256_reused':proof['sha256'],'recovered_body_proof_sha256':h(D.parent/'RECOVERED_PAYLOAD_HASH01.json'),'retirement_paths':[row['path'],str(recovered.relative_to(M))],'retirement_bytes':6437658624,'retirement_namespace_absent':True,'source_execution_not_performed':True,'payload_reads':0}
(D/'BINDING_CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
