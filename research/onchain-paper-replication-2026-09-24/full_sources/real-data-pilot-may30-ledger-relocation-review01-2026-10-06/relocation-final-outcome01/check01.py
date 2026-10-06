from pathlib import Path
import hashlib,json,os,stat,subprocess,ast
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';T=F/'real-data-pilot-may30-ledger-relocation01-2026-10-06';O=Path(__file__).resolve().parent
E={}
def body(p,h=None):
 assert p.resolve(strict=True)==p and p.is_file() and p.stat().st_nlink==1 and p.stat().st_size<4*1024**2
 b=p.read_bytes();d=hashlib.sha256(b).hexdigest()
 if h:assert d==h,(str(p),d,h)
 E[str(p.relative_to(R))]=d;return b
def obj(p,h=None):return json.loads(body(p,h))
def sig(p):
 assert p.resolve(strict=True)==p
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
 return [s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,stat.S_IMODE(s.st_mode)]
def put(n,v):(O/n).write_text(json.dumps(v,indent=2)+'\n')
cp='50f98a6b9729e9eabf035243260e583f59b59a42ce8c73a1d849cc9b03e959e8';bp='c66ac207901db2c2eff695114fa31db22827ef01fc48bd8286abedf644237472'
c=obj(T/'retire-complete01.json',cp);b=obj(T/'relocation-receipt01.json',bp);r=obj(T/'retire-ROOT_TERMINAL01.json','0f35421f30da399365eb932bcd6c6be39389cd6cbd413607996ca31429c4ce0b');x=obj(T/'retire-outer-exit01.json');p=obj(T/'retire-preflight01.json');env=obj(T/'retire-envelope01.json','21c829f2176d92fddeef3279ea26001277e685d8da06074a444ac599734df47e');rel=obj(T/'retire-RELEASE_REVIEW01.json','64546ee231cb22b8946d1cc7d062226cf1d4cc425c28418604b7bd14d24e17a1');s=obj(T/'SELECTION01.json');q=obj(T/'copy-complete01.json',c['copy_receipt']['sha256'])
assert c['copy_receipt']==rel['copy_receipt'] and c['copy_review']==rel['copy_review']
for k in ['copy_receipt','copy_review','copy_native','copy_outer','copy_root']:body(R/rel[k]['path'],rel[k]['sha256'])
assert r['actual_root_tool_exit_code']==r['actual_parent_exit_code']==x['entry_selected_exit_code']==0
assert r['retire_complete_sha256']==cp and r['relocation_receipt_sha256']==bp and r['native_child_used'] is False
assert x['guard_phase'] is x['guard_child_exit_code'] is x['cleanup_verified'] is x['fatal_type'] is None
assert p['head']==r['source_commit']=='852f4669c0cebfb7e24ed0399e76f4797a211eb4' and p['envelope_sha256']==rel['envelope_sha256']
for path,h in env['source_files'].items():body(R/path,h)
for name in ['entry01.py','relocate-retire02.py','retire-envelope01.json','retire-RELEASE_REVIEW01.json']:
 path=T/name;assert hashlib.sha256(subprocess.check_output(['git','show',p['head']+':'+str(path.relative_to(R))],cwd=R)).hexdigest()==E[str(path.relative_to(R))]
for n in ['retire-launch-attempt01.json','retire-attempt01.json']:obj(T/n)
assert not (T/'retire-failed01.json').exists()
assert c['original']==q['original'] and c['target']==q['target']==b['target']
assert b['original']=={k:c['original'][k] for k in ['path','bytes','sha256']}
assert c['source_retired'] is c['original_retired'] is c['two_partial_arrays_retained'] is b['original_retired'] is True
assert c['original_parent_status']=='failed' and b['predecessor']==q['predecessor'] and b['original_source']==q['original_source'] and b['original_claim_sha256']==q['original_claim_sha256']
assert not os.path.lexists(R/c['original']['path'])
t=Path(b['target']['path']);ts=sig(t);assert ts==b['target']['stat_identity'] and set(z.name for z in t.parent.iterdir())=={'ledger.sqlite'} and ts[0]==66307 and R.stat().st_dev==66310
partial=[]
for row in s['recovery_selection']['rows'][1:]:
 a=row['original'];v=sig(R/a['path']);assert [v[i] for i in [0,1,3,4,5]]==a['stat_identity'] and v[6]==a['mode'];partial.append({'path':a['path'],'stat_identity7':v})
for path,h in s['recovery_selection']['evidence'].items():
 if path.endswith('/failed.json') or 'postmortem-cells' in path:body(R/path,h)
proof=b['retirement_evidence'];assert proof=={'path':str((T/'retire-complete01.json').relative_to(R)),'sha256':cp}
review={'decision':'accepted','identity':b['identity'],'predecessor':b['predecessor'],'relocation_receipt_sha256':bp,'complete_copy_recovery_and_retirement':True,'evidence':E,'original_parent_status':'failed','original_graph_status':'unavailable','original_path_absent':True,'destination_stat_identity7':ts,'two_original_partial_arrays_retained':True,'actual_root_exit_code':0,'actual_outer_exit_code':0,'native_child_used':False,'original_outer_native_fields':{'guard_phase':None,'guard_child_exit_code':None,'cleanup_verified':None},'qualification':'Actual full COPY readback and historical external BYTE recovery inherited from exact accepted proofs; final review reads metadata and current stats only. No writer exclusion grant, database consistency, complete graph, capacity, future remote availability, research admission or numerical release.'}
# Actual installed pure metadata predicate, extracted without importing empirical module or executing its producer.
source=R/'tradingagents/research/onchain_replication/graph_ledger_continuation.py';tree=ast.parse(source.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='relocation_metadata')
ns={'json':json,'Path':Path,'need':lambda ok,msg:None if ok else (_ for _ in ()).throw(ValueError(msg)),'sha':lambda raw:hashlib.sha256(raw).hexdigest(),'OLD':b['predecessor'],'FIXED':{'old_claim':{'sha256':b['original_claim_sha256']}},'EXTERNAL':t,'DATA_DEVICE':66307}
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),ns)
assert ns['relocation_metadata']({'new_experiment_id':b['identity'],'ledger':b['original']},(T/'relocation-receipt01.json').read_bytes(),json.dumps(review).encode())==b
put('CHECK01.json',{'decision':'pass','actual_original_path_absent':True,'destination_stat_identity7':ts,'partial_arrays':partial,'actual_retire_native_fields_null':True,'source_commit':p['head'],'entry_envelope_release_helper_committed':True,'installed_consumer_metadata_predicate_passed':True,'real_payload_reads':0,'SQL_or_numerical_imports':0})
E[str((O/'CHECK01.json').relative_to(R))]=hashlib.sha256((O/'CHECK01.json').read_bytes()).hexdigest()
put('RELOCATION_REVIEW01.json',review)
print(json.dumps({'decision':'accepted','review_sha256':hashlib.sha256((O/'RELOCATION_REVIEW01.json').read_bytes()).hexdigest(),'real_payload_reads':0}))
