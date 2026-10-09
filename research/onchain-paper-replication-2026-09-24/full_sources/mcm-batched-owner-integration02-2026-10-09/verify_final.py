from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'verify.py').read_text().replace("'tiny-stage'","'tiny-stage02'").replace("'tiny-output'","'tiny-output02'").replace("'RESULT01.json'","'RESULT02.json'")
exec(compile(s,str(H/'verify.py'),'exec'))
