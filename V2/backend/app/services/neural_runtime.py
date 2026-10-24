"""Deadline-aware independent workers; no model imports on HTTP request threads."""
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from collections import deque
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[2]
RESOURCES=ROOT/'models/neural'


def manifest():
    try:return json.loads((RESOURCES/'manifest.json').read_text(encoding='utf-8'))
    except (OSError,ValueError):return {}


def version(kind):
    return manifest().get('versions',{}).get(kind, 'unprepared.'+kind+'.v1')


class ModelWorker:
    def __init__(self,kind):
        self.kind=kind;self.lock=threading.RLock();self.proc=None;self.epoch=0
        self.state='unavailable';self.pending={};self.restarts=deque();self.progress=time.monotonic()
        self.warming_since=0
        self.inflight=set()
        self.loaded_version=None
        self.effective_threads=None;self.thread_fallback=False

    def start(self):
        with self.lock:
            current_version=version(self.kind)
            if self.proc and self.proc.poll() is None:
                if self.loaded_version==current_version:return
                self.proc.terminate()
                for p in self.pending.values():p['result']={'status':'unavailable','reason':'resource_version_changed'};p['event'].set()
            if not manifest():self.state='unavailable';return
            now=time.monotonic()
            while self.restarts and now-self.restarts[0]>3600:self.restarts.popleft()
            if len(self.restarts)>=3:self.state='restart_limit';return
            self.restarts.append(now);self.epoch+=1;epoch=self.epoch
            self.loaded_version=current_version
            self.state='warming';self.progress=now;self.warming_since=now;self.inflight.clear()
            self.proc=subprocess.Popen([sys.executable,str(ROOT/'scripts/neural_worker.py'),self.kind,str(RESOURCES)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding='utf-8')
            threading.Thread(target=self._read,args=(self.proc,epoch),daemon=True).start()
            threading.Thread(target=self._watch,args=(self.proc,epoch),daemon=True).start()

    def _read(self,proc,epoch):
        try:
            for line in proc.stdout:
                msg=json.loads(line)
                with self.lock:
                    if epoch!=self.epoch:return
                    self.progress=time.monotonic()
                    if msg.get('status')=='ready':
                        self.state='ready';self.effective_threads=msg.get('threads');self.thread_fallback=msg.get('thread_fallback',False)
                    if msg.get('epoch')==epoch and 'result' in msg:
                        self.inflight.discard(msg['id'])
                        pending=self.pending.get(msg['id'])
                        if pending:pending['result']=msg['result'];pending['event'].set()
        finally:
            with self.lock:
                if epoch==self.epoch:
                    self.state='unavailable'
                    for p in self.pending.values():p['result']={'status':'unavailable','reason':'worker_exited'};p['event'].set()

    def _watch(self,proc,epoch):
        while proc.poll() is None:
            time.sleep(1)
            with self.lock:
                if epoch!=self.epoch:return
                if (self.inflight or self.state=='warming') and time.monotonic()-self.progress>60:
                    proc.kill();return

    def request(self,payload,budget):
        self.start()
        with self.lock:
            if self.state!='ready':return {'status':'unavailable','reason':self.state}
            if sum(not p.get('background') for p in self.pending.values())>=8 and not payload.get('background'):return {'status':'unavailable','reason':'queue_full'}
            rid=str(uuid4());epoch=self.epoch;event=threading.Event();entry={'event':event,'user':payload.get('user'),'background':payload.get('background',False)}
            self.pending[rid]=entry
            self.inflight.add(rid)
            message={**payload,'id':rid,'epoch':epoch,'deadline':time.time()+budget,'version':version(self.kind)}
            try:self.proc.stdin.write(json.dumps(message)+'\n');self.proc.stdin.flush()
            except OSError:self.pending.pop(rid,None);self.inflight.discard(rid);return {'status':'unavailable','reason':'worker_exited'}
        event.wait(budget)
        with self.lock:
            self.pending.pop(rid,None)
            if 'result' in entry:return entry['result']
            if epoch==self.epoch and self.proc.poll() is None:
                try:self.proc.stdin.write(json.dumps({'cancel':True,'id':rid})+'\n');self.proc.stdin.flush()
                except OSError:pass
            return {'status':'unavailable','reason':'deadline'}

    def clear(self,user):
        with self.lock:
            if self.proc and self.proc.poll() is None:
                try:
                    self.proc.stdin.write(json.dumps({'clear_user':user})+'\n')
                    for rid,p in self.pending.items():
                        if p.get('user')==user:
                            self.proc.stdin.write(json.dumps({'cancel':True,'id':rid})+'\n');p['result']={'status':'cancelled','reason':'memory_reset'};p['event'].set()
                    self.proc.stdin.flush()
                except OSError:pass

    def stop(self):
        with self.lock:
            if self.proc and self.proc.poll() is None:self.proc.terminate()
            self.proc=None;self.epoch+=1;self.state='unavailable';self.inflight.clear()
            for p in self.pending.values():p['result']={'status':'unavailable','reason':'worker_shutdown'};p['event'].set()
            # Operator/application shutdown is not an automatic crash restart.
            # A later explicit start receives a fresh three-restart watchdog budget.
            self.restarts.clear()


EMBEDDING=ModelWorker('embedding')
NLI=ModelWorker('nli')
