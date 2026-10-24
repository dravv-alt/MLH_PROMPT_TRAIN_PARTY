"""Resumable, owner-scoped embedding backfill. No generation or topic replay."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import argparse
import time
import os
import httpx
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1]/'.env')
from app.models.db import init_db
from app.services.nlp_service import get_nlp_service
from app.services.neural_runtime import EMBEDDING

parser=argparse.ArgumentParser();parser.add_argument('--user-id');parser.add_argument('--offline',action='store_true');parser.add_argument('--api-url',default='http://127.0.0.1:8000');parser.add_argument('--token-env',default='SANCTUARY_BACKFILL_TOKEN');args=parser.parse_args()
if not args.offline:
    token=os.getenv(args.token_env)
    if not token:raise SystemExit('Set the configured token environment variable to an authenticated owner token, or use --offline --user-id while the API is idle.')
    with httpx.Client(base_url=args.api_url,headers={'Authorization':'Bearer '+token},timeout=10) as client:
        while True:
            response=client.post('/nlp/neural/backfill');response.raise_for_status();result=response.json();print(result,flush=True)
            if not result['remaining']:break
            if result['status']=='unavailable':raise SystemExit('Backfill paused; inspect /nlp/neural/status and repair resources before retrying.')
            time.sleep(2)
    raise SystemExit(0)
if not args.user_id:parser.error('--offline requires --user-id')
init_db();service=get_nlp_service();EMBEDDING.start()
try:
    for _ in range(60):
        if EMBEDDING.state=='ready':break
        time.sleep(1)
    while True:
        result=service.neural.backfill_batch(args.user_id);print(result,flush=True)
        if not result['remaining']:break
        if result.get('reason') not in {None,'stale_batch','live_requests_waiting','warming'}:raise SystemExit('Backfill paused; fix resources and rerun.')
        time.sleep(1)
finally:EMBEDDING.stop()
