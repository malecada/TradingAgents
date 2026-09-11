"""Invented disposable journal attacks; no network, claims or real run stores."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

root=Path(__file__).resolve().parents[3]
source=root/'tradingagents/research_options_capture/journal.py'
spec=importlib.util.spec_from_file_location('reviewed_journal',source)
j=importlib.util.module_from_spec(spec);spec.loader.exec_module(j)
results={}
def make(base):
    claim=base/'claim.json';claim.write_bytes(b'invented claim')
    return j.Journal(base/'journal',claim_path=claim,claim_sha256=hashlib.sha256(claim.read_bytes()).hexdigest(),slots=[{'id':'a','scheduled_ms':10,'deadline_ms':15,'request':{'symbol':'invented'},'body_cap':128}],total_cap=50000,terminal_reserve=2048,check_source=lambda:None)

with tempfile.TemporaryDirectory() as td:
 base=Path(td)
 for name in ('partial_prefix','intent_clock','seal_status','foreign_recovery','member_reserve'):
  directory=base/name;directory.mkdir()
  with make(directory) as journal:
   accepted=False;reason=None
   try:
    if name=='partial_prefix':
        journal.begin('a',now_ms=10);journal.partial('a',b'abc');journal.record('a',b'xyz',metadata={});journal.validate();accepted=True
    elif name=='intent_clock':
        journal.begin('a',now_ms=10)
        p=journal.path/'intent-a.json';v=json.loads(p.read_bytes());v['now_ms']=999;p.write_bytes(j.encode(v));journal.validate();accepted=True
    elif name=='seal_status':
        journal.seal('failed');p=journal.path/'seal.json';v=json.loads(p.read_bytes());v['status']='complete';p.write_bytes(j.encode(v));journal.validate();accepted=True
    elif name=='foreign_recovery':
        (journal.path/'recovery-000000.json').write_bytes(b'{}');journal.validate();accepted=True
    else:
        journal.begin('a',now_ms=10)
        original=Path.unlink
        def crash(path,*args,**kwargs):
            if path.name.startswith('pending-'):raise OSError('invented crash after atomic link')
            return original(path,*args,**kwargs)
        for part in range(64):
            try:
                with patch.object(Path,'unlink',crash):journal.partial('a',b'x')
            except OSError:continue
            except j.JournalError:break
        try:journal.seal('failed');accepted=False
        except j.JournalError as exc:accepted=True;reason=str(exc)
   except Exception as exc:reason=type(exc).__name__+': '+str(exc)
   results[name]={'unsafe_or_invalid_state_accepted':accepted,'reason':reason}
report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'cases':results,'scope':'Disposable invented file-state attacks only; no actual research journal.'}
destination=Path(__file__).with_name('options-journal-adversarial-review.json')
with destination.open('x') as out:json.dump(report,out,indent=2);out.write('\n')
print(json.dumps(report))
