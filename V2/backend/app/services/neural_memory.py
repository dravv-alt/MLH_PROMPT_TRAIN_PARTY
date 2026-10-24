"""Owner-scoped hybrid retrieval, durable jobs, and generation-CAS indexing."""
from collections import OrderedDict
import copy
import threading
import time
from uuid import uuid4
import numpy as np
from fastapi import HTTPException
from sqlalchemy import select, delete, text
from app.models.orm import NeuralMemoryState, LocalProcessingPreference, LocalMemoryPreference, LocalRawTurn, SceneEmbedding, NeuralJob, PWMState, ChatTurn, NLPRecord
from app.services.neural_runtime import EMBEDDING, NLI, version, manifest
from app.services.neural_text import TAXONOMY, nli_candidates
from app.services.nlp_engine import cosine

_CACHE=OrderedDict();_CACHE_LOCK=threading.RLock();_CACHE_BYTES=512*1024*1024


def invalidate(user):
    with _CACHE_LOCK:
        for key in list(_CACHE):
            if key[0]==user:_CACHE.pop(key,None)


def unavailable(reason):return {'status':'unavailable','reason':reason}


def decode(row):
    pooled=np.frombuffer(row.pooled,dtype='<f4')
    vectors=np.frombuffer(row.windows,dtype='<f4')
    if row.dimension!=384 or not 1<=len(row.spans)<=8 or pooled.size!=384 or vectors.size!=384*len(row.spans):raise ValueError('invalid_vector_size')
    vectors=vectors.reshape(-1,384)
    if not np.isfinite(vectors).all() or not np.isfinite(pooled).all():raise ValueError('invalid_vector_values')
    if not np.allclose(np.linalg.norm(vectors,axis=1),1,atol=1e-3) or abs(np.linalg.norm(pooled)-1)>1e-3:raise ValueError('invalid_vector_norm')
    return pooled,vectors


def write_embedding(db,user,generation,scene,result):
    vectors=np.asarray(result['windows'],dtype='<f4');pooled=np.asarray(result['pooled'],dtype='<f4')
    row=SceneEmbedding(turn_id=scene['turn_id'],version=version('embedding'),user_id=user,generation=generation,scene_id=scene['id'],input_hash=result['input_hash'],dimension=384,
                       pooled=pooled.tobytes(),windows=vectors.tobytes(),spans=result['spans'])
    decode(row)
    db.merge(row)


def canonical_spans(spans, offset_map):
    mapped=[]
    for start,end in spans:
        for segment in offset_map:
            a,b=segment['original'];x,y=segment['redacted'];lo,hi=max(start,a),min(end,b)
            if lo>=hi:continue
            candidate=[x,y] if segment['replacement'] else [x+lo-a,x+hi-a]
            if mapped and candidate[0]<=mapped[-1][1]:mapped[-1][1]=max(mapped[-1][1],candidate[1])
            else:mapped.append(candidate)
    return mapped


def begin(db):
    if db.bind.dialect.name=='sqlite':db.execute(text('BEGIN IMMEDIATE'))


def scrub_raw_retrieval_records(db,user):
    """Remove raw retrieval excerpts retained in idempotent chat snapshots."""
    for record in db.scalars(select(NLPRecord).where(NLPRecord.user_id==user)):
        analysis=copy.deepcopy(record.analysis)
        retrieval=analysis.get('semantic_retrieval',{})
        analysis['semantic_retrieval']={'status':'unavailable','reason':'unredacted_local_memory_erased','method':retrieval.get('method','rrf60'),'index_revision':retrieval.get('index_revision',0),'version':retrieval.get('version',version('embedding')),'local_memory_mode':'redacted','coverage':retrieval.get('coverage',{}),'results':[],'notice':'Stored unredacted retrieval evidence was erased.'}
        analysis['memory_retrieval']=[]
        result=copy.deepcopy(record.result);result['nlp_analysis']=analysis
        record.analysis,record.result=analysis,result


