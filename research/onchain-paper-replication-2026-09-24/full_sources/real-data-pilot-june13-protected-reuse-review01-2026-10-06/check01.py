from pathlib import Path
import ast,copy,hashlib,json,stat,sys,types
D=Path(__file__).resolve().parent;F=D.parent;M=F.parents[2];C=F/'real-data-pilot-june13-protected-reuse-handoff01-2026-10-06';evidence={}
def raw(p):
 s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
 b=p.read_bytes();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==tuple(getattr(p.lstat(),k) for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns'));evidence[str(p.relative_to(M))]=hashlib.sha256(b).hexdigest();return b
def read(p):return json.loads(raw(p))
manifest=read(C/'MANIFEST01.json');assert evidence[str((C/'MANIFEST01.json').relative_to(M))]=='21dcd4d42d452c360c3bb5ec6243095d92433521253045276179bdb393a67fe5'
for name,pin in manifest['files'].items():assert hashlib.sha256(raw(C/name)).hexdigest()==pin
for path,pin in read(C/'SOURCE_EVIDENCE01.json').items():assert hashlib.sha256(raw(M/path)).hexdigest()==pin
inv=read(C/'INVERSE01.json');before=raw(M/inv['baseline']);after=raw(C/'candidate/real_pilot_import_caller.py');text=after.decode()
for edit in reversed(inv['edits']):assert text.count(edit['after'])==1;text=text.replace(edit['after'],edit['before'])
assert text.encode()==before and len(inv['edits'])==2
pkg=types.ModuleType('june13_review_metadata');pkg.__path__=[];sys.modules[pkg.__name__]=pkg
def module(name,path):
 m=types.ModuleType(pkg.__name__+'.'+name);m.__package__=pkg.__name__;sys.modules[m.__name__]=m;exec(compile(raw(path),str(path),'exec'),vars(m));return m
legacy=module('graph_legacy_coverage',M/'tradingagents/research/onchain_replication/graph_legacy_coverage.py');helper=module('adapter',C/'candidate/real_pilot_legacy_graph.py');d=read(C/'draft01/HANDOFF_DRAFT01.json');inputs=d['registered_input_templates'];assert len(inputs)==21 and len(legacy.EVIDENCE)==19
assert helper.registered(inputs,{helper.GRAPH_KEY:'graph_20220613'})==set(inputs)-{'graph_20220613'}
blobs={}
for role,ref in inputs.items():b=raw(M/ref['path']);assert hashlib.sha256(b).hexdigest()==ref['sha256'];blobs[role]=b
# Independent changed-seam refusals, no runtime authority fixture.
for mutation in ('missing_coverage','wrong_coverage'):
 x=copy.deepcopy(inputs)
 if mutation=='missing_coverage':del x['legacy_graph_evidence']
 else:x['legacy_graph_evidence']['sha256']='f'*64
 try:helper.registered(x,{helper.GRAPH_KEY:'graph_20220613'})
 except ValueError:pass
 else:raise AssertionError(mutation+' accepted')
assert d['status']=='DRAFT_NOT_ADMITTED' and all(v is None for v in d['future_root_bindings'].values()) and d['modern_original_producer_plan'] is None
ref=d['reuse_evidence']['accepted_count_manifest'];cm=read(M/ref['path']);assert hashlib.sha256((M/ref['path']).read_bytes()).hexdigest()==ref['sha256'];proofref=d['reuse_evidence']['five_body_proof'];body=read(M/proofref['path']);assert hashlib.sha256((M/proofref['path']).read_bytes()).hexdigest()==proofref['sha256'] and body['decision']=='pass'
countref=d['count_ref'];count=read(M/countref['path']);assert hashlib.sha256((M/countref['path']).read_bytes()).hexdigest()==countref['sha256'] and count['rows']==1768268
for ref in (proofref,countref):assert cm['members'][Path(ref['path']).name]['sha256']==ref['sha256']
gmanifest=json.loads(blobs['legacy_graph_manifest']);assert gmanifest['graph_hash']==helper.GRAPH_KEY
stats=[]
for row in body['files']:
 p=M/row['path'];s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==row['mode'];sig=[s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns];assert sig==row['stat_identity'];r=gmanifest['arrays'][p.stem];assert r['bytes']==row['bytes']==s.st_size and r['sha256']==row['sha256'] and r['path']==p.name;stats.append({'path':row['path'],'stat_identity':sig,'sha256_inherited':row['sha256']})
assert len(stats)==5 and {Path(x['path']).stem for x in stats}==set(gmanifest['arrays'])
# Pure metadata verifier only: authentic 19 inputs, no Runner/GraphSnapshot authority claim.
result=legacy.verify_legacy_coverage(json.loads(blobs['legacy_graph_evidence']),types.SimpleNamespace(**gmanifest['metadata']),inputs['graph_20220613']['sha256'],blobs.__getitem__);assert result['parent_status']=='failed' and result['graph_cell_status']=='complete' and result['member_count']==7
caller=ast.parse(after);functions={n.name:ast.unparse(n) for n in caller.body if isinstance(n,ast.FunctionDef)};execute=functions['execute'];assert execute.index('verify(run, graph, role)')<execute.index('resource_binding.open_first(')<execute.index('original_import_stage.attach(')<execute.index('activate(execution,')
assert 'from .real_pilot_legacy_graph import registered' in functions['admitted']
verify=next(n for n in ast.parse(raw(C/'candidate/real_pilot_legacy_graph.py')).body if isinstance(n,ast.FunctionDef) and n.name=='verify');v=ast.unparse(verify);assert 'type(run) is ResearchRun' in v and 'type(graph) is GraphSnapshot' in v and 'verify_legacy_coverage(proof, graph,' in v and 'run.read_input' in v
assert not any(n in sys.modules for n in ('numpy','torch','scipy','pyarrow'))
out={'decision':'pass-source-metadata-only','two_exact_caller_inverse_hunks':True,'authentic_input_roles':21,'original_roles':19,'missing_wrong_coverage_refused':True,'existing_pure_validator':result,'arrays_stat_only':stats,'runtime_type_guards_source_inspected_not_executed':True,'helper_import_before_owner_and_authority_snapshot':True,'future_authority_null':True,'payload_header_reads':0,'numeric_imports':False,'evidence':evidence}
(D/'CHECK01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('evidence','arrays_stat_only')}))
