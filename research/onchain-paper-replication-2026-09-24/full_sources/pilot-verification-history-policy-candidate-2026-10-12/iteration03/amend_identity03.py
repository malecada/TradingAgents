from pathlib import Path
import shutil
P=Path(__file__).resolve().parent;I=P/'iteration02';I.mkdir()
for p in list(P.iterdir()):
 if p.is_file() and p.name!='amend_identity03.py':shutil.copy2(p,I/p.name)
p=P/'admission.py';s=p.read_text();old='return _history_bytes((str(root), experiment, source, design_source, registration,';new='return _history_bytes((id(run), str(root), experiment, source, design_source, registration,';assert s.count(old)==1;p.write_text(s.replace(old,new))
