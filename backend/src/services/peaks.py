from datetime import timedelta
from sqlalchemy import select,func
from ..models.revision import Revision
from ..models.event import Event
from ..models.hour_state import HourState
from ..models.meta import Meta
from ..models.settlement import Settlement
from ..utils.time import iso
from . import engine as eng
from .settlements import MAX_RANGE_HOURS

def published(db):
    rows=list(db.scalars(select(HourState).order_by(HourState.hour_start)))
    meta=db.get(Meta,1)
    return {'horizon':iso(meta.horizon) if meta else None,
            'hours':[{'hour':iso(h.hour_start),'peak':h.peak,'start_keys':h.start_keys,
                      'end_keys':h.end_keys,'source':h.source} for h in rows]}

def pending(db):
    """待结算预览：按当前全部已发布修订实时演算，不落库。"""
    meta=db.get(Meta,1)
    horizon=meta.horizon if meta else None
    q=select(Event).join(Revision,Event.revision_id==Revision.id).where(Revision.status=='published')
    events=[{'op':e.op,'key':e.key,'event_time':e.event_time,'recv_seq':e.id} for e in db.scalars(q)]
    if not events:return {'horizon':iso(horizon),'hours':[],'truncated':False}
    if horizon is not None:
        start_hour=horizon+timedelta(hours=1)
        state=set(db.get(HourState,horizon).end_keys)
    else:
        start_hour=eng.hour_floor(min(e['event_time'] for e in events));state=set()
    last=eng.hour_floor(max(e['event_time'] for e in events))
    truncated=False
    if last>=start_hour+timedelta(hours=MAX_RANGE_HOURS):
        last=start_hour+timedelta(hours=MAX_RANGE_HOURS-1);truncated=True
    grouped=eng.group_by_hour([e for e in events if e['event_time']>=start_hour])
    hours=[]
    h=start_hour
    while h<=last:
        start=sorted(state)
        peak=eng.sweep(state,grouped.get(h,[]))
        hours.append({'hour':iso(h),'peak':peak,'start':len(start),'end':len(state)})
        h+=timedelta(hours=1)
    return {'horizon':iso(horizon),'hours':hours,'truncated':truncated}

def overview(db):
    meta=db.get(Meta,1)
    return {'horizon':iso(meta.horizon) if meta else None,
            'published_hours':db.scalar(select(func.count()).select_from(HourState)) or 0,
            'pending_hours':len(pending(db)['hours']),
            'open_revisions':db.scalar(select(func.count()).select_from(Revision).where(Revision.status!='published')) or 0,
            'open_settlements':db.scalar(select(func.count()).select_from(Settlement).where(Settlement.status.in_(['queued','running']))) or 0}
