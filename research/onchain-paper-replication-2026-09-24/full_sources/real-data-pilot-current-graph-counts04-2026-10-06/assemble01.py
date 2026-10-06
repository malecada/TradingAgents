"""Fixed six-count metadata successor; never reads array/price/raw bodies."""
from pathlib import Path
import copy,hashlib,json,stat,types
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];F=HERE.parent
SHA=lambda b:hashlib.sha256(b).hexdigest()
READS={}
def need(v,m):
 if not v:raise ValueError(m)
def read(path,expected=None):
 p=Path(path);p=p if p.is_absolute() else ROOT/p
 need(p.suffix=='.json' and p.is_file() and not p.is_symlink() and p.stat().st_size<=4*1024**2,'bounded JSON metadata only')
 raw=p.read_bytes();h=SHA(raw)
 if expected:need(h==expected,'metadata source changed: '+str(p))
 READS[str(p.relative_to(ROOT))]=h
 return json.loads(raw)
def ref(path):
 p=Path(path);p=p if p.is_absolute() else ROOT/p
 raw=p.read_bytes();need(p.suffix=='.json' and len(raw)<=4*1024**2,'metadata reference only')
 return {'path':str(p.relative_to(ROOT)),'bytes':len(raw),'sha256':SHA(raw)}
def write(name,body):
 p=HERE/name;need(not p.exists(),'fresh output required: '+name);p.write_text(json.dumps(body,sort_keys=True,indent=2,allow_nan=False)+'\n');return ref(p)
def load(path,pin):
 raw=path.read_bytes();need(SHA(raw)==pin,'accepted metadata preparer changed')
 m=types.ModuleType(path.stem);m.__file__=str(path);exec(compile(raw,str(path),'exec'),m.__dict__);return m
idx=read(F/'real-data-pilot-current-graph-counts03-2026-10-06/INDEX_DRAFT01.json')
read(idx['prior_four_counts']['path'],idx['prior_four_counts']['sha256'])
oldpath=F/'real-data-pilot-feature-policy-successor-preparation01-2026-10-06/draft01/INPUT_DRAFT01.json'
old=read(oldpath);draft=copy.deepcopy(old)
proofpath=F/'real-data-pilot-may30-ledger-continuation-bodyproof01-2026-10-06/BODY_HASH01.json'
proof=read(proofpath,'0a503d5637c4a6d53e7916b9def287add75d2bdff8e48a38964c32585870d82a')
reviewroot=F/'real-data-pilot-may30-ledger-relocation-review01-2026-10-06/continuation-actual-outcome01'
br=read(reviewroot/'BODY_REVIEW01.json','5fae826efe05f4e574a85f2c45d42ac52dd087d7d75acc317cad32ed7fba3caa')
outcome=read(reviewroot/'OUTCOME_REVIEW01.json','22b233e1777601c9c6dfc567cef711b539b92281eaabfc246e27d4bec9a75bd6')
recoverypath=F/'real-data-pilot-may30-continuation-preservation-outcome-review01-2026-10-06/REVIEW01.json'
recovery=read(recoverypath,'95d4589ad2d27af249867a7ebf0529e54fc8e5fbb6256d6a692f04b0d4da4455')
identity='eth-paper-real-pilot-may30-ledger-continuation-20261006-01'
need(proof['status']=='passed' and br['decision']=='pass' and outcome['decision']=='accepted','actual complete graph proofs required')
need(proof['identity']==br['identity']==outcome['identity']==identity,'continuation identity differs')
need(outcome['status']=='complete' and outcome['original_failed_parent_retained'] is True and outcome['source_rows_inherited']==7507236 and outcome['source_rows_redecoded']==0 and outcome['admitted_count']==3548344,'failed/continuation source separation differs')
need(recovery['decision']=='accepted' and recovery['identity']=='real-pilot-may30-continuation-preservation-20261006-01' and recovery['full_scope_byte_recovery'] is True and recovery['count']==24,'actual new increment recovery required')
mp=ROOT/proof['manifest']['path'];manifest=read(mp,'a856a6134263a0b04e3365a2a35f9c7a96792b4739274ad80b2155545eba5830')
need(outcome['graph_manifest_sha256']==proof['manifest']['sha256'],'outcome/manifest join differs')
need(proof['nodes']==1581441 and proof['edges']==2426106 and proof['bytes_read']==br['total_bytes']==432741928,'actual scalar totals differ')
body_by_path={row['path']:row for row in br['files']};statjoins=[]
for key,desc in manifest['arrays'].items():
 a=proof['arrays'][key];need(a['path']==str((mp.parent/desc['path']).relative_to(ROOT)) and a['sha256']==desc['sha256'] and a['bytes']==desc['bytes'],'manifest/body join differs')
 r=body_by_path[a['path']];need(r['sha256']==a['sha256'] and r['bytes']==a['bytes'] and r['header']==a['header'],'independent body/header join differs')
 p=ROOT/a['path'];s=p.lstat();sig=[s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,stat.S_IMODE(s.st_mode)]
 need(stat.S_ISREG(s.st_mode) and not p.is_symlink() and sig==a['stat_identity_after']==a['stat_identity_before'],'current original array stat differs')
 statjoins.append({'path':a['path'],'stat_identity':sig,'body_read':False})
