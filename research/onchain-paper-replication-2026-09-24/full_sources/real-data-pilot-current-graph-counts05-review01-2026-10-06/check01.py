"""Independent seventh-count delta: compact metadata and five lstat calls only."""
from pathlib import Path
import copy,hashlib,json,stat
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];F=HERE.parent
C=F/'real-data-pilot-current-graph-counts05-2026-10-06';P=F/'real-data-pilot-current-graph-counts04-2026-10-06'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def need(v,m):
 if not v:raise AssertionError(m)
def ref(r):
 p=ROOT/r['path'];need(p.suffix=='.json' and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'metadata pin');return read(p)
need(sha(C/'MANIFEST01.json')=='ab9255c02a79e73f9da405e89a4c315ef2ae3a7fa4e0b95ccbf511e92114b5cc','candidate manifest')
for name,pin in read(C/'MANIFEST01.json')['members'].items():
 p=C/name;need(p.stat().st_size==pin['bytes'] and sha(p)==pin['sha256'],'member '+name)
need(sha(P/'INPUT_DRAFT01.json')=='2cf12d267e8f52d2cb86a669a825e84fa04b1140e9b5cc39366ce193dd563180','accepted prior input')
need(sha(F/'real-data-pilot-current-graph-counts04-review01-2026-10-06/REVIEW01.json')=='43399e22eae69e1c95a67f4f366aabe37f8229b75fd3d73d8e279c62a639dbbd','prior review')
old=read(P/'INPUT_DRAFT01.json');new=read(C/'INPUT_DRAFT01.json');w='2022-06-06T00:00:00Z'
need(len(new['graphs'])==7 and all(new['graphs'].values()),'seven populated slots')
inverse=copy.deepcopy(new);inverse['graphs'][w]=None;inverse['protocol']['typed_allocations']['by_week'][w]=None
need(inverse==old,'only two authorized changes')
prov=read(C/'JUNE6_PROVENANCE01.json');proof=ref(prov['body_proof']);actual=ref(prov['actual_pass_link']);complete=ref(prov['complete']);claim=ref(prov['claim'])
need(complete['status']=='complete' and complete['claim_sha256']==prov['claim']['sha256'] and complete['experiment_id']==proof['identity']==prov['identity'],'genuine terminal join')
need(actual['body_proof']['sha256']==prov['body_proof']['sha256'] and actual['actual_tool_exit_code']==0,'actual proof link')
R=F/'real-data-pilot-sixth-graph-outcome-preservation-review01-2026-10-06'
need(sha(R/'OUTCOME_REVIEW01.json')=='a2b28ba34081505db793469663c6cbcbc8c74a25f539d5577ceb03173a3449ea','outcome acceptance')
need(sha(R/'BODY_REVIEW01.json')=='a8731acab16ecaaa80476d3a19125ee0602c9ff5a3dcb33255171a83fcf635ac','body acceptance')
outcome=read(R/'OUTCOME_REVIEW01.json');body=read(R/'BODY_REVIEW01.json')
need(outcome['decision']=='accepted' and outcome['status']=='complete' and outcome['identity']==prov['identity'] and outcome['terminal_sha256']==prov['complete']['sha256'] and outcome['claim_sha256']==prov['claim']['sha256'],'accepted identity join')
need(outcome['source']=='483f92786c5076ec6f6ad0bffa894b8b36653797' and body['decision']=='pass' and body['body_proof']['sha256']==prov['body_proof']['sha256'],'accepted source/proof')
count=ref(new['graphs'][w]['node_count']);manifest=ref(new['graphs'][w]['manifest'])
need(count['rows']==proof['nodes']==outcome['nodes']==1581761 and proof['edges']==outcome['edges']==2355230,'dimensions')
need(count['graph_manifest_sha256']==new['graphs'][w]['manifest']['sha256']==proof['manifest']['sha256'],'manifest identity')
need(count['evidence']==prov['body_proof'] and count['node_features_sha256']==manifest['arrays']['node_features']['sha256']==proof['arrays']['node_features']['sha256'],'count identity')
need(proof['arrays']['node_features']['header']['shape']==[count['rows'],4] and proof['arrays']['edge_index']['header']['shape']==[2,2355230],'retained header dimensions')
need(sum(x['bytes'] for x in manifest['arrays'].values())==429403880,'array scalar bytes')
reviewed={x['path']:x for x in body['files']};need(len(prov['current_five_array_stats'])==5,'stat roster')
for row in prov['current_five_array_stats']:
 a=next(x for x in proof['arrays'].values() if x['path']==row['path']);r=reviewed[row['path']]
 need(r['sha256']==a['sha256'] and r['header']==a['header'] and r['bytes']==a['bytes'],'independent retained body join')
 s=(ROOT/row['path']).lstat();sig=[s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,stat.S_IMODE(s.st_mode)]
 need(stat.S_ISREG(s.st_mode) and sig==row['stat_identity']==a['stat_identity_before']==a['stat_identity_after'] and sig==r['stat_identity']+[r['mode']],'stat signature')
