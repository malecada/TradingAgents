"""Publish-event timing only; no numerical imports, admission or execution."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
F = HERE.parent

BASELINES = {
    'compact_matcher.py': ROOT/'tradingagents/research/onchain_replication/compact_matcher.py',
    'stage_retention.py': F/'real-data-pilot-retention-timing01-2026-10-08/stage_retention.py',
    'real_pilot_partial_progress.py': F/'real-data-pilot-retention-timing01-2026-10-08/real_pilot_partial_progress.py',
}
EDITS = {
    'compact_matcher.py': [
        ('            self.log.progress(result)\n',
         "            self._timed('event_publication',self.log.progress,result)\n"),
        ('            self.log.begin(cache_key(purpose), pair.digest(identity))\n',
         "            self._timed('event_publication',self.log.begin,cache_key(purpose),pair.digest(identity))\n"),
        ('                    answer = self.log.complete(float(result.score), result.convergence, result.iterations)\n',
         "                    answer = self._timed('event_publication',self.log.complete,float(result.score),result.convergence,result.iterations)\n"),
    ],
    'stage_retention.py': [
        ('            self.matcher.log.progress(artifact);self.current_frame=expected;self._refresh();self.live()\n',
         "            self.matcher._timed('event_publication',self.matcher.log.progress,artifact);self.current_frame=expected;self._refresh();self.live()\n"),
    ],
    'real_pilot_partial_progress.py': [
        ("'score_only', 'retention_live')\n", "'score_only', 'retention_live', 'event_publication')\n"),
    ],
}


def pin(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    rows = {}
    for name, baseline in BASELINES.items():
        original = baseline.read_text()
        source = original
        for old, new in EDITS[name]:
            if source.count(old) != 1:
                raise ValueError('original publication seam differs: '+name)
            source = source.replace(old, new, 1)
        inverse = source
        for old, new in reversed(EDITS[name]):
            if inverse.count(new) != 1:
                raise ValueError('inverse publication seam differs: '+name)
            inverse = inverse.replace(new, old, 1)
        if inverse != original:
            raise ValueError('unrelated source changed: '+name)
        ast.parse(source)
        target = HERE/name
        target.write_text(source)
        (HERE/('baseline_'+name)).write_text(original)
        (HERE/(name+'.diff')).write_text(''.join(difflib.unified_diff(
            original.splitlines(True),source.splitlines(True),fromfile='accepted/'+name,tofile='timed/'+name)))
        rows[name] = {'baseline': pin(baseline), 'candidate': pin(target),
                      'literal_inverse_exact': True, 'edit_count': len(EDITS[name])}
    result = {'status': 'SOURCE_ONLY_NOT_INSTALLED_NOT_ENTRY_RELEASED', 'files': rows,
              'scope': 'One inclusive public-event timer for begin, both progress routes and complete, using the unchanged existing CompactMatcher._timed/ScoringDiagnostic.measure. Captures validation, append/readback and conditional archive sealing; separately called durability barriers and argument construction remain outside. Original arguments, ordering, output, counters, policies and 1024 stop are unchanged.',
              'limitations': ['No live or numerical performance measurement.',
                              'Timings overlap lease/retention measurements and cannot be added or interpreted as pure disk IO.',
                              'Independent changed-seam review and finite checkpoint capacity check pending.']}
    (HERE/'CANDIDATE01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':result['status'],'files':rows},sort_keys=True))


if __name__ == '__main__':
    main()
