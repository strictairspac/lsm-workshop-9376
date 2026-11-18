from sqlalchemy import select
from fastapi import HTTPException
from redis import Redis
from ..config.settings import REDIS_URL
from ..models.trial import Trial
from ..models.dataset import Dataset
from ..models.config import Config
from .config import serialize as config_dict
queue=Redis.from_url(REDIS_URL)
def serialize(x):return {'id':x.id,'name':x.name,'dataset_id':x.dataset_id,'config_id':x.config_id,'status':x.status,'created_at':str(x.created_at),'input_snapshot':x.input_snapshot,'result':x.result}
def listing(db):return [serialize(x) for x in db.scalars(select(Trial).order_by(Trial.id.desc()))]
def detail(db,ident):
    x=db.get(Trial,ident)
    if not x:raise HTTPException(404,'试验不存在')
    return serialize(x)
def create(db,data):
    dataset=db.get(Dataset,data.dataset_id);config=db.get(Config,data.config_id)
    if not dataset or not config:raise HTTPException(404,'写入批次或存储配置不存在')
    if db.scalar(select(Trial).where(Trial.name==data.name)):raise HTTPException(409,'试验名称已存在')
    if len(list(db.scalars(select(Trial).where(Trial.status.in_(['queued','running'])))))>=20:raise HTTPException(429,'待运行试验上限20个')
    x=Trial(**data.model_dump(),input_snapshot={'entries':dataset.entries,'config':config_dict(config)});db.add(x);db.commit();queue.rpush('lsm:jobs',x.id);return serialize(x)
