from pathlib import Path
import shutil
P=Path(__file__).resolve().parent;I=P/'iteration01';I.mkdir()
for p in list(P.iterdir()):
 if p.is_file() and p.name!='amend_fifo02.py':shutil.copy2(p,I/p.name)
p=P/'admission.py';s=p.read_text();old='fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)';new='fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)';assert s.count(old)==1;p.write_text(s.replace(old,new))
p=P/'benchmark01.py';s=p.read_text();s=s.replace("'capability_created':False}","'capability_created':False,'measurement_scope':'historical frontier and history audit component only','excludes':['current admission HEAD/source/design/runtime/input-binding/budget checks','warm own-claim verification','production warm _check_source latency']}");p.write_text(s)