class NeuralMemory:
    def __init__(self,factory):self.factory=factory;self.stop_event=threading.Event();self.thread=None

    def metadata(self,user):
        with self.factory() as db:
            row=db.get(NeuralMemoryState,user)
            local=db.get(LocalProcessingPreference,user)
            memory=db.get(LocalMemoryPreference,user)
            return {'generation':row.generation if row else '', 'index_revision':row.index_revision if row else 0,
                    'share_history_with_provider':row.share_history if row else False,
                    'process_local_unredacted':local.process_unredacted if local else False,
                    'store_local_unredacted_memory':memory.store_unredacted if memory else False,
                    'preference_revision':row.preference_revision if row else 0}

    def preferences(self,user,value=None,process_local_unredacted=None,store_local_unredacted_memory=None):
        if value is None and process_local_unredacted is None and store_local_unredacted_memory is None:return self.metadata(user)
        reset_index=False
        with self.factory() as db:
            begin(db);row=db.get(NeuralMemoryState,user)
            if row is None:row=NeuralMemoryState(user_id=user,generation=str(uuid4()),index_revision=0,share_history=False,preference_revision=0);db.add(row)
            if value is not None:
                row.share_history=value
            if process_local_unredacted is not None:
                local=db.get(LocalProcessingPreference,user)
                if local is None:
                    local=LocalProcessingPreference(user_id=user,process_unredacted=False);db.add(local)
                local.process_unredacted=process_local_unredacted
            if store_local_unredacted_memory is not None:
                memory=db.get(LocalMemoryPreference,user)
                old=memory.store_unredacted if memory else False
                if memory is None:
                    memory=LocalMemoryPreference(user_id=user,store_unredacted=False);db.add(memory)
                memory.store_unredacted=store_local_unredacted_memory
                if old!=store_local_unredacted_memory:
                    reset_index=True;row.generation=str(uuid4());row.index_revision+=1
                    db.execute(delete(SceneEmbedding).where(SceneEmbedding.user_id==user))
                    db.execute(delete(NeuralJob).where(NeuralJob.user_id==user))
                    if not store_local_unredacted_memory:
                        db.execute(delete(LocalRawTurn).where(LocalRawTurn.user_id==user))
                        scrub_raw_retrieval_records(db,user)
                        world=db.get(PWMState,user)
                        for scene in (world.world.get('scenes',[]) if world else []):
                            if scene.get('turn_id'):self.enqueue(db,user,row.generation,scene['turn_id'],'embedding')
                    world=db.get(PWMState,user)
                    if world and world.world.get('canonical_memory'):
                        updated=copy.deepcopy(world.world)
                        updated['canonical_memory']['memory_generation']=row.generation
                        world.world=updated
                        from sqlalchemy.orm.attributes import flag_modified
                        flag_modified(world,'world')
            row.preference_revision+=1;db.commit()
        if reset_index:invalidate(user);NLI.clear(user)
        return self.metadata(user)

    def commit(self,db,user,turn,scene,metadata,embedding,raw_context=None):
        state=db.get(NeuralMemoryState,user)
        if (state.generation if state else '')!=metadata['generation']:
            raise HTTPException(409,detail={'code':'session_changed','message':'World memory was reset. Refresh before resubmitting.'})
        if state is None:state=NeuralMemoryState(user_id=user,generation=str(uuid4()),index_revision=0,share_history=False,preference_revision=0);db.add(state)
        if metadata.get('store_local_unredacted_memory') and raw_context:
            db.merge(LocalRawTurn(turn_id=turn.id,user_id=user,session_id=turn.session_id,raw_text=raw_context['text'],offset_map=raw_context['offset_map'],lexical_vector=raw_context['vector']))
        if embedding and embedding.get('status')=='ready':write_embedding(db,user,state.generation,scene,embedding);state.index_revision+=1
        else:self.enqueue(db,user,state.generation,turn.id,'embedding')
        self.enqueue(db,user,state.generation,turn.id,'nli')
        return {'status':'pending','turn_id':turn.id,'taxonomy_version':TAXONOMY,'version':version('nli'),'local_memory_mode':'unredacted' if metadata.get('store_local_unredacted_memory') else 'redacted'}

    def enqueue(self,db,user,generation,turn_id,kind):
        key=(turn_id,kind,version(kind))
        if db.get(NeuralJob,key) is None:db.add(NeuralJob(turn_id=turn_id,kind=kind,version=key[2],user_id=user,generation=generation,status='pending',attempts=0,due=0,lease=0))

    def reset(self,db,user):
        state=db.get(NeuralMemoryState,user)
        if state is None:state=NeuralMemoryState(user_id=user,generation=str(uuid4()),index_revision=0,share_history=False,preference_revision=0);db.add(state)
        state.generation=str(uuid4());state.index_revision+=1
        db.execute(delete(SceneEmbedding).where(SceneEmbedding.user_id==user));db.execute(delete(NeuralJob).where(NeuralJob.user_id==user));db.execute(delete(LocalRawTurn).where(LocalRawTurn.user_id==user));scrub_raw_retrieval_records(db,user)
        invalidate(user);NLI.clear(user)

    def classify(self,user,analysis,generation,budget=10,text_override=None,offset_map=None):
        text_value=text_override or analysis['redacted_text']
        candidates=[{'spans':[[0,len(text_value)]],'clauses':[]}] if text_override else nli_candidates(analysis)
        result=NLI.request({'user':user,'generation':generation,'text':text_value,'mentions':[] if text_override else analysis.get('mentions',[]),'candidates':candidates,'background':budget>10},budget)
        if text_override and offset_map and result.get('status')=='ready':
            for collection in ('labels','suggestions'):
                for item in result.get(collection,[]):item['spans']=canonical_spans(item.get('spans',[]),offset_map)
        return result

    def embed(self,analysis,budget=2,text_override=None):
        return EMBEDDING.request({'text':text_override or analysis['redacted_text'],'mentions':[] if text_override else analysis.get('mentions',[]),'background':budget>5},budget)

    def _rows(self,user,meta,active,world_revision,deadline):
        key=(user,meta['generation'],version('embedding'),meta['index_revision'],world_revision)
        with _CACHE_LOCK:
            if key in _CACHE:
                rows,size=_CACHE.pop(key);_CACHE[key]=(rows,size);return iter(rows)
        def scan():
            rows=[];size=0;cacheable=True;repairs=[]
            with self.factory() as db:
                query=select(SceneEmbedding).where(SceneEmbedding.user_id==user,SceneEmbedding.generation==meta['generation'],SceneEmbedding.version==version('embedding')).order_by(SceneEmbedding.turn_id)
                for row in db.scalars(query.execution_options(yield_per=256)):
                    if time.monotonic()>deadline:raise TimeoutError()
                    if row.turn_id not in active:continue
                    try:_,v=decode(row)
                    except ValueError:
                        # Corrupt persisted input is never used; durable repair is queued separately.
                        repairs.append(row.turn_id);continue
                    frozen=v.copy();frozen.setflags(write=False)
                    spans=tuple(tuple(tuple(span) for span in window) for window in row.spans)
                    item=(row.turn_id,frozen,spans);size+=v.nbytes+1024
                    if cacheable:
                        rows.append(item)
                        if size>_CACHE_BYTES:cacheable=False;rows=[]
                    yield item
            for turn_id in repairs:self.repair(user,turn_id)
            if cacheable:
                with _CACHE_LOCK:
                    for old in list(_CACHE):
                        if old[0]==user:_CACHE.pop(old,None)
                    while _CACHE and sum(x[1] for x in _CACHE.values())+size>_CACHE_BYTES:_CACHE.popitem(last=False)
                    _CACHE[key]=(rows,size)
        return scan()

    def repair(self,user,turn_id):
        with self.factory() as db:
            state=db.get(NeuralMemoryState,user)
            if state:
                job=db.get(NeuralJob,(turn_id,'embedding',version('embedding')))
                if job:job.status='pending';job.due=0
                else:self.enqueue(db,user,state.generation,turn_id,'embedding')
                db.commit()

    def search(self,user,analysis,world,world_revision,meta,embedding,limit=3,budget=5):
        scenes=copy.deepcopy(world.get('scenes',[]))
        raw_rows={}
        if meta.get('store_local_unredacted_memory'):
            with self.factory() as db:
                raw_rows={row.turn_id:row for row in db.scalars(select(LocalRawTurn).where(LocalRawTurn.user_id==user))}
            for scene in scenes:
                raw=raw_rows.get(scene.get('turn_id'))
                scene['provider_text']=scene['text']
                if raw:scene['text'],scene['vector']=raw.raw_text,raw.lexical_vector
        by_turn={s['turn_id']:s for s in scenes if s.get('turn_id') and (not meta.get('store_local_unredacted_memory') or s['turn_id'] in raw_rows)}
        query_vector=analysis.get('_query_vector',{})
        lexical=[]
        for scene in scenes:
            score=round(cosine(query_vector,scene.get('vector',{})),6)
            if score>=.25:lexical.append((scene,score))
        ordering=lambda item:(-item[1],-int(item[0].get('turn_id') or 0),item[0]['id'])
        lexical=sorted(lexical,key=ordering)[:50];semantic=[];indexed=0;reason=None
        if embedding.get('status')=='ready':
            query=np.asarray(embedding['windows'],dtype=np.float64);deadline=time.monotonic()+budget
            try:
                for turn_id,v,spans in self._rows(user,meta,by_turn,world_revision,deadline):
                    if time.monotonic()>deadline:raise TimeoutError()
                    indexed+=1;scores=query@v.astype(np.float64).T
                    qi,si=np.unravel_index(scores.argmax(),scores.shape);score=round(float(np.clip(scores[qi,si],-1,1)),6)
                    if score>0:semantic.append((by_turn[turn_id],score,embedding['spans'][qi],spans[si]))
                semantic=sorted(semantic,key=ordering)[:50]
            except TimeoutError:semantic=[];reason='search_deadline'
        else:reason=embedding.get('reason','embedding_unavailable')
        merged={}
        for arm,rows in [('lexical',lexical),('semantic',semantic)]:
            for rank,row in enumerate(rows,1):
                scene,score=row[:2];key=(scene.get('turn_id'),scene['id'])
                item=merged.setdefault(key,{'scene_id':scene['id'],'source_turn_id':scene.get('turn_id'),'source_session_id':scene.get('session_id'),'text':scene['text'],'provider_excerpt':scene.get('provider_text',scene['text'])[:300],'lexical_score':None,'semantic_score':None,'fusion_score':0.,'query_spans':[],'scene_spans':[[0,len(scene['text'])]]})
                item[arm+'_score']=score;item['fusion_score']+=1/(60+rank)
                if arm=='semantic':item['query_spans'],item['scene_spans']=row[2:]
        for item in merged.values():
            item['fusion_score']=round(item['fusion_score'],6);item['excerpt']=' … '.join(item['text'][a:b] for a,b in item['scene_spans'])
            query_text=analysis.get('_query_text',analysis['redacted_text'])
            item['query_excerpt']=' … '.join(query_text[a:b] for a,b in item['query_spans'])
        results=sorted(merged.values(),key=lambda i:(-i['fusion_score'],-int(i['source_turn_id'] or 0),i['scene_id']))[:limit]
        return {'status':'ready' if not reason else 'lexical_fallback','reason':reason,'method':'rrf60','index_revision':meta['index_revision'],'version':version('embedding'),'local_memory_mode':'unredacted' if meta.get('store_local_unredacted_memory') else 'redacted',
                'coverage':{'active_scenes':len(scenes),'eligible_scenes':len(by_turn),'indexed_scenes':indexed,'complete':not reason and indexed==len(by_turn)},'results':results,'notice':'Semantic matches are exploratory, not verified relevance.'}

    def classification(self,user,turn_id):
        with self.factory() as db:
            turn=db.get(ChatTurn,turn_id)
            if turn is None or turn.user_id!=user:raise HTTPException(404,detail={'code':'not_found','message':'Turn not found.'})
            job=db.get(NeuralJob,(turn_id,'nli',version('nli')))
            return copy.deepcopy(job.result) if job and job.result else {'status':job.status if job else 'unavailable','reason':None if job else 'not_indexed','turn_id':turn_id}

    def process_one(self):
        now=time.time();token=str(uuid4())
        with self.factory() as db:
            begin(db)
            job=db.scalar(select(NeuralJob).where(((NeuralJob.status=='pending') & (NeuralJob.due<=now)) | ((NeuralJob.status=='running') & (NeuralJob.lease<now))).order_by(NeuralJob.due,NeuralJob.turn_id).limit(1))
            if job is None:return False
            key=(job.turn_id,job.kind,job.version);user=job.user_id;generation=job.generation
            job.status='running';job.lease=now+180;job.lease_token=token;job.attempts+=1
            world=db.get(PWMState,user);state=db.get(NeuralMemoryState,user);record=db.get(NLPRecord,job.turn_id)
            active=world and any(s.get('turn_id')==job.turn_id for s in world.world['scenes'])
            if not active or not state or state.generation!=generation or not record:
                job.status='cancelled';db.commit();return True
            analysis=copy.deepcopy(record.analysis);revision=world.revision;scene=copy.deepcopy(next(s for s in world.world['scenes'] if s.get('turn_id')==job.turn_id));raw=db.get(LocalRawTurn,job.turn_id);raw_payload=copy.deepcopy({'text':raw.raw_text,'offset_map':raw.offset_map}) if raw else None;db.commit()
        result=((self.embed(analysis,120,text_override=raw_payload['text']) if raw_payload else self.embed(analysis,120)) if key[1]=='embedding' else (self.classify(user,analysis,generation,120,text_override=raw_payload['text'],offset_map=raw_payload['offset_map']) if raw_payload else self.classify(user,analysis,generation,120))) if key[2]==version(key[1]) else unavailable('resource_version_changed')
        with self.factory() as db:
            begin(db);job=db.get(NeuralJob,key);state=db.get(NeuralMemoryState,user);world=db.get(PWMState,user)
            if job is None or job.lease_token!=token:return True
            if not state or state.generation!=generation or not world or not any(s.get('turn_id')==key[0] for s in world.world['scenes']):job.status='cancelled'
            elif key[1]=='embedding' and world.revision!=revision:job.status='pending';job.due=time.time()+2
            elif result.get('status')=='ready':
                if key[1]=='embedding':write_embedding(db,user,generation,scene,result);state.index_revision+=1;job.result={'status':'ready'};invalidate(user)
                else:job.result=result
                job.status='ready'
            elif result.get('reason')=='warming':
                job.status='pending';job.attempts=max(0,job.attempts-1);job.due=time.time()+2
            elif result.get('reason') in {'deadline','queue_full','worker_exited','inference_failed'} and job.attempts<3:
                job.status='pending';job.due=time.time()+2**job.attempts
            else:job.status='unavailable';job.result=result
            db.commit()
        return True

    def start(self):
        if self.thread and self.thread.is_alive():return
        self.stop_event.clear();EMBEDDING.start();NLI.start()
        def loop():
            while not self.stop_event.is_set():
                try:worked=self.process_one()
                except Exception:worked=False
                if not worked:self.stop_event.wait(1)
        self.thread=threading.Thread(target=loop,daemon=True);self.thread.start()

    def stop(self):self.stop_event.set();EMBEDDING.stop();NLI.stop()

    def backfill_batch(self,user):
        with self.factory() as db:
            world=db.get(PWMState,user);state=db.get(NeuralMemoryState,user)
            if not world:return {'inserted':0,'remaining':0}
            if not state:self.preferences(user,False);return {'inserted':0,'remaining':len(world.world['scenes'])}
            memory=db.get(LocalMemoryPreference,user);raw_mode=bool(memory and memory.store_unredacted)
            generation,revision=state.generation,world.revision
            existing=set(db.scalars(select(SceneEmbedding.turn_id).where(SceneEmbedding.user_id==user,SceneEmbedding.generation==generation,SceneEmbedding.version==version('embedding'))))
            raw_rows={row.turn_id:row.raw_text for row in db.scalars(select(LocalRawTurn).where(LocalRawTurn.user_id==user))} if raw_mode else {}
            scenes=[copy.deepcopy(s) for s in world.world['scenes'] if s.get('turn_id') and s['turn_id'] not in existing and (not raw_mode or s['turn_id'] in raw_rows)]
            records={s['turn_id']:copy.deepcopy(db.get(NLPRecord,s['turn_id']).analysis) for s in scenes[:32] if db.get(NLPRecord,s['turn_id'])}
        computed=[]
        for scene in scenes[:32]:
            if scene['turn_id'] not in records:continue
            if EMBEDDING.pending:return {'inserted':0,'remaining':len(scenes),'reason':'live_requests_waiting'}
            result=self.embed(records[scene['turn_id']],120,text_override=raw_rows[scene['turn_id']]) if raw_mode else self.embed(records[scene['turn_id']],120)
            if result.get('status')!='ready':return {'inserted':0,'remaining':len(scenes),'reason':result.get('reason')}
            computed.append((scene,result))
        with self.factory() as db:
            begin(db);state=db.get(NeuralMemoryState,user);world=db.get(PWMState,user)
            if not state or state.generation!=generation or not world or world.revision!=revision:return {'inserted':0,'remaining':len(scenes),'reason':'stale_batch'}
            active={s.get('turn_id') for s in world.world['scenes']}
            for scene,result in computed:
                turn=db.get(ChatTurn,scene['turn_id'])
                if scene['turn_id'] in active and turn and turn.user_id==user:write_embedding(db,user,generation,scene,result);state.index_revision+=1
            db.commit();invalidate(user)
        return {'inserted':len(computed),'remaining':max(0,len(scenes)-len(computed))}

    def queue_backfill(self,user):
        """Coordinated API backfill shares the live-priority embedding worker."""
        with self.factory() as db:
            begin(db);world=db.get(PWMState,user);state=db.get(NeuralMemoryState,user)
            if not world:return {'queued':0,'remaining':0,'pending':0,'status':'ready'}
            if not state:
                state=NeuralMemoryState(user_id=user,generation=str(uuid4()),index_revision=0,share_history=False,preference_revision=0);db.add(state)
            memory=db.get(LocalMemoryPreference,user);raw_mode=bool(memory and memory.store_unredacted)
            raw_ids=set(db.scalars(select(LocalRawTurn.turn_id).where(LocalRawTurn.user_id==user))) if raw_mode else set()
            existing=set(db.scalars(select(SceneEmbedding.turn_id).where(SceneEmbedding.user_id==user,SceneEmbedding.generation==state.generation,SceneEmbedding.version==version('embedding'))))
            scenes=[s for s in world.world['scenes'] if s.get('turn_id') and s['turn_id'] not in existing and (not raw_mode or s['turn_id'] in raw_ids)]
            queued=pending=0
            for scene in scenes[:32]:
                turn=db.get(ChatTurn,scene['turn_id'])
                if not turn or turn.user_id!=user:continue
                job=db.get(NeuralJob,(turn.id,'embedding',version('embedding')))
                if job is None:self.enqueue(db,user,state.generation,turn.id,'embedding');queued+=1;pending+=1
                elif job.status in {'pending','running'}:pending+=1
            db.commit()
            return {'queued':queued,'remaining':len(scenes),'pending':pending,'status':'pending' if pending else 'unavailable' if scenes else 'ready'}
