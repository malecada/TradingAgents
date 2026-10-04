import gzip,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;p=H/'READBACK01.json';raw=p.read_bytes();data=json.loads(raw);compressed=gzip.compress(raw,mtime=0);assert gzip.decompress(compressed)==raw
with (H/'RAW_DETAILED_READBACK01.json.gz').open('xb') as f:f.write(compressed)
summary={k:v for k,v in data.items() if k!='check_names'};summary['detailed_check_evidence']={'path':'RAW_DETAILED_READBACK01.json.gz','compression':'gzip','compressed_bytes':len(compressed),'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'uncompressed_bytes':len(raw),'uncompressed_sha256':hashlib.sha256(raw).hexdigest(),'exact_original_unsealed_READBACK01_bytes_preserved':True};p.write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n');print(len(raw),len(compressed))
