from pathlib import Path
import json,sys,hashlib
D=Path(__file__).resolve().parent;F=D.parent;T=F/'financial-wrapper-complete100-final-supplement-tooling01-2026-10-04';C=F/'financial-wrapper-complete100-final-supplement-capture01-2026-10-04';sys.path.insert(0,str(T/'utilities'));import recovery_pax01 as R
cap=json.loads((C/'CAPTURE01.json').read_bytes());roots=json.loads((C/'SUPPORT_ROOTS01.json').read_bytes());support=Path(cap['scopes']['support']['snapshot']);checks=[]
for label,row in roots.items():
 original=R.scan(Path(row['original']));copied=R.scan(support/label);assert original==copied and original['root_mode']==row['original_root_mode'];checks.append('whole original support current membership '+label)
contract=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-final-contract-20261004-01');assert R.scan(contract)==R.scan(Path(cap['scopes']['contract']['snapshot']));checks.append('whole actual current finalcontract snapshot equality')
P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-root-launch-20261004-01');old=F/'financial-wrapper-complete100-baseline-capture01-2026-10-04';assert R.scan(P)==json.loads((old/'PARENT_MANIFEST01.json').read_bytes());checks.append('original nine Parent unchanged')
(D/'CURRENT02.json').write_text(json.dumps({'checks':len(checks),'checks_detail':checks},indent=2)+'\n');print(len(checks))
