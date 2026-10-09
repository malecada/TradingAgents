from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;F=H.parent;R=Path.cwd();A=F/'mcm-batched-numeric-execution01-2026-10-09';C=F/'mcm-batched-numeric-execution02-2026-10-09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=(C/'numeric_execution.py').read_text()
for indent,label in [('    ','read'),('        ','summary')]:
 old=indent+"finally:\n"+indent+"    primary=__import__('sys').exception()\n"+indent+"    try:os.close(child)\n"+indent+"    except BaseException as cleanup:\n"+indent+"        if primary is None:raise\n"+indent+"        primary.add_note('numeric "+label+" cleanup: '+repr(cleanup))"
 assert old in s;s=s.replace(old,indent+'finally:os.close(child)',1)
assert s==(A/'numeric_execution.py').read_text()
paths=[A/'numeric_execution.py',C/'numeric_execution.py',C/'MANIFEST01.json',C/'RESULT01.json',F/'mcm-batched-numeric-execution-review01-2026-10-09/WITHHELD01.json',H/'REPORT.md']+list(H.glob('*RESULT01.json'))+list(H.glob('*TEST01.log'))+[H/'verify.py',H/'enclosing_exception.py',H/'summary_enclosing.py']
out={'decision':'withheld','literal_two_finally_inverse':True,'original_findings_fixed':True,'new_finding':'Ambient sys.exception suppresses cleanup-only errors under an enclosing handled exception, including summary batch credit.','required_fix':'Track the local primary with explicit except in read, summary and verifier scopes.','source_sha256':sha(C/'numeric_execution.py'),'numeric_or_authority_execution':False,'evidence':{str(p.relative_to(R)):sha(p) for p in paths}}
(H/'WITHHELD01.json').write_text(json.dumps(out,indent=2)+'\n');print(sha(H/'WITHHELD01.json'))
