from sqlalchemy import select
from fastapi import HTTPException
from ..models.config import Config
def serialize(x):return {'id':x.id,'name':x.name,'memtable_limit':x.memtable_limit,'l0_trigger':x.l0_trigger,'max_levels':x.max_levels,'final_compaction':x.final_compaction}
def listing(db):return [serialize(x) for x in db.scalars(select(Config).order_by(Config.id))]
def create(db,data):
    if db.scalar(select(Config).where(Config.name==data.name)):raise HTTPException(409,'配置名称已存在')
    x=Config(**data.model_dump());db.add(x);db.commit();return serialize(x)
