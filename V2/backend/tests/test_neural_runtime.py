import io
import json
import threading
import time
from app.services.neural_runtime import ModelWorker


class Process:
    def __init__(self):self.stdin=io.StringIO();self.stdout=[]
    def poll(self):return None


def test_deadline_does_not_kill_worker_and_queue_cap(monkeypatch):
    worker=ModelWorker('embedding');worker.proc=Process();worker.state='ready';worker.epoch=3
    monkeypatch.setattr(worker,'start',lambda:None)
    start=time.monotonic();result=worker.request({'text':'example'},.01)
    assert result['reason']=='deadline';assert time.monotonic()-start<.2
    messages=[json.loads(line) for line in worker.proc.stdin.getvalue().splitlines()]
    assert messages[0]['epoch']==3;assert messages[1]['cancel'];assert worker.inflight
    worker.pending={str(i):{} for i in range(8)}
    assert worker.request({},.01)['reason']=='queue_full'


def test_late_epoch_cannot_complete_new_request():
    worker=ModelWorker('embedding');worker.epoch=2
    event=threading.Event();worker.pending={'same':{'event':event}}
    old=Process();old.stdout=[json.dumps({'id':'same','epoch':1,'result':{'status':'ready'}})]
    worker._read(old,1)
    assert not event.is_set();assert 'result' not in worker.pending['same']
