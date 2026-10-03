"""Run only the explicit finite source/stdlib target, never research mains."""
import pathlib,subprocess,sys
D=pathlib.Path(__file__).resolve().parent
names=('test_inventory03.py','test_reader03.py','test_predecessor_bounds03.py','test_integration03.py','test_tail_genuine03.py','test_marker_reader04.py','test_adapter01.py','test_worker01.py')
for name in names:
 result=subprocess.run([sys.executable,'-B',str(D/name)],capture_output=True,text=True);print(name,'exit',result.returncode);print(result.stdout,end='');print(result.stderr,end='');assert result.returncode==0,name
print('27 source/stdlib checks pass; no actual refusal cases or numeric execution.')
