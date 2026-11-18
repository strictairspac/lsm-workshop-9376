import time
from datetime import timedelta
from sqlalchemy import select,func,or_
from fastapi import HTTPException
from ..models.revision import Revision
from ..models.event import Event
from ..models.hour_state import HourState
from ..models.meta import Meta
from ..utils.time import utcnow,iso,normalize
from . import engine as eng
from .switch_lock import switch_lock

def lock_meta(db):
    meta=db.scalar(select(Meta).where(Meta.id==1).with_for_update())
    if meta is None:
        meta=Meta(id=1,horizon=None);db.add(meta);db.flush()
    return meta

def serialize(x,with_ops=False):
    d={'id':x.id,'name':x.name,'note':x.note,'status':x.status,'publish_seq':x.publish_seq,
       'affected_from':iso(x.affected_from),'diff':x.diff or [],'recomputed':x.recomputed or [],
       'op_count':len(x.ops),'created_at':iso(x.created_at),'published_at':iso(x.published_at)}
    if with_ops:d['ops']=x.ops
    return d

def listing(db):return [serialize(x,with_ops=True) for x in db.scalars(select(Revision).order_by(Revision.id.desc()))]

def detail(db,ident):
    x=db.get(Revision,ident)
    if not x:raise HTTPException(404,'修订批次不存在')
    return serialize(x,with_ops=True)

def create(db,data):
    if db.scalar(select(Revision).where(Revision.name==data.name)):raise HTTPException(409,'修订批次名称已存在')
    ops=[{'op':o.op,'key':o.key,'value':o.value,'event_time':iso(normalize(o.event_time))} for o in data.ops]
    rev=Revision(name=data.name,note=data.note,ops=ops,status='staged')
    db.add(rev);db.flush()
    for i,o in enumerate(data.ops):
        db.add(Event(revision_id=rev.id,op_index=i,key=o.key,op=o.op,value=o.value,event_time=normalize(o.event_time)))
    db.commit()
    return serialize(rev)

def published_events(db,extra_revision=None):
    """已发布修订的事件（可并入一个正在切换的批次），元素带 recv_seq（接收顺序）。"""
    q=(select(Event).join(Revision,Event.revision_id==Revision.id)
       .where(or_(Revision.status=='published',Revision.id==(extra_revision or -1))))
    return [{'op':e.op,'key':e.key,'event_time':e.event_time,'recv_seq':e.id,'revision_id':e.revision_id}
            for e in db.scalars(q)]

def save_hour(db,hour,peak,start_keys,end_keys,source):
    row=db.get(HourState,hour)
    if row is None:
        row=HourState(hour_start=hour);db.add(row)
    row.peak=peak;row.start_keys=start_keys;row.end_keys=end_keys;row.source=source

def recompute_affected(db,rev,affected,horizon):
    """只重算受影响的小时 [affected, horizon]：起点状态收敛后即停止，更早的小时不碰。"""
    stored={h.hour_start:h for h in db.scalars(select(HourState))}
    first_stored=min(stored) if stored else None
    sweep_from=max(affected,first_stored) if first_stored else affected
    events=published_events(db,extra_revision=rev.id)
    if sweep_from in stored and affected>=sweep_from:
        state=set(stored[sweep_from].start_keys)
    else:
        state=eng.state_before(events,sweep_from)
    grouped=eng.group_by_hour([e for e in events if sweep_from<=e['event_time']<horizon+timedelta(hours=1)])
    batch_hours={eng.hour_floor(e.event_time) for e in db.scalars(select(Event).where(Event.revision_id==rev.id))}
    diff,recomputed=[],[]
    h=sweep_from
    while h<=horizon:
        start=set(state)
        peak=eng.sweep(state,grouped.get(h,[]))
        row=stored.get(h)
        if h>sweep_from and row is not None and h not in batch_hours and set(row.start_keys)==start:
            break
        before=row.peak if row else None
        save_hour(db,h,peak,sorted(start),sorted(state),'revision:%d'%rev.id)
        recomputed.append(iso(h))
        if before is None or before!=peak:
            diff.append({'hour':iso(h),'before':before,'after':peak})
        h+=timedelta(hours=1)
    return diff,recomputed

def publish(db,ident,data):
    rev=db.get(Revision,ident)
    if not rev:raise HTTPException(404,'修订批次不存在')
    if rev.status=='published':
        return serialize(rev)
    if rev.status=='staged':
        rev.status='switching';db.commit()
    if data.simulate_crash:
        raise HTTPException(500,'演练：切换在生效前中断，批次保持 switching 状态；再次发布即可恢复')
    db.commit()
    with switch_lock:
        meta=lock_meta(db)
        db.refresh(rev)
        if rev.status=='published':
            db.commit();return serialize(rev)
        if data.delay_seconds:time.sleep(data.delay_seconds)
        own=list(db.scalars(select(Event).where(Event.revision_id==rev.id)))
        affected=min(eng.hour_floor(e.event_time) for e in own)
        horizon=meta.horizon
        diff,recomputed=[],[]
        if horizon is not None and affected<=horizon:
            diff,recomputed=recompute_affected(db,rev,affected,horizon)
        rev.status='published'
        rev.publish_seq=(db.scalar(select(func.max(Revision.publish_seq))) or 0)+1
        rev.affected_from=affected
        rev.diff=diff
        rev.recomputed=recomputed
        rev.published_at=utcnow()
        db.commit()
    return serialize(rev)
