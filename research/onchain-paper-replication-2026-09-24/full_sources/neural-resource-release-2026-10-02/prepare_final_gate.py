from pathlib import Path
import json,hashlib,subprocess,copy
root=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
out=root/'research/onchain-paper-replication-2026-09-24/full_sources/neural-resource-release-2026-10-02'
prep=root/'research/onchain-paper-replication-2026-09-24/full_sources/neural-resource-registration-2026-10-02/revision03'
phys=root/'research/onchain-paper-replication-2026-09-24/full_sources/neural-resource-physical-implementation-2026-10-02'
smoke=phys/'os-smoke-execution01'
def pin(p):return {'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def save(name,value):
 with (out/name).open('x') as f:json.dump(value,f,sort_keys=True,indent=2);f.write('\n')
wrapped=json.loads((prep/'gate-candidate02.NONEXECUTABLE.json').read_bytes());registry=copy.deepcopy(wrapped['registry_candidate']);identity=wrapped['experiment_id'];exp=registry['experiments'][identity]
text=(prep/'CHARTER.candidate02.md').read_text().replace('# Neural-only capacity measurement — candidate charter','# Neural-only capacity measurement — registered charter')
text=text.replace('This draft is nonexecutable. It proposes one new retained-data resource claim','This charter freezes one new retained-data resource claim')
text=text.replace('under the reviewed cumulative 62-slot allocation proposal.','under the reviewed cumulative 62-slot allocation.')
text=text.replace('Proposed hard whole-job controls remain','Registered hard whole-job controls remain')
text=text.replace('This candidate selects the proposed version1 physical policy:','This charter selects the independently accepted version1 physical policy:')
text=text.replace('ceilings are proposed refusal','ceilings are registered refusal')
text += '''\n\n## Final source and release bindings\n\nThe exact gate.json freezes the complete dynamic package and parent research\nsource hashes, runtime-helper hashes, unchanged model/plan/configuration, actual\nworkspace/environment, accepted62 extension/review/allocation and all original\n48 metadata/provenance inputs. The selected physical source is independently\naccepted. One separately reviewed invented-payload systemd test observed the\n64KiB log limit, kernel memory controls and inactive cleaned-up unit, preserving\nall raw receipts. Its success establishes the exercised containment mechanism;\nthe original nine real graph populations still require this capacity measurement.\n\nThe prospective6GiB worker/5GiB high/3GiB host reserve/9GiB startup,10GiB disk\nfloor,7200-second whole-job ceiling and600-second cooperative cell budgets are\nunchanged. The8MiB file/256KiB JSON/160MiB allocated/128MiB logical/128entries/\n32MiB tail limits remain finite refusal ceilings. No fit, graph/model change,\nthreshold relaxation or success guarantee follows from engineering observations.\n\nThe original new adopter remains eth-paper-neural-resource-20261002-01 and consumes\nonly the single neural resource allocation. No historical identity is relaunched.\nNo namespace is reserved by this document. Execution requires committed gate/\ncharter/source, final independent release review, actual lifecycle admission and\nfresh host/input/guard checks. Full claim and nested authority request encoding\nmust both fit256KiB. Registered readers and worker revalidate original numerical\narray bytes under the live guard before use. All failed/remaining cells stay in\nthe denominator; parent loss retains the explicitly qualified recovery limits.\n'''
with (out/'CHARTER.md').open('x') as f:f.write(text)
job=(prep/'execution-job.candidate.json').read_bytes()
with (out/'execution-job.json').open('xb') as f:f.write(job)
exp['charter']=pin(out/'CHARTER.md');exp['inputs']['execution_job']={**pin(out/'execution-job.json'),'dataset':'eth'}
paths=sorted(list((root/'tradingagents/research/onchain_replication').glob('*.py'))+list((root/'tradingagents/research').glob('*.py'))+[root/'tradingagents/__init__.py'])
exp['source_files']={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
exp['runtime_hashes']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'tradingagents/research').glob('*.py'))}
extra=[out/'CHARTER.md',out/'execution-job.json',phys/'REVIEW_FINAL.md',phys/'os-smoke-preparation/REVIEW_CANDIDATE02.md',smoke/'spec.json',smoke/'smoke.py',smoke/'REVIEW_RELEASE.md',smoke/'result01.json']
extra += [root/x['path'] for x in wrapped['required_source_pins']]
for item in exp['inputs'].values():
 p=root/item['path'];assert pin(p)['sha256']==item['sha256'],str(p)
 if subprocess.run(['git','ls-files','--error-unmatch','--',item['path']],cwd=root,capture_output=True).returncode==0:extra.append(p)
for p in extra:exp['source_files'][str(p.relative_to(root))]=pin(p)['sha256']
assert len(exp['cells'])==len(exp['windows'])==9
assert exp['parent']==wrapped['registry_candidate']['experiments'][identity]['parent']
save('gate.json',registry)
source='0'*40
claim={'schema_version':1,'program_id':registry['program_id'],'experiment_id':identity,'started_at':'2026-10-02T23:59:59.123456+00:00','source':source,'registration':str((out/'gate.json').relative_to(root)),'registration_sha256':pin(out/'gate.json')['sha256'],'design_source':source,'bindings':None,'bindings_sha256':None,'inputs':exp['inputs'],'family':registry['families'][exp['family']],'experiment':exp,'effective_attempt_budget':62,'windows':[{**w,'identity':registry['datasets'][w['dataset']]['identity'],'state':'exposed'} for w in exp['windows']],'prior_exposures':[{**x,'identity':d['identity']} for d in registry['datasets'].values() for x in d['exposures']]}
enc=lambda v:(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
claim_bytes=len(enc(claim));rpc_bytes=len(enc({'anchor_sha256':'0'*64,'op':'claim','value':claim}));assert max(claim_bytes,rpc_bytes)<262144
save('preparation02.json',{'gate':pin(out/'gate.json'),'charter':pin(out/'CHARTER.md'),'job':pin(out/'execution-job.json'),'science_or_model_changed':False,'cells':9,'windows':9,'input_count':len(exp['inputs']),'source_pin_count':len(exp['source_files']),'complete_dynamic_python_count':len(paths),'claim_preview_bytes':claim_bytes,'rpc_preview_bytes':rpc_bytes,'json_limit_bytes':262144,'qualification':'Exact prospective claim shape, placeholder40-character commit and maximal6-digit microsecond timestamp. Actual committed admission and exact claim/RPC measurement remain before launch. Source/code numerical arrays were not executed. No experiment roots reserved.'})
with (out/'prepare_final_gate.py').open('x') as f:f.write(Path(__file__).read_text())
print(json.dumps({'gate_sha256':pin(out/'gate.json')['sha256'],'source_count':len(exp['source_files']),'claim_preview_bytes':claim_bytes,'rpc_preview_bytes':rpc_bytes}))
