import json,os,time
from datetime import timedelta
from pathlib import Path
from redis import Redis
from sqlalchemy import select,func
from fastapi import HTTPException
from ..config.settings import REDIS_URL
from ..config.database import Session
from ..models.revision import Revision
from ..models.event import Event
from ..models.hour_state import HourState
from ..models.settlement import Settlement
from ..utils.time import utcnow,iso,normalize
from . import engine as eng
from .revisions import lock_meta,save_hour
from .switch_lock import switch_lock

queue=Redis.from_url(REDIS_URL)
QUEUE='keypeak:settlements'
ARTIFACTS=Path(os.getenv('ARTIFACTS_DIR','/artifacts'))
MAX_RANGE_HOURS=744

def serialize(x):
    return {'id':x.id,'up_to_hour':iso(x.up_to_hour),'status':x.status,'watermark':x.watermark,
            'result':x.result,'error':x.error,'delay_seconds':x.delay_seconds,
            'created_at':iso(x.created_at),'finished_at':iso(x.finished_at)}

def listing(db):return [serialize(x) for x in db.scalars(select(Settlement).order_by(Settlement.id.desc()))]

def detail(db,ident):
    x=db.get(Settlement,ident)
    if not x:raise HTTPException(404,'结算任务不存在')
    return serialize(x)

def _published_window(db):
    return select(func.min(Event.event_time)).join(Revision,Event.revision_id==Revision.id).where(Revision.status=='published')

def create(db,data,enqueue=True):
    up=normalize(data.up_to_hour)
    if up!=eng.hour_floor(up):raise HTTPException(422,'结算目标必须整点对齐（分秒为 0）')
    if db.scalar(select(Settlement).where(Settlement.up_to_hour==up)):raise HTTPException(409,'该小时已有结算任务')
    with switch_lock:
        meta=lock_meta(db)
        first_event=db.scalar(_published_window(db))
        if first_event is None:raise HTTPException(422,'还没有已发布的修订批次，无法结算')
        horizon=meta.horizon
        if horizon is not None and up<=horizon:raise HTTPException(422,'该小时已经结算过，请选择更晚的整点')
        first=horizon+timedelta(hours=1) if horizon else eng.hour_floor(first_event)
        if up<first:raise HTTPException(422,'结算目标早于首个待结算小时')
        if up-first>=timedelta(hours=MAX_RANGE_HOURS):raise HTTPException(422,'单次结算跨度不能超过 %d 小时'%MAX_RANGE_HOURS)
        x=Settlement(up_to_hour=up,delay_seconds=data.delay_seconds)
        db.add(x);db.commit()
    if enqueue:queue.rpush(QUEUE,x.id)
    return serialize(x)

def events_up_to(db,watermark,start_hour,end_excl):
    q=(select(Event).join(Revision,Event.revision_id==Revision.id)
       .where(Revision.status=='published',Revision.publish_seq<=watermark,
              Event.event_time>=start_hour,Event.event_time<end_excl))
    return [{'op':e.op,'key':e.key,'event_time':e.event_time,'recv_seq':e.id} for e in db.scalars(q)]

def apply_settlement(db,x):
    """在切换锁内执行：水位线快照 → 逐小时演算 → 推进结算水位，同一事务提交。"""
    meta=lock_meta(db)
    watermark=db.scalar(select(func.max(Revision.publish_seq)).where(Revision.status=='published')) or 0
    horizon=meta.horizon
    if horizon is not None and x.up_to_hour<=horizon:
        return {'watermark':watermark,'note':'目标小时已被更早的结算覆盖','hours':[]}
    if horizon is None:
        first_event=db.scalar(_published_window(db))
        if first_event is None:return {'watermark':watermark,'note':'没有可结算的事件','hours':[]}
        start_hour=eng.hour_floor(first_event);state=set()
    else:
        start_hour=horizon+timedelta(hours=1)
        state=set(db.get(HourState,horizon).end_keys)
    if x.delay_seconds:time.sleep(x.delay_seconds)
    grouped=eng.group_by_hour(events_up_to(db,watermark,start_hour,x.up_to_hour+timedelta(hours=1)))
    hours=[]
    h=start_hour
    while h<=x.up_to_hour:
        start=sorted(state)
        peak=eng.sweep(state,grouped.get(h,[]))
        save_hour(db,h,peak,start,sorted(state),'settlement:%d'%x.id)
        hours.append({'hour':iso(h),'peak':peak,'start':len(start),'end':len(state)})
        h+=timedelta(hours=1)
    meta.horizon=x.up_to_hour
    return {'watermark':watermark,'from':iso(start_hour),'to':iso(x.up_to_hour),'hours':hours}

def execute(ident):
    with Session() as db:
        x=db.get(Settlement,ident)
        if not x or x.status=='published':return
        x.status='running';db.commit()
        try:
            with switch_lock:
                result=apply_settlement(db,x)
                x.status='published';x.result=result;x.finished_at=utcnow()
                db.commit()
        except Exception as exc:
            db.rollback();x.status='failed';x.error=str(exc)[:500];db.commit();return
        try:
            ARTIFACTS.mkdir(parents=True,exist_ok=True)
            (ARTIFACTS/f'settlement-{ident}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
        except OSError:pass
