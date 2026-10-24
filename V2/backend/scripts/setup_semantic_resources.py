"""Explicit setup only: freeze model revisions, checksums, and null calibration."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
from huggingface_hub import snapshot_download

root=Path(__file__).resolve().parents[1]/'models/neural'
root.mkdir(parents=True,exist_ok=True)
dest=root/'manifest.json'
old=json.loads(dest.read_text()) if dest.exists() else {}
models={'embedding':'sentence-transformers/all-MiniLM-L6-v2','nli':'cross-encoder/nli-deberta-v3-small'}
PINNED={'embedding':'1110a243fdf4706b3f48f1d95db1a4f5529b4d41','nli':'fa2804872c3b4bd748f38c0185cc85775361e735'}
revisions={}
for kind,repo in models.items():
    revision=PINNED[kind]
    revisions[kind]=revision
    snapshot_download(repo,revision=revision,local_dir=str(root/kind),allow_patterns=['*.json','*.txt','*.model','model.safetensors','tokenizer.*','special_tokens_map.json'],ignore_patterns=['onnx/*','openvino/*'])
subprocess.run([sys.executable,str(Path(__file__).with_name('neural_worker.py')),'nli',str(root),'--calibrate'],check=True)
hashes={}
for file in root.rglob('*'):
    if not file.is_file() or '.cache' in file.parts or file==dest:continue
    h=hashlib.sha256()
    with file.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    hashes[file.relative_to(root).as_posix()]=h.hexdigest()
versions={kind:f'{kind}.{revision[:12]}.surrogate1.eagercpu1.repeatcheck1.'+('win128x32' if kind=='embedding' else 'topics-functions1.null1.'+hashes['null_scores.json'][:10]) for kind,revision in revisions.items()}
dest.write_text(json.dumps({'models':models,'revisions':revisions,'versions':versions,'sha256':hashes},indent=2,sort_keys=True),encoding='utf-8')
print('Prepared local neural models and versioned null-score artifact:',dest)
