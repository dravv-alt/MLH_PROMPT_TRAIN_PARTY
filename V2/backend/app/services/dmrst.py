"""Local CPU DMRST subprocess. Never fabricate neural discourse output."""
import json
import os
import subprocess
import sys
import threading
import queue
from pathlib import Path

_LOCK=threading.RLock()
_WORKER=None


def parse_dmrst(text):
    global _WORKER
    root=Path(__file__).resolve().parents[2]
    checkpoint=Path(os.getenv('DMRST_MODEL_PATH') or str(root/'models/dmrst/multi_all_checkpoint.torchsave'))
    backbone=Path(os.getenv('DMRST_BACKBONE_PATH') or str(root/'models/dmrst/xlm-roberta-base'))
    if not checkpoint.is_file() or not (backbone/'config.json').is_file():
        return {'status':'unavailable','reason':'dmrst_checkpoint_or_backbone_missing','edus':[],'tree':[]}
    with _LOCK:
        if _WORKER is None or _WORKER.poll() is not None:
            _WORKER=subprocess.Popen([sys.executable,str(root/'scripts/dmrst_worker.py'),str(checkpoint),str(backbone)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding='utf-8')
        try:
            _WORKER.stdin.write(json.dumps({'text':text},ensure_ascii=False)+'\n');_WORKER.stdin.flush()
            responses=queue.Queue()
            threading.Thread(target=lambda:responses.put(_WORKER.stdout.readline()),daemon=True).start()
            try:
                raw=responses.get(timeout=90)
            except queue.Empty:
                _WORKER.kill();_WORKER=None
                return {'status':'unavailable','reason':'dmrst_timeout_90s','edus':[],'tree':[]}
            if not raw:raise RuntimeError('worker exited')
            return json.loads(raw)
        except (OSError,ValueError,RuntimeError):
            return {'status':'unavailable','reason':'dmrst_inference_failed','edus':[],'tree':[]}
