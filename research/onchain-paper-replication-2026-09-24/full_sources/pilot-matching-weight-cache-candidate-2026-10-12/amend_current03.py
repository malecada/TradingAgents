from pathlib import Path
import shutil
P=Path(__file__).resolve().parent;I=P/'iteration02';I.mkdir()
for name in ('matching_numeric_policy.py','SOURCE_MANIFEST02.json'):shutil.copy2(P/name,I/name)
p=P/'matching_numeric_policy.py';s=p.read_text();old='''    def current(self):
        if dict(self.policy).get("format")==CACHE_POLICY["format"]:_cache_current(self)
        if self.policy is not self._pin or kernel.np is not self._numpy:
            raise ValueError('numeric adapter changed')
''';new='''    def current(self):
        if self.policy is not self._pin or kernel.np is not self._numpy:
            raise ValueError('numeric adapter changed')
        if dict(self.policy).get("format")==CACHE_POLICY["format"]:_cache_current(self)
''';assert s.count(old)==1;p.write_text(s.replace(old,new))
