"""Offline controls only: no transfer/guard/authority construction."""
import hashlib,importlib.util,json,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('candidate',HERE/'caller01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Changed(unittest.TestCase):
    def test_actual_claim_shape_refuses_and_preserves_fatal(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            root=Path(tmp);d=root/'research_runs/active';d.mkdir(parents=True)
            (d/'claim.json').write_text(json.dumps({'experiment':{'inputs':{'graph':{'path':'graphs/week/manifest.json','sha256':'a'*64}}}}))
            rows=[{'path':'graphs/week/edge_index.npy'}];events=[]
            with patch.object(m,'selected_rows',return_value=rows),patch.object(m.subprocess,'check_output',return_value=b''):
                with self.assertRaisesRegex(ValueError,'active consumer references selected graph'):
                    m.move_rows(rows,before=lambda row:m.verify_metadata(root,{'metadata_pins':{},'closures':[]},[]),move=lambda *a:self.fail('transfer reached'),publish=lambda name,value:events.append((name,value)))
            self.assertEqual([x[0] for x in events],['00-attempted.json','00-failed.json'])
            self.assertEqual(events[-1][1]['error_type'],'ValueError')
    def test_real_git_anchor_and_preflight_mutations(self):
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        anchor=subprocess.check_output(['git','rev-parse','HEAD^'],cwd=ROOT,text=True).strip()
        body=subprocess.check_output(['git','cat-file','blob',anchor+':AGENTS.md'],cwd=ROOT)
        self.assertEqual(body,(ROOT/'AGENTS.md').read_bytes())
        c={'source_commit':anchor,'source_files':{'AGENTS.md':hashlib.sha256(body).hexdigest()}}
        expected={'identity':m.ID,'manifest_sha256':'a'*64,'head':head,'source_anchor':anchor}
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            here=Path(tmp);p=here/'preflight01.json'
            p.write_text(json.dumps(expected));m.verify_source(ROOT,here,c,'a'*64)
            for key in expected:
                bad=dict(expected);bad[key]='wrong';p.write_text(json.dumps(bad))
                with self.subTest(field=key),self.assertRaisesRegex(ValueError,'preflight/source'):m.verify_source(ROOT,here,c,'a'*64)
            p.unlink()
            with self.assertRaises(FileNotFoundError):m.verify_source(ROOT,here,c,'a'*64)
            p.write_text(json.dumps(expected))
            bad={'source_commit':anchor,'source_files':{'AGENTS.md':'0'*64}}
            with self.assertRaisesRegex(ValueError,'metadata binding'):m.verify_source(ROOT,here,bad,'a'*64)
            # Keep actual Git/object read, isolate the second (anchor-body) comparison.
            with patch.object(m,'checked',return_value=body),self.assertRaisesRegex(ValueError,'source anchor body'):m.verify_source(ROOT,here,bad,'a'*64)
            bad={'source_commit':'0'*40,'source_files':c['source_files']}
            p.write_text(json.dumps(dict(expected,source_anchor='0'*40)))
            with self.assertRaisesRegex(ValueError,'not an ancestor'):m.verify_source(ROOT,here,bad,'a'*64)
    def test_literal_inverse_and_transport_ceiling(self):
        previous=(HERE.parent/'real-data-pilot-closed-array-offload-caller01-2026-10-05/caller01.py').read_text()
        current=(HERE/'caller01.py').read_text()
        helper=current[current.index('def verify_source('):current.index('def worker(')]
        inverse=current.replace(helper,'').replace("claim['experiment']['inputs'].values()","claim.get('inputs',{}).values()")
        inverse=inverse.replace('    verify_source(root,here,c,config_sha)',"    for path,h in c['source_files'].items():checked(root,{'path':path,'sha256':h})\n    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==c['source_commit'],'source changed after release')")
        inverse=inverse.replace('maximum_payload_bytes=MAX_BODY','maximum_payload_bytes=8*GIB')
        self.assertEqual(inverse,previous)
        self.assertEqual(current.count('maximum_payload_bytes=MAX_BODY'),1)
if __name__=='__main__':unittest.main()
