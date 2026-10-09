from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;F=H.parent;R=Path.cwd();A=F/'mcm-batched-numeric-execution02-2026-10-09';C=F/'mcm-batched-numeric-execution03-2026-10-09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=(C/'numeric_execution.py').read_text()
s=s.replace("    child=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)\n    primary=None\n", "    child=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)\n",1)
s=s.replace("    except BaseException as error:\n        primary=error;raise\n    finally:\n        try:os.close(child)","    finally:\n        primary=__import__('sys').exception()\n        try:os.close(child)",1)
s=s.replace("        primary=None\n        try:write_all(child,body);os.fsync(child)\n        except BaseException as error:\n            primary=error;raise\n        finally:","        try:write_all(child,body);os.fsync(child)\n        finally:\n            primary=__import__('sys').exception()",1)
s=s.replace("root=Path(stream_root).absolute();fd=bd=origin=None;primary=None","root=Path(stream_root).absolute();fd=bd=origin=None",1)
s=s.replace("    except BaseException as error:\n        primary=error;raise\n    finally:\n        cleanup_error=None", "    finally:\n        primary=__import__('sys').exception();cleanup_error=None",1)
assert s==(A/'numeric_execution.py').read_text()
assert sha(C/'numeric_execution.py')=='e3a6450c816a73c8ba60c270d88564a9728437f501d5df594f5f9c1018a1ec34'
paths=[A/'numeric_execution.py',C/'numeric_execution.py',C/'MANIFEST01.json',C/'AMBIENT_RESULT01.json',C/'PRIOR_RESULT01.json',F/'mcm-batched-numeric-execution-review01-2026-10-09/WITHHELD01.json',F/'mcm-batched-numeric-execution-review02-2026-10-09/WITHHELD01.json',F/'matching-exact-numeric-reuse-review03-2026-10-09/SOURCE_REVIEW01.json',F/'mcm-immutable-pair-executor-review02-2026-10-09/SOURCE_REVIEW01.json',H/'REPORT.md',H/'AMBIENT_RESULT01.json',H/'RESULT01.json',H/'AMBIENT_TEST01.log',H/'PRIMARY_TEST01.log',H/'verify_ambient.py',H/'verify_primary.py']
out={'decision':'accepted','scope':'source-only numeric execution03 local-primary correction with prior unchanged-seam review inherited','source_sha256':sha(C/'numeric_execution.py'),'manifest_sha256':sha(C/'MANIFEST01.json'),'literal_inverse_to02':True,'three_ambient_cleanup_refusals':True,'original_primary_preserved':True,'summary_cleanup_failure_credit':0,'numerical_matrix_repeated':False,'key_equivalence_independently_recomputed':False,'whole_capacity_or_empirical_authority':False,'genuine_transport_executed':False,'evidence':{str(p.relative_to(R)):sha(p) for p in paths}}
(H/'SOURCE_REVIEW01.json').write_text(json.dumps(out,indent=2)+'\n');print(sha(H/'SOURCE_REVIEW01.json'))
