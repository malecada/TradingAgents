from pathlib import Path
import ast,hashlib,json,shutil
D=Path(__file__).resolve().parent;F=D.parent;ROOT=F.parents[2];O=F/'financial-wrapper-complete100-final-supplement-tooling01-2026-10-04';B=F/'financial-wrapper-complete100-failed-outcome-capture02-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();req=json.loads((B/'REQUIRED_BODIES01.json').read_bytes());cap=json.loads((B/'CAPTURE01.json').read_bytes());assert sha((B/'CAPTURE01.json').read_bytes())=='e9e78f1cc4f33d51ddca968bc80170e83e1a12b6ff2bff9cf301ab25e280fce8';assert len(req)==35 and sum(r['bytes'] for r in req.values())==16481302
(D/'utilities').mkdir()
for n in ('recovery_pax01.py','owned_io.py','bounded_git01.py'):shutil.copyfile(O/'utilities'/n,D/'utilities'/n)
records={}
def change(s,old,new,edits):
 assert s.count(old)==1,(old[:60],s.count(old));edits.append({'old':old,'new':new});return s.replace(old,new)
for name,origin in [('recover01.py','recover01.py'),('restore01.py','restore02.py')]:
 raw=(O/origin).read_bytes();(D/('ORIGINAL_'+name)).write_bytes(raw);s=raw.decode();ed=[]
 oldreq=next(x for x in s.splitlines() if x.startswith('REQUIRED'));s=change(s,oldreq,'REQUIRED = '+repr(req),ed)
 if name=='recover01.py':
  s=change(s,'fresh-complete100-final-supplement01.git','fresh-complete100-failed-outcome02-01.git',ed);s=change(s,'fresh-actual-remote-complete100-final-supplement-recovered','fresh-actual-remote-complete100-failed-outcome02-recovered',ed)
  old="Exact final contract/support byte supplement recovered from external Git. Complete baseline Source339 and all385 original Git objects remain separately preserved and recovered. This byte receipt grants no native launch, financial, runtime, POSIX or whole-capacity authority; actual complete flat recovery and independent final release joins remain required."
  s=change(s,old,'Exact corrected failed-outcome02 and retained withheld-capture01 bytes recovered. Historical native attempt remains FAILED/spent; remote retrieval starts no claim. Baseline385 Git remains separate. Selected bodies are bounded4MiB; writable Git pack extents are not universally bounded4MiB and require separate actual readback. No numerical/runtime/POSIX/capacity authority.',ed)
 else:
  s=change(s,"REL = 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-final-supplement-capture01-2026-10-04'","REL = "+repr(str(B.relative_to(ROOT)))+"\nOLD_REL = "+repr(str(B.relative_to(ROOT)).replace('capture02-','capture01-')),ed)
  s=change(s,"CAPTURE = '86b787a7a01f15a596f356c16b1c1b55060549159fb7a301cc173c814cfcb67e'","CAPTURE = 'e9e78f1cc4f33d51ddca968bc80170e83e1a12b6ff2bff9cf301ab25e280fce8'",ed)
  s=change(s,"CAPTURE_STATUS = 'FINAL_CONTRACT_SUPPORT_FROZEN_NO_CLAIM'","CAPTURE_STATUS = 'FAILED_COMPLETE100_OUTCOME_FROZEN'",ed)
  s=change(s,"LABELS = ('contract', 'support')","LABELS = "+repr(tuple(cap['scopes'])),ed)
  s=change(s,"REMOTE_STATUS = 'fresh-actual-remote-complete100-final-supplement-recovered'","REMOTE_STATUS = 'fresh-actual-remote-complete100-failed-outcome02-recovered'",ed)
  s=change(s,"name.startswith(REL + '/')","any(name.startswith(prefix + '/') for prefix in (REL, OLD_REL))",ed)
  s=change(s,"capture['native_or_claim_started'] is False","capture['historical_native_started'] is True and capture['new_native_or_claim_started_by_capture'] is False and capture['permanent_disposition'] == 'FAILED_SPENT' and capture['prior_failed_capture_permanently_withheld'] is True",ed)
  s=change(s,'    return scopes\n\n\ndef restore_scopes','    validate_union(bundle, capture, scopes)\n    return scopes\n\n\ndef restore_scopes',ed)
  extension=(D/'union_body01.txt').read_text();s=change(s,'\ndef restore_scopes(',extension+'\ndef restore_scopes(',ed)
  s=change(s,'len(floors) < 32','len(floors) < 64',ed)
  s=change(s,"'COMPLETE_FINAL_SUPPLEMENT_CONTRACT_SUPPORT_BYTES_RECOVERED'","'COMPLETE_FAILED_OUTCOME02_BYTES_RECOVERED'",ed)
  s=change(s,"'Actual final contract/support bytes and mode metadata only; genuine baseline Source339/all385 Git recovery stays separate. Independent exact recovery/release review remains required; no native or scientific authority is minted.'","'Actual corrected failed CAP588/475 and Parent/support bytes recovered; historical capture01 remains withheld forensic evidence and failed native identity remains spent. No checkpoint decode, scientific completion, new claim or restart; baseline385 Git recovery separate.'",ed)
 (D/name).write_text(s);inverse=s
 for e in reversed(ed):assert inverse.count(e['new'])==1;inverse=inverse.replace(e['new'],e['old'])
 assert inverse.encode()==raw and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(raw));records[name]={'original_sha256':sha(raw),'candidate_sha256':sha(s.encode()),'edits':ed,'complete_literal_and_AST_inverse':True}
(D/'SOURCE_INVERSE01.json').write_text(json.dumps(records,indent=2)+'\n');(D/'REQUIRED_BODIES01.json').write_bytes((B/'REQUIRED_BODIES01.json').read_bytes());(D/'ACTUAL_CAPTURE01.json').write_bytes((B/'CAPTURE01.json').read_bytes());print({k:len(v['edits']) for k,v in records.items()})
