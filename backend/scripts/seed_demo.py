from datetime import datetime
from sqlalchemy import select
from src.config.database import Base,engine,Session
from src.models.user import User
from src.models.revision import Revision
from src.models.settlement import Settlement
from src.models.hour_state import HourState
from src.models.event import Event
from src.models.meta import Meta
from src.utils.password import hash_password
from src.schemas.revision import RevisionInput,PublishInput
from src.schemas.settlement import SettlementInput
from src.services import revisions as rev_svc,settlements as set_svc

def put(t,k,v):return {'op':'put','key':k,'value':v,'event_time':t}
def delete(t,k):return {'op':'delete','key':k,'event_time':t}

PUBLISHED=[
 ('am-baseline-0910','早班基线：09–10 点的写入、覆盖与删键；10 点峰值应为 4。',[
   put('2026-11-18T09:05:00Z','sensor-01','18.2'),
   put('2026-11-18T09:10:00Z','sensor-02','19.1'),
   put('2026-11-18T09:20:00Z','sensor-03','22.4'),
   put('2026-11-18T09:40:00Z','sensor-02','19.6'),
   delete('2026-11-18T09:50:00Z','sensor-01'),
   put('2026-11-18T10:05:00Z','sensor-04','17.0'),
   put('2026-11-18T10:30:00Z','sensor-05','21.6'),
   delete('2026-11-18T10:45:00Z','sensor-03')]),
 ('late-morning-11','11 点常规事件；结算水位停在 10 点，本批留作待结算预览。',[
   put('2026-11-18T11:10:00Z','sensor-06','20.3'),
   delete('2026-11-18T11:30:00Z','sensor-02'),
   put('2026-11-18T11:50:00Z','sensor-01','18.9')]),
]
STAGED=[
 ('late-delete-sensor04','迟到删键演练：sensor-04 实际于 10:10 离线。发布后 10 点峰值 4→3，并跨小时改写 11 点起点状态。',[
   delete('2026-11-18T10:10:00Z','sensor-04')]),
 ('noon-backfill-12','正午补传演练：两条 12 点写入，用于结算推进与切换中断恢复演练。',[
   put('2026-11-18T12:05:00Z','sensor-07','23.0'),
   put('2026-11-18T12:20:00Z','sensor-08','18.9')]),
]
SETTLE_TO='2026-11-18T10:00:00Z'

def seed():
    Base.metadata.create_all(engine)
    with Session() as db:
        for role in ('admin','operator','viewer'):
            email=role+'@beiling.test'
            if not db.scalar(select(User).where(User.email==email)):
                db.add(User(email=email,role=role,password_hash=hash_password('EdgeStore!17')))
        db.commit()
        for name,note,ops in PUBLISHED:
            if not db.scalar(select(Revision).where(Revision.name==name)):
                created=rev_svc.create(db,RevisionInput(name=name,note=note,ops=ops))
                rev_svc.publish(db,created['id'],PublishInput())
        for name,note,ops in STAGED:
            if not db.scalar(select(Revision).where(Revision.name==name)):
                rev_svc.create(db,RevisionInput(name=name,note=note,ops=ops))
        meta=db.get(Meta,1)
        settled=meta and meta.horizon and meta.horizon>=datetime(2026,11,18,10)
        if not settled and not db.scalar(select(Settlement).where(Settlement.up_to_hour==datetime(2026,11,18,10))):
            s=set_svc.create(db,SettlementInput(up_to_hour=SETTLE_TO),enqueue=False)
            set_svc.execute(s['id'])
        return {name:db.query(model).count() for name,model in
                [('users',User),('revisions',Revision),('events',Event),('settlements',Settlement),('hour_states',HourState)]}
if __name__=='__main__':print(seed())
