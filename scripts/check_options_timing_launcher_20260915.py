"""Invented shell clocks; actual launcher control flow, no worker/network execution."""
from pathlib import Path
import hashlib,json,shlex,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'research/strategy-search-2026-09-11'
source=base/'launch-options-timing-20260915-v2.sh';raw=source.read_text();L=1789469880;B=1789469940
cases=[('exact-lease',[L-10,L,L],0,True),('after-sleep-backward',[L-10,L-1],42,False),('after-sleep-too-late',[L-10,B],42,False),('during-hash-backward',[L-10,L+1,L-1],43,False),('during-hash-too-late',[L-10,L+1,B],43,False),('last-allowed-second',[L-10,B-1,B-1],0,True),('prewait-over-two-hours',[L-7201],41,False)]
rows=[];root=Path(tempfile.mkdtemp(prefix='options-timing-launcher-clocks-'))
for name,clocks,expected,executed in cases:
    d=root/name;d.mkdir();clockfile=d/'clocks';clockfile.write_text(''.join(str(n)+'\n' for n in clocks))
    mock='date() {\n  if [ "$*" = "-u +%s" ]; then\n    head -n 1 CLOCKFILE\n    tail -n +2 CLOCKFILE > CLOCKFILE.next\n    mv CLOCKFILE.next CLOCKFILE\n  fi\n}\nsleep() { :; }\nflock() { :; }\nsha256sum() { cat >/dev/null; }\n'.replace('CLOCKFILE',shlex.quote(str(clockfile)))
    script=raw.replace('umask 077\n','umask 077\n'+mock).replace('cd /opt/thesis-research/options-timing-20260915','cd '+shlex.quote(str(d)))
    lines=script.splitlines();last=lines[-1];assert last.startswith('exec /opt/thesis-research/options-episode-20260911/runtime/')
    lines[-1]="printf 'EXECUTED\\n' > "+shlex.quote(str(d/'executed'))
    script=d/'case.sh';script.write_text('\n'.join(lines)+'\n')
    result=subprocess.run(['bash',str(script)],capture_output=True,text=True,timeout=5)
    row={'name':name,'clocks':clocks,'returncode':result.returncode,'executed_marker':(d/'executed').exists(),'pass':result.returncode==expected and (d/'executed').exists()==executed};rows.append(row)
    assert row['pass'],row
report={'scope':'Clock-boundary control-flow tests with mocked date/sleep/hash/flock and replaced final exec marker; no actual worker, market or SSH operations','source':str(source.relative_to(ROOT)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'fixture_root':str(root),'cases':rows,'pass':all(r['pass'] for r in rows)}
with (base/'reviews/options-timing-launcher-clock-tests-20260915.json').open('x') as f:f.write(json.dumps(report,indent=2)+'\n')
print(json.dumps({'pass':report['pass'],'case_count':len(rows),'source_sha256':report['source_sha256']}))
