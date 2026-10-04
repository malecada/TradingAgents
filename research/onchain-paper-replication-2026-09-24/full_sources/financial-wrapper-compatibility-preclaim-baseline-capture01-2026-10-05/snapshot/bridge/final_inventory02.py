from pathlib import Path
import hashlib,importlib.util,json,stat
H=Path(__file__).resolve().parent;B=H.parent;P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01')
p=P/'preclaim01.py';assert hashlib.sha256(p.read_bytes()).hexdigest()=='557b7bcb38b48e3bf1e9e5b5b1eae25ab4908b8567820e17700dc08774b48d16';s=importlib.util.spec_from_file_location('_final_known_reader',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
x=json.loads((H/'INVENTORY_BOUND01.json').read_bytes());r=m.Reader()
for z in x['inventory']:assert hashlib.sha256(r.read(Path(z['path']))).hexdigest()==z['sha256']
qraw=r.read(P/'REQUEST_DRAFT01.json');assert hashlib.sha256(qraw).hexdigest()=='e7579251741a865a2955917a3a9dc346ed6710ffc08388f1907c727e95d0a721'
proofraw=r.read(H/'SOURCE_INPUT_RUNTIME_PROOF01.json');assert hashlib.sha256(proofraw).hexdigest()=='ac1ed8a157d7ec113ebe1a8e2eb71a917f46572d0cc8b035c1ee850d9b10730c'
first=r.total;r.finish();assert r.total==2*first==8261930
c=B/'heartbeat-root-checkpoint10-2026-10-04';evidence=H/'actual-install-evidence';evidence.mkdir(mode=0o700);rows=[]
for n in ['COALESCED_CANDIDATES_INSTALL04_INTENT01.json','COALESCED_CANDIDATES_INSTALL04_OBSERVED01.json','COALESCED_CANDIDATES_INSTALL04_ACTUAL_TOOL_EXIT01.json']:
 p=c/n;raw=p.read_bytes();assert len(raw)<4194304;v=json.loads(raw);(evidence/n).write_bytes(raw);rows.append({'original_path':str(p),'original_mode':stat.S_IMODE(p.stat().st_mode),'path':'actual-install-evidence/'+n,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'keys':list(v)})
observed=json.loads((evidence/'COALESCED_CANDIDATES_INSTALL04_OBSERVED01.json').read_bytes());terminal=json.loads((evidence/'COALESCED_CANDIDATES_INSTALL04_ACTUAL_TOOL_EXIT01.json').read_bytes())
assert rows[1]['sha256'].startswith('ef49531c') and rows[2]['sha256'].startswith('f4a073f0')
out={'schema_version':1,'decision':'EXACT_CURRENT_DRAFT_PLUS_ACTUAL_SOURCE_PROOF_BYTE_INVENTORY_ONLY','unique_paths':len(r.cache),'first_read_bytes':first,'including_finish_bytes':r.total,'remaining_charged_bytes':m.TOTAL-r.total,'remaining_unique_bytes_if_each_read_twice':(m.TOTAL-r.total)//2,'source_proof_bytes':len(proofraw),'source_proof_sha256':m.sha(proofraw),'actual_draft_bytes':len(qraw),'unavailable_final_fields':['actual final Parent request byte delta versus draft','actual full_recovery proof','actual final Parent release'],'final_public_preclaim_success':False,'numerical_authority':False,'original_inner_root_exit_null_preserved':True,'actual_installer_evidence':rows,'actual_tool_terminal':terminal,'inventory':[{'path':str(p),'bytes':len(raw),'sha256':m.sha(raw)} for p,raw in r.cache.items()]}
with (H/'FINAL_KNOWN_INVENTORY02.json').open('x') as f:f.write(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['inventory','actual_installer_evidence','actual_tool_terminal']}))