# Independent partition arithmetic, unchanged accepted constants.
cells=32*count['rows'];chunk=65536;part=4194240;outpart=4194304
sizes=[min(chunk,cells-i) for i in range(0,cells,chunk)];ceil=lambda n,d:(n+d-1)//d
expected={'score-tail-f64':{'chunk_bytes':part,'max_preserved_bytes':80*cells,'max_recovered_bytes':80*cells,'max_operations':len(sizes),'max_chunks':2*sum(ceil(80*n,part) for n in sizes)},'score-batch-f64':{'chunk_bytes':outpart,'max_preserved_bytes':8*cells,'max_recovered_bytes':8*cells,'max_operations':len(sizes)+1,'max_chunks':2*len(sizes)},'mcm-output-f32':{'chunk_bytes':outpart,'max_preserved_bytes':4*cells,'max_recovered_bytes':1,'max_operations':1,'max_chunks':ceil(4*cells,outpart)}}
need(new['protocol']['typed_allocations']['by_week'][w]==expected,'typed allowance')
oldtot=read(P/'SCALAR_TOTALS01.json');tot=read(C/'SCALAR_TOTALS01.json');by=copy.deepcopy(oldtot['by_week']);by[w]={'nodes':count['rows'],'motif_cells':cells,'tail_f64_record_bytes':80*cells,'batch_f64_value_bytes':8*cells,'output_f32_bytes':4*cells,'original_graph_array_bytes':429403880}
need(tot['by_week']==by and tot['seven_graph_totals']=={k:sum(v[k] for v in by.values()) for k in by[w]},'scalar totals')
need(new['protocol']['physical_baseline']=={'evidence':None,'allocated_bytes':None,'logical_bytes':None,'entries':None} and new['protocol']['typed_allocations']['max_control_bytes'] is None,'missing prerequisites changed')
need(prov['external_recovery_review'] is None and prov['independent_outcome_review'] is None,'historical missing refs filled')
refusal=read(C/'PREPARE_REFUSAL01.json');typed=read(C/'INITIAL_NULL_CONTROL_REFUSAL01.json');receipt=read(C/'ACTUAL_CHECK01.json')
need(refusal['message']=='exact file reference required' and "base['evidence']" in refusal['traceback'] and typed['actual_value'] is None and typed['reason']=='finite positive integer required','refusal cause')
need(receipt['metadata_assembly_and_actual_cli_tool']=='f33c75' and receipt['actual_cli_exit_code']==1 and typed['tool_chunk']=='99ea78' and typed['exit_code']==1,'actual retained refusal receipts')
result={'status':'PASS_SEVENTH_COUNT_DELTA_ONLY','changed_slots':['graphs.'+w,'protocol.typed_allocations.by_week.'+w],'exact_inverse':True,'graph_count':7,'prior_slots_unchanged':6,'june6_nodes':count['rows'],'june6_edges':proof['edges'],'stat_only_joins':5,'typed_allocation':expected,'seven_scalar_totals':tot['seven_graph_totals'],'accepted_outcome_sha256':sha(R/'OUTCOME_REVIEW01.json'),'accepted_body_sha256':sha(R/'BODY_REVIEW01.json'),'outcome_reference_in_candidate':None,'recovery_reference_in_candidate':None,'reused_refusals':['f33c75 missing physical_baseline.evidence','99ea78 null max_control_bytes'],'payload_or_header_reads':0,'numerical_imports':False,'release':False}
(HERE/'CHECK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','exact_inverse','graph_count','stat_only_joins','seven_scalar_totals']}))
