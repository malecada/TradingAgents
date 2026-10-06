"""Independent delta-only metadata check. Never opens payload bodies or active outputs."""
from pathlib import Path
import copy,hashlib,json,stat
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];F=HERE.parent
C=F/'real-data-pilot-current-graph-counts04-2026-10-06'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def need(v,m):
 if not v:raise AssertionError(m)
def ref(r):
 p=ROOT/r['path'];need(p.suffix=='.json' and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'metadata pin');return read(p)
need(sha(C/'MANIFEST01.json')=='7725acb8f053287049805a6e21ccf58b4d4d6d3b1f11d93332fb8d57da92e8b3','candidate identity')
for name,pin in read(C/'MANIFEST01.json')['members'].items():
 p=C/name;need(p.stat().st_size==pin['bytes'] and sha(p)==pin['sha256'],'member '+name)
old=read(F/'real-data-pilot-feature-policy-successor-preparation01-2026-10-06/draft01/INPUT_DRAFT01.json');new=read(C/'INPUT_DRAFT01.json')
w='2022-05-30T00:00:00Z';missing='2022-06-06T00:00:00Z'
need(len(new['graphs'])==7 and sum(x is not None for x in new['graphs'].values())==6 and new['graphs'][missing] is None,'six/seven cardinality')
need(new['protocol']['typed_allocations']['by_week'][missing] is None,'missing allocation')
legacy=read(C/'JUNE13_REUSE_INPUTS01.json');handoff=ref(legacy['handoff']);templates=legacy['registered_input_templates']
need(len(templates)==21 and set(templates)==set(handoff['registered_input_templates']),'legacy cardinality')
for role,v in templates.items():
 need(v['path']==handoff['registered_input_templates'][role]['path'] and v['sha256']==handoff['registered_input_templates'][role]['sha256'] and v==new['protocol']['references'][role],'legacy descriptor delta')
 need((ROOT/v['path']).stat().st_size==v['bytes'],'legacy descriptor size')
need(templates['graph_20220613']==new['graphs']['2022-06-13T00:00:00Z']['manifest'],'graph alias')
inverse=copy.deepcopy(new);inverse['graphs'][w]=None;inverse['protocol']['typed_allocations']['by_week'][w]=None
for role in templates:del inverse['protocol']['references'][role]
need(inverse==old,'unrequested draft change')
prov=read(C/'MAY30_PROVENANCE01.json');proof=ref(prov['original_body_proof']);br=ref(prov['independent_body_review']);outcome=ref(prov['independent_outcome']);recovery=ref(prov['actual_increment_recovery'])
need(proof['identity']==br['identity']==outcome['identity']==prov['new_identity'] and proof['status']=='passed' and br['decision']=='pass' and outcome['decision']=='accepted' and outcome['status']=='complete','continuation acceptance')
need(recovery['decision']=='accepted' and recovery['count']==24 and recovery['full_scope_byte_recovery'] is True,'increment recovery acceptance')
count=ref(new['graphs'][w]['node_count']);manifest=ref(new['graphs'][w]['manifest'])
need(count['rows']==proof['nodes']==outcome['nodes']==1581441 and proof['edges']==outcome['edges']==2426106,'new dimensions')
need(count['graph_manifest_sha256']==new['graphs'][w]['manifest']['sha256']==proof['manifest']['sha256']==outcome['graph_manifest_sha256'],'manifest link')
need(count['node_features_sha256']==manifest['arrays']['node_features']['sha256']==proof['arrays']['node_features']['sha256'] and count['evidence']==prov['original_body_proof'],'count source')
need(proof['arrays']['node_features']['header']['shape']==[count['rows'],4],'retained node header')
need(proof['bytes_read']==br['total_bytes']==prov['array_bytes']==432741928,'new byte total')
body={x['path']:x for x in br['files']}
for row in prov['current_original_stat_joins']:
 a=next(x for x in proof['arrays'].values() if x['path']==row['path']);r=body[row['path']]
 need(r['sha256']==a['sha256'] and r['header']==a['header'] and r['bytes']==a['bytes'],'accepted body join')
 s=(ROOT/row['path']).lstat();sig=[s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,stat.S_IMODE(s.st_mode)]
 need(stat.S_ISREG(s.st_mode) and sig==row['stat_identity']==a['stat_identity_before']==a['stat_identity_after'],'stat join')
