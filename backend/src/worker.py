import os,time,traceback
from pathlib import Path
from sqlalchemy import select
from .config.database import Session
from .models.settlement import Settlement
from .services.settlements import queue,execute,QUEUE
heartbeat=Path(os.getenv('ARTIFACTS_DIR','/artifacts'))/'worker.heartbeat'
def recover():
    """进程重启后接管未完成结算：queued/running 任务按提交顺序重放，幂等。"""
    with Session() as db:
        pending=list(db.scalars(select(Settlement.id).where(Settlement.status.in_(['queued','running'])).order_by(Settlement.id)))
    for ident in pending:execute(ident)
def main():
    while True:
        try:
            heartbeat.parent.mkdir(parents=True,exist_ok=True)
            heartbeat.write_text(str(time.time()))
            item=queue.blpop(QUEUE,timeout=2)
            if item:execute(int(item[1]))
            else:recover()
        except Exception:traceback.print_exc();time.sleep(2)
if __name__=='__main__':main()
