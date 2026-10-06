"""Only the final genuine June6 count/manifest/allocation delta; metadata only."""
from pathlib import Path
import copy,hashlib,json,stat,types,traceback
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];F=HERE.parent
sha=lambda x:hashlib.sha256(x).hexdigest()
READS={}
def need(x,m):
 if not x:raise ValueError(m)
def read(p,pin=None):
 p=Path(p);p=p if p.is_absolute() else ROOT/p
 need(p.suffix=='.json' and not p.is_symlink() and 0<p.stat().st_size<=4*1024**2,'bounded compact JSON only')
 raw=p.read_bytes();h=sha(raw)
 if pin:need(h==pin,'pinned metadata differs: '+str(p))
 READS[str(p.relative_to(ROOT))]=h
 return json.loads(raw)
def ref(p):
 p=Path(p);p=p if p.is_absolute() else ROOT/p
 need(p.suffix=='.json' and not p.is_symlink() and p.stat().st_size<=4*1024**2,'compact metadata reference only')
 b=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'bytes':len(b),'sha256':sha(b)}
def save(name,v):
 p=HERE/name;need(not p.exists(),'fresh output only');p.write_text(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n');return ref(p)
prior=F/'real-data-pilot-current-graph-counts04-2026-10-06'
read(prior/'MANIFEST01.json','7725acb8f053287049805a6e21ccf58b4d4d6d3b1f11d93332fb8d57da92e8b3')
old=read(prior/'INPUT_DRAFT01.json','2cf12d267e8f52d2cb86a669a825e84fa04b1140e9b5cc39366ce193dd563180')
oldreviewpath=F/'real-data-pilot-current-graph-counts04-review01-2026-10-06/REVIEW01.json';oldreview=read(oldreviewpath)
need(READS[str(oldreviewpath.relative_to(ROOT))].startswith('43399e22') and oldreview['decision']=='accepted-six-count-draft-delta-only','previous delta not accepted')
proofpath=F/'real-data-pilot-sixth-graph-bodyproof01-2026-10-06/BODY_HASH01.json'
proof=read(proofpath,'ebab6695dfc9c33fe01537fbbf0b6a4fef7829238272e50eaedebaa8036fb88f')
passpath=proofpath.parent/'ACTUAL_PASS_TOOL01.json';actual=read(passpath)
need(actual['body_proof']['sha256']==sha(proofpath.read_bytes()) and actual['actual_tool_exit_code']==0,'Root genuine pass link differs')
identity='eth-paper-real-pilot-graph-20220606-20261005-01';week='2022-06-06T00:00:00Z'
completepath=ROOT/'research_runs'/identity/'complete.json';complete=read(completepath,'14cd212dbc4062c274038a060c6035594090057d84d60627fefb4b32f530eef8')
claimpath=completepath.parent/'claim.json';claim=read(claimpath,'89198aa4122144e6754ca9a1b65b65997cf19c12d0bef8d3f3790a49ac92515a')
need(complete['status']=='complete' and complete['claim_sha256']==sha(claimpath.read_bytes()) and complete['experiment_id']==identity and proof['identity']==identity and proof['status']=='passed','genuine completed identity differs')
mp=ROOT/proof['manifest']['path'];manifest=read(mp,'dfca930e8f7daf3f4a17096360b20925f0473a8cd297c00943d06f627ec8487f')
need(manifest['metadata']['start_utc']==week and manifest['metadata']['asset']=='ETH','June6 calendar differs')
need(proof['nodes']==1581761 and proof['edges']==2355230 and len(proof['arrays'])==5,'Root count differs')
statjoins=[]
for name,d in manifest['arrays'].items():
 a=proof['arrays'][name];p=mp.parent/d['path'];s=p.lstat()
 sig=[s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,stat.S_IMODE(s.st_mode)]
 need(a['path']==str(p.relative_to(ROOT)) and a['sha256']==d['sha256'] and a['bytes']==d['bytes'],'manifest/body descriptor differs')
 need(stat.S_ISREG(s.st_mode) and not p.is_symlink() and sig==a['stat_identity_before']==a['stat_identity_after'],'current original stat differs')
 statjoins.append({'path':a['path'],'stat_identity':sig,'body_read':False})
arraybytes=sum(a['bytes'] for a in manifest['arrays'].values());need(arraybytes==429403880,'array sum differs')
need(proof['arrays']['node_features']['header']['shape']==[1581761,4] and proof['arrays']['edge_index']['header']['shape']==[2,2355230],'retained original headers differ')
count={'schema_version':1,'kind':'graph-node-count-metadata-v1','graph_manifest_sha256':proof['manifest']['sha256'],'node_features_sha256':manifest['arrays']['node_features']['sha256'],'rows':proof['nodes'],'method':'retained-header-only','evidence':ref(proofpath)}
countref=save('JUNE6_COUNT_DRAFT01.json',count)
p=F/'real-data-pilot-feature-integration-successor01-2026-10-06/successor01.py';raw=p.read_bytes();need(sha(raw)=='710fac4de18630fccdb6aa1531c09c4026a78d8ae38db77285b59720556edd72','accepted source changed')
successor=types.ModuleType('accepted_successor');successor.__file__=str(p);exec(compile(raw,str(p),'exec'),successor.__dict__)
selected=successor.load('selected');draft=copy.deepcopy(old)
need(draft['graphs'][week] is None and draft['protocol']['typed_allocations']['by_week'][week] is None,'previous absent slot differs')
draft['graphs'][week]={'role':'graph_20220606','manifest':ref(mp),'node_count':countref}
draft['protocol']['typed_allocations']['by_week'][week]=selected.kind_alloc(proof['nodes'])
inverse=copy.deepcopy(draft);inverse['graphs'][week]=None;inverse['protocol']['typed_allocations']['by_week'][week]=None
need(inverse==old,'more than authorized two data slots changed')
inputref=save('INPUT_DRAFT01.json',draft)
# All-seven actual validator reads compact metadata only, not arrays or prices.
b=successor.load('builder');graphs=b.graphs(ROOT,draft['graphs']);need(len(graphs)==7,'seven metadata graph joins failed')
sequences=b.sequences(graphs);need(len(sequences)==16 and all(len(x)==28 for x in sequences),'original16x28 sequence differs')
typed,totals,minima=b.typed_budget(graphs,draft['protocol']['typed_allocations'])
try:successor.prepare(ROOT,draft)
except Exception as e:
 failure={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
else:raise AssertionError('null current physical baseline unexpectedly accepted')
# No fabricated baseline is used to probe beyond this refusal.
need(draft['protocol']['physical_baseline']=={'allocated_bytes':None,'entries':None,'evidence':None,'logical_bytes':None},'baseline was filled')
oldscalars=read(prior/'SCALAR_TOTALS01.json');by=copy.deepcopy(oldscalars['by_week']);n=proof['nodes']
by[week]={'nodes':n,'motif_cells':32*n,'tail_f64_record_bytes':80*32*n,'batch_f64_value_bytes':8*32*n,'output_f32_bytes':4*32*n,'original_graph_array_bytes':arraybytes}
sums={k:sum(v[k] for v in by.values()) for k in by[week]}
save('SCALAR_TOTALS01.json',{'status':'SEVEN_GRAPH_SCALAR_SUMS_NOT_CAPACITY','by_week':by,'seven_graph_totals':sums,'motifs':32,'original_samples_spent':512,'decisions':16,'lookback':28,'typed_only_transfer_reservation_lower_bounds':totals,'typed_minima':minima,'pair_archive_and_controls_not_in_typed_total':True,'baseline_and_admission':None})
save('INDEX_DRAFT01.json',{'status':'SEVEN_AUTHENTIC_COUNT_SLOTS_DRAFT_NOT_ADMITTED','prior_six':ref(prior/'INDEX_DRAFT01.json'),'prior_six_review':ref(oldreviewpath),'graphs':draft['graphs'],'june6_count':countref,'missing_count_weeks':[],'input_draft':inputref,'independent_june6_outcome_review':None,'june6_external_recovery':None})
save('JUNE6_PROVENANCE01.json',{'identity':identity,'claim':ref(claimpath),'complete':ref(completepath),'body_proof':ref(proofpath),'actual_pass_link':ref(passpath),'status':'complete','nodes':n,'edges':proof['edges'],'array_bytes':arraybytes,'current_five_array_stats':statjoins,'independent_outcome_review':None,'external_recovery_review':None,'qualification':'Root actual original one-pass evidence and stat joins, not independent outcome/recovery acceptance or scientific authority.'})
save('PREPARE_REFUSAL01.json',failure)
save('DELTA01.json',{'prior_input':ref(prior/'INPUT_DRAFT01.json'),'new_input':inputref,'paths_changed':['graphs.'+week,'protocol.typed_allocations.by_week.'+week],'exact_inverse_equal':True,'earlier_six_slots_unchanged':True,'protected_june13_refs_and_old_failed_may30_distinction_unchanged':True,'protocol_caps_unchanged':True})
save('CHECK01.json',{'status':'PASS_NEW_METADATA_DELTA_ONLY','genuine_seven_graph_validator_passed':True,'original_sequences':'16x28 availability checked','typed_budget_validator_passed':True,'next_prepare_refusal':failure['message'],'physical_baseline_still_null':True,'no_payload_header_reads_or_numerical_imports':True,'independent_june6_outcome_and_recovery_pending':True})
save('READ_EVIDENCE01.json',READS)
print(json.dumps({'status':'PASS_METADATA_ONLY','seven_totals':sums,'next_refusal':failure['message']}))