need(len(prov['current_original_stat_joins'])==5,'five original files')
failed=read(C/'ORIGINAL_FAILED_PARENT01.json');ref(failed['original_claim']);ref(failed['original_terminal'])
need(failed['status']=='failed' and failed['no_status_upgrade'] and outcome['original_failed_parent_retained'] and prov['original_status']=='failed' and prov['original_graph_status']=='unavailable' and prov['original_source_cell_status']=='complete','original failure separation')
need(outcome['source_rows_redecoded']==0 and outcome['source_rows_inherited']==prov['raw_rows_inherited']==7507236 and outcome['admitted_count']==prov['admitted_rows']==3548344,'inherited denominator')
# Independent integer partition reconstruction of accepted allocator, no module execution.
cells=32*count['rows'];chunk=65536;part=4194240;outpart=4194304
sizes=[min(chunk,cells-i) for i in range(0,cells,chunk)]
ceil=lambda n,d:(n+d-1)//d
expected={'score-tail-f64':{'chunk_bytes':part,'max_preserved_bytes':80*cells,'max_recovered_bytes':80*cells,'max_operations':len(sizes),'max_chunks':2*sum(ceil(80*n,part) for n in sizes)},'score-batch-f64':{'chunk_bytes':outpart,'max_preserved_bytes':8*cells,'max_recovered_bytes':8*cells,'max_operations':len(sizes)+1,'max_chunks':2*len(sizes)},'mcm-output-f32':{'chunk_bytes':outpart,'max_preserved_bytes':4*cells,'max_recovered_bytes':1,'max_operations':1,'max_chunks':ceil(4*cells,outpart)}}
need(expected==new['protocol']['typed_allocations']['by_week'][w],'typed allocation')
index=read(C/'INDEX_DRAFT01.json');totals=read(C/'SCALAR_TOTALS01.json');computed={}
for week,g in new['graphs'].items():
 if g is None:continue
 n=read(ROOT/g['node_count']['path']);m=read(ROOT/g['manifest']['path'])
 need(index['graphs'][week]==dict(g,graph_hash=m['graph_hash']),'index mapping')
 computed[week]={'nodes':n['rows'],'motif_cells':32*n['rows'],'tail_f64_record_bytes':80*32*n['rows'],'batch_f64_value_bytes':8*32*n['rows'],'output_f32_bytes':4*32*n['rows'],'original_graph_array_bytes':sum(x['bytes'] for x in m['arrays'].values())}
need(computed==totals['by_week'] and totals['six_graph_totals']=={k:sum(v[k] for v in computed.values()) for k in next(iter(computed.values()))},'scalar sums')
need(totals['full_seven_totals'] is None and totals['seventh_graph'] is None,'unknown seventh')
actual=read(C/'ACTUAL_CHECK01.json');need(actual['actual_cli']=={'exit_code':1,'expected_refusal':'missing genuine graph/count metadata: '+missing,'tool_chunk':'375a25'},'retained CLI receipt')
result={'status':'PASS_DELTA_ONLY_METADATA_REVIEW','known_graphs':6,'weekly_slots':7,'missing_weeks':[missing],'unchanged_prior_slots':5,'new_may30_nodes':count['rows'],'new_may30_edges':proof['edges'],'new_may30_array_bytes':proof['bytes_read'],'protected_june13_descriptors':21,'current_stat_only_joins':5,'unchanged_inverse':True,'independently_reconstructed_typed_allocation':expected,'six_graph_totals':totals['six_graph_totals'],'author_cli_reused_not_repeated':actual['actual_cli'],'payload_reads':0,'header_reads':0,'numerical_imports':False}
(HERE/'CHECK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','known_graphs','weekly_slots','new_may30_nodes','current_stat_only_joins','unchanged_inverse']}))
