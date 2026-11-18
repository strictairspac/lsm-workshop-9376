import time,json,traceback
from pathlib import Path
from sqlalchemy import select
from .config.database import Session
from .models.trial import Trial
from .models.dataset import Dataset
from .models.config import Config
from .services.trial import queue
from .services.lsm_engine import simulate
heartbeat=Path('/artifacts/worker.heartbeat')
def run_one(ident):
    with Session() as db:
        x=db.get(Trial,ident)
        if not x or x.result is not None:return
        x.status='running';db.commit()
        try:
            x.result=simulate(x.input_snapshot['entries'],x.input_snapshot['config']);x.status='passed'
        except Exception as exc:x.result={'error':str(exc)[:500]};x.status='failed'
        db.commit();Path(f'/artifacts/lsm-trial-{ident}.json').write_text(json.dumps(x.result,ensure_ascii=False,indent=2))
while True:
    try:
        heartbeat.write_text(str(time.time()));item=queue.blpop('lsm:jobs',timeout=2)
        if item:run_one(int(item[1]))
        else:
            with Session() as db:pending=list(db.scalars(select(Trial.id).where(Trial.status.in_(['queued','running']))))
            for ident in pending:run_one(ident)
    except Exception:traceback.print_exc();time.sleep(2)
