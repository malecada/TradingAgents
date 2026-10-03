"""Read exact selected source and whitelisted receipt JSON; never binary scores/arrays."""
import ast,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[4];O=Path(__file__).resolve().parent
P=R/'research/onchain-paper-replication-2026-09-24/full_sources/original-import-native-successor-preparation06-2026-10-03';C=P/'capsule04';ID='original-import-native-success-20261003-04'
def read(p,limit=1048576):
 assert p.resolve()==p and p.stat().st_size<=limit and p.suffix in ('.json','.py','.md','.log')
 return p.read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
ret_raw=read(P/'RETAINED_PRIMARY01.json',2097152);ret=json.loads(ret_raw);members={r['path']:r for r in ret['members']}
execution=json.loads(read(P/'EXECUTION_PRIMARY01.json'));assert sha(ret_raw)==execution['retention_sha256']
claim_path=f'research_runs/{ID}/claim.json';claim_raw=read(C/claim_path);assert sha(claim_raw)==execution['claim_sha256'];claim=json.loads(claim_raw)
source_files=claim['experiment']['source_files'];source_rows=[]
names=['onchain_replication/'+n+'.py' for n in ['compact_mcm','compact_matcher','compact_pair_log','score_tail','mcm_score_stream','imported_mcm_identity','original_import_stage','original_import_preparation','original_dictionary','matching_owner','environment','compact_owner','matching_checkpoint','matching_annealing','resource_binding','import_metadata','job']]+['admission.py','lifecycle.py','verify.py','budget_extensions.py']
for name in names:
 path='tradingagents/research/'+name;b=read(C/path);assert sha(b)==source_files[path]
 tree=ast.parse(b);source_rows.append({'path':path,'sha256':sha(b),'bytes':len(b),'definitions':[{'name':n.name,'line':n.lineno} for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.ClassDef))]})
def method(module,cls,name):
 tree=ast.parse(read(C/('tradingagents/research/onchain_replication/'+module+'.py')))
 if cls:tree=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls)
 return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
def calls(node,value):return sum(isinstance(n,ast.Call) and ast.unparse(n.func)==value for n in ast.walk(node))
assert calls(method('original_import_preparation','PreparedImport','execution_contract'),'self._check')==2
assert calls(method('original_import_preparation','PreparedImport','execution_contract'),'self.stage_contract')==1
assert calls(method('original_import_preparation','PreparedImport','stage_contract'),'self._check')==1
assert calls(method('original_import_stage','ImportStage','lease'),'self.prepared._check')==1
assert calls(method('compact_matcher','CompactMatcher','_check'),'self.lease')==1
assert calls(method('compact_matcher','CompactMatcher','_check'),'self.log._check')==1
assert calls(method('compact_pair_log','PairLog','_check'),'self.lease')==1
assert calls(method('matching_owner','Binding','lease'),'self._guard')==2
assert calls(method('original_dictionary','ImportedOriginal','_check'),'self._lease')==2
observed=[];json_refs=[]
for name,row in members.items():
 if ID not in name or not ('/compact/' in name or '/sources/' in name or '/onchain_compact_mcm/' in name):continue
 p=C/name;assert p.stat().st_size==row['bytes'] if row['kind']=='file' else p.is_dir()
 item={k:row[k] for k in ('path','kind','bytes','sha256') if k in row};item['mtime_ns']=p.stat().st_mtime_ns
 if row['kind']=='file' and p.suffix=='.json' and p.name in {'start.json','intent.json','import-complete.json','failed.json','import-target-01.json','import-target-02.json'}:
  b=read(p);assert sha(b)==row['sha256'];value=json.loads(b)
  item['metadata_keys']=sorted(value);item['safe_fields']={k:value[k] for k in ('status','kind','id','resource_only','rows','motifs','chunk_cells','cells','completed_pairs','phase') if k in value};json_refs.append(name)
 observed.append(item)
inputs=claim['experiment']['inputs'];input_rows=[]
for name,v in inputs.items():
 path=C/v['path'];input_rows.append({'name':name,'path':v['path'],'bytes_from_stat_only':path.stat().st_size,'registered_sha256':v['sha256']})
source_extent=sum((C/k).stat().st_size for k in source_files)
anchor=json.loads(read(C/'fixture_inputs/success/anchor.json')) if (C/'fixture_inputs/success/anchor.json').exists() else None
# No retained .bin/.npy payload is opened, hashed or decoded by this script.
v={'schema_version':1,'source':claim['source'],'identity':ID,'claim_sha256':sha(claim_raw),'retained_inventory_sha256':sha(ret_raw),'retained_members':len(members),'retained_files':ret['files'],'retained_directories':ret['directories'],'retained_logical_bytes':ret['logical_bytes'],'source_count':len(source_files),'source_bytes_stat_only':source_extent,'registered_inputs':input_rows,'registered_input_bytes_stat_only':sum(r['bytes_from_stat_only'] for r in input_rows),'selected_source_rows':source_rows,'observed_metadata':observed,'authenticated_whitelisted_json':json_refs,'binary_payloads_read':0,'static_successful_path_lower_counts_per_matcher_check':{'target_leases':2,'prepared_checks':8,'original_validations':8,'original_role_body_reads':176,'membership_canonical_calls':4352,'membership_comparisons':131072,'full_binding_checks':8,'minimum_binding_leases_from_prepared_checks':24,'minimum_guard_checks_from_those_leases':48},'actual_timing_breakdown':None,'lookup_failure_preserved':'Initial exploratory lookup treated retained.files integer as an iterable; corrected to retained.members; no source/outcome changed.'}
(O/'census01.json').write_text(json.dumps(v,indent=2)+'\n')
print(json.dumps({k:v[k] for k in ['source','retained_members','retained_files','retained_directories','source_count','source_bytes_stat_only','registered_input_bytes_stat_only','binary_payloads_read','static_successful_path_lower_counts_per_matcher_check']},sort_keys=True))