need(proof['arrays']['node_features']['header']['shape']==[1581441,4] and proof['arrays']['edge_index']['header']['shape']==[2,2426106],'original retained headers differ')
count={'schema_version':1,'kind':'graph-node-count-metadata-v1','graph_manifest_sha256':proof['manifest']['sha256'],'node_features_sha256':manifest['arrays']['node_features']['sha256'],'rows':proof['nodes'],'method':'retained-header-only','evidence':ref(proofpath)}
countref=write('MAY30_COUNT_DRAFT01.json',count)
week='2022-05-30T00:00:00Z';need(draft['graphs'][week] is None,'old missing May30 must remain explicit ancestry')
draft['graphs'][week]={'role':'graph_20220530','manifest':ref(mp),'node_count':countref}
# Existing accepted pure integer allocator, unchanged route/chunk settings/caps.
successorpath=F/'real-data-pilot-feature-integration-successor01-2026-10-06/successor01.py'
successor=load(successorpath,'710fac4de18630fccdb6aa1531c09c4026a78d8ae38db77285b59720556edd72')
selected=successor.load('selected')
need(draft['protocol']['typed_allocations']['by_week'][week] is None,'old typed slot differs')
draft['protocol']['typed_allocations']['by_week'][week]=selected.kind_alloc(proof['nodes'])
handoffpath=F/'real-data-pilot-june13-protected-reuse-handoff01-2026-10-06/draft01/HANDOFF_DRAFT01.json'
handoff=read(handoffpath,'3a37be3209a66df05e6f98cf5626900207f75943aa10c083c4ca209c62b9b838')
need(handoff['original_parent_status']=='failed' and handoff['original_graph_component_status']=='complete' and handoff['modern_original_producer_plan'] is None,'June13 distinctions differ')
legacy={}
for role,v in handoff['registered_input_templates'].items():
 p=ROOT/v['path'];need(p.is_file() and not p.is_symlink(),'legacy compact reference missing')
 value={'path':v['path'],'sha256':v['sha256'],'bytes':p.stat().st_size}
 need(role not in draft['protocol']['references'],'legacy role collision')
 draft['protocol']['references'][role]=value;legacy[role]=value
need(len(legacy)==21 and draft['graphs']['2022-06-13T00:00:00Z']['manifest']==legacy['graph_20220613'],'June13 graph alias differs')
# Six known manifests/counts only. No numeric/opaque import/price references are opened.
rows={};graphs={};b=successor.load('builder')
for w,g in draft['graphs'].items():
 if g is None:continue
 m=read(g['manifest']['path'],g['manifest']['sha256']);n=read(g['node_count']['path'],g['node_count']['sha256'])
 need(m['metadata']['start_utc']==w and m['metadata']['asset']=='ETH' and m['metadata']['graph_config_hash']==b.GRAPH_CONFIG,'graph calendar/config differs')
 need(n['graph_manifest_sha256']==g['manifest']['sha256'] and n['node_features_sha256']==m['arrays']['node_features']['sha256'] and n['method']=='retained-header-only','count/manifest join differs')
 need(set(m['arrays'])=={'node_ids','node_features','edge_index','edge_features','edge_aggregates'},'five array roster differs')
 rows[w]={'nodes':n['rows'],'motif_cells':32*n['rows'],'tail_f64_record_bytes':80*32*n['rows'],'batch_f64_value_bytes':8*32*n['rows'],'output_f32_bytes':4*32*n['rows'],'original_graph_array_bytes':sum(a['bytes'] for a in m['arrays'].values())}
 graphs[w]={'graph_hash':m['graph_hash'],'role':g['role'],'manifest':g['manifest'],'node_count':g['node_count']}
