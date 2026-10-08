"""Concrete fixed21 metadata successor; reuse accepted fixed20 helpers."""
import copy,datetime,hashlib,json,subprocess,types
from pathlib import Path
R=Path.cwd();H=Path(__file__).resolve().parent;F=H.parent;O=F/'real-data-pilot-final20-2026-10-08'
OLD='eth-paper-real-data-end-to-end-resource-20261008-20';N='eth-paper-real-data-end-to-end-resource-20261008-21'
NS0='ethpilot-20261008-20';NS='ethpilot-20261008-21'
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(R)),'sha256':sha(p),'bytes':p.stat().st_size}
def save(p,v):
 with p.open('xb') as f:f.write((json.dumps(v,indent=2,sort_keys=True)+'\n').encode())
def module(p):
 m=types.ModuleType(p.stem);m.__file__=str(p)
 if p.name=='real_pilot_storage.py':m.__package__='tradingagents.research.onchain_replication'
 exec(compile(p.read_bytes(),str(p),'exec'),vars(m));return m
def rename(v):return json.loads(json.dumps(v).replace(OLD,N).replace(NS0,NS))
assert not (R/'research_runs'/N).exists() and not (H/'launch-attempt01.json').exists()
T=H/'templates02';draft=load(H/'INPUT_DRAFT01.json');refs=draft['protocol']['references'];pair=load(T/'pair_policy01.json');anchor=pair['numerical_source']['commit'];pins=pair['numerical_source']['files'];previous=load(O/'templates02/pair_policy01.json')['numerical_source'];changes={p:{'before':previous['files'][p],'after':h} for p,h in pins.items() if h!=previous['files'][p]}
prepared=module(F/'real-data-pilot-fixed21-metadata-successor01-2026-10-08/successor04.py').prepare(R,draft);old_inventory=load(O/'PREPARATION_RESULT06.json')['inventory'];assert {k:v for k,v in prepared['inventory'].items() if k not in ('total_with_declared_baseline','storage_budget_unchanged')}=={k:v for k,v in old_inventory.items() if k not in ('total_with_declared_baseline','storage_budget_unchanged')};assert rename(old_inventory['storage_budget_unchanged'])==prepared['inventory']['storage_budget_unchanged'];save(H/'PREPARATION_RESULT01.json',prepared)
request=load(O/'TRANSPORT_REQUEST06.json');request['prepared']=ref(H/'PREPARATION_RESULT01.json');request['archive_policy']=refs['archive_policy'];parent=R/'research_artifacts/real_pilot_runtime/pilot-transport-20261008-21-01';parent.mkdir(mode=0o700);request['private_parent']=str(parent.relative_to(R));save(H/'TRANSPORT_REQUEST01.json',request)
binder=module(F/'real-data-pilot-transport-binding-preparation01-2026-10-06/bind01.py');bound=binder.bind(R,request);save(H/'TRANSPORT_BINDING01.json',bound);I=H/'inputs01';I.mkdir();inputrefs={}
for role,v in bound['inputs'].items():p=I/(role+'.json');p.write_bytes(binder.raw(v));inputrefs[role]=ref(p)
inputrefs.update(bound['private_input']);save(H/'INPUT_REFS01.json',inputrefs)
pre=(O/'preflight03.py').read_text().replace(OLD,N).replace('gate03.json','gate01.json').replace('BINDING02.json','BINDING01.json').replace('RELEASE_REVIEW02.json','RELEASE_REVIEW01.json').replace('effective_attempt_budget!=91','effective_attempt_budget!=92').replace("'effective_attempt_budget':91","'effective_attempt_budget':92")
pre=pre.replace('real-data-pilot-fixed20-metadata-successor01-2026-10-08/successor04.py','real-data-pilot-fixed21-metadata-successor01-2026-10-08/successor04.py')
marker='    # Scalar/header-only capacity refusal precedes torch inventory and RootIO.\n';assert pre.count(marker)==1
pre=pre.replace(marker,"""    # Validate the genuine resource-owner schema before graph loading or reservation.
    from tradingagents.research.onchain_replication.matching_owner import _pair_limits
    pair_limits=json.loads(read_path(ROOT/admission.inputs['pair_policy']['path']))['limits']
    compact_limits=json.loads(read_path(ROOT/admission.inputs['compact_policy']['path']))['stage_policy']['pair']
    need(pair_limits==compact_limits,'resource-owner and compact limits differ')
    _pair_limits(pair_limits,resource=True)
"""+marker)
(H/'preflight01.py').write_text(pre);root=(O/'root_io03.py').read_text().replace(OLD,N).replace('from preflight03 import check','from preflight01 import check');(H/'root_io.py').write_text(root)
(H/'CHARTER01.md').write_text((O/'CHARTER01.md').read_text().replace(OLD,N).replace(NS0,NS)+'\nThis successor corrects resource-owner metadata validation only; the frozen diagnostic and full end-to-end objective remain unchanged.\n')
save(H/'NUMERICAL_CONTEXT_REANCHOR01.json',{'source':anchor,'previous':previous['commit'],'files':len(pins),'changed':changes,'qualification':'Exact current package-source join; accepted scientific method/protocol and diagnostic unchanged. Fresh21 resource-owner adapter accepted separately. No new numerical execution.'})
save(H/'PREPARATION_EXIT01.json',{'status':'DRAFT_NOT_ADMITTED','identity':N,'source_anchor':anchor,'inputs':len(inputrefs),'inventory_unchanged':True,'claim':False,'reservation':False})
print(json.dumps({'status':'DRAFT_NOT_ADMITTED','identity':N,'source_anchor':anchor,'source_pins':len(pins),'inputs':len(inputrefs),'new_allocated_growth':prepared['inventory']['new_logical_bytes']+prepared['inventory']['allocation_overhead_bytes']}))
