from pathlib import Path
import runpy,copy,json
C=Path('research/onchain-paper-replication-2026-09-24/full_sources/pilot-verification-history-policy-candidate-2026-10-12');ns=runpy.run_path(str(C/'check01.py'));f=ns['Fixture'](2)
try:
 f.admit();original=f.run;clone=ns['ResearchRun']();clone.__dict__.update(original.__dict__);f.env['_HISTORY'][clone]=f.env['_HISTORY'][original];f.run=clone;f.events.clear()
 try:f.admit()
 except ValueError as e:r={'status':'PASS','transplant_refused':str(e)}
 else:r={'status':'RED','same_claim_different_run_snapshot_accepted':True,'fresh_claim_verifications':sum(k=='verify' for k,v in f.events)}
 print(json.dumps(r,indent=2));assert r['status']=='PASS'
finally:f.close()