need(len(rows)==6 and draft['graphs']['2022-06-06T00:00:00Z'] is None,'six known/one absent required')
# Exact inverse of data transformation: only May30 graph/allocation and21 fixed reuse refs.
inverse=copy.deepcopy(draft);inverse['graphs'][week]=None;inverse['protocol']['typed_allocations']['by_week'][week]=None
for role in legacy:del inverse['protocol']['references'][role]
need(inverse==old,'unrequested policy/reference change')
inputref=write('INPUT_DRAFT01.json',draft)
try:successor.prepare(ROOT,draft)
except ValueError as exc:reason=str(exc)
else:raise AssertionError('absent June6 unexpectedly admitted')
need(reason=='missing genuine graph/count metadata: 2022-06-06T00:00:00Z','wrong first missing prerequisite: '+reason)
write('INDEX_DRAFT01.json',{'status':'SIX_GENUINE_COUNTS_DRAFT_NOT_ADMISSION','prior_five_counts':ref(F/'real-data-pilot-current-graph-counts03-2026-10-06/INDEX_DRAFT01.json'),'graphs':graphs,'missing_weeks':['2022-06-06T00:00:00Z'],'may30_count':countref,'input_draft':inputref})
write('MAY30_PROVENANCE01.json',{'original_failed_identity':'eth-paper-real-pilot-graph-20220530-20261005-01','original_status':'failed','original_graph_status':'unavailable','original_source_cell_status':'complete','new_identity':identity,'new_status':'complete','raw_rows_inherited':7507236,'admitted_rows':3548344,'nodes':1581441,'edges':2426106,'array_bytes':432741928,'original_body_proof':ref(proofpath),'independent_body_review':ref(reviewroot/'BODY_REVIEW01.json'),'independent_outcome':ref(reviewroot/'OUTCOME_REVIEW01.json'),'actual_increment_recovery':ref(recoverypath),'current_original_stat_joins':statjoins,'no_original_parent_upgrade':True})
write('JUNE13_REUSE_INPUTS01.json',{'status':'EXACT_ACCEPTED_ROLE_TEMPLATES_NOT_AUTHORITY','handoff':ref(handoffpath),'registered_input_templates':legacy,'original_provenance_roles':19,'coverage_and_graph_alias_roles':2,'parent_status':'failed','component_status':'complete','before_owner_check_required':True})
write('SCALAR_TOTALS01.json',{'status':'SIX_GRAPH_SCALAR_SUMS_NOT_CAPACITY','by_week':rows,'six_graph_totals':{k:sum(v[k] for v in rows.values()) for k in next(iter(rows.values()))},'seventh_graph':None,'motifs':32,'original_samples_spent':512,'decisions':16,'lookback':28,'tail_bytes_are_record_bytes_not_ram_or_network_total':True,'full_seven_totals':None})
write('CHECK01.json',{'status':'PASS_METADATA_ONLY','known_graphs':6,'first_prepare_refusal':reason,'unchanged_protocol_inverse':True,'changes':['new May30 complete manifest/count slot','May30 count-derived typed allocation under unchanged formula','21 accepted June13 provenance/coverage/alias references'],'payload_header_reads':0,'payload_hash_passes':0,'numerical_imports':False,'root_remaining':['genuine June6 complete manifest and accepted original header/body-derived count plus outcome/recovery','count-derived June6 typed allocation under same accepted formula','fresh physical baseline, current source/runtime, endpoint, complete finite control allocations and independent final input/release review; downstream checks not bypassed']})
write('READ_EVIDENCE01.json',READS)
print(json.dumps({'status':'PASS_METADATA_ONLY','known_graphs':6,'missing':'2022-06-06T00:00:00Z','nodes':sum(v['nodes'] for v in rows.values()),'array_bytes':sum(v['original_graph_array_bytes'] for v in rows.values()),'prepare_refusal':reason}))
