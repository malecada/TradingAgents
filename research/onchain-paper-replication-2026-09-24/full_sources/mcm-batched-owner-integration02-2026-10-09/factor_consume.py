from pathlib import Path
p=Path(__file__).resolve().parent/'registered_offload.py';s=p.read_text();a=s.index('        if consume is not None:');b=s.index("        semantic.dispose_recovery",a)
old=s[a:b]
body=old[old.index('            # Actual'):]
body=''.join(line[8:] if line.strip() else line for line in body.splitlines(True))
body=body.replace("work/'semantic/tree'","directory/'tree'")
func="def _consume_recovered(journal,evidence,batch,directory,consume):\n"+body+'\n'
s=s[:a]+"        if consume is not None:_consume_recovered(journal,evidence,batch,work/'semantic',consume)\n"+s[b:]
a=s.index('def fresh_recover');s=s[:a]+func+s[a:];p.write_text(s)
