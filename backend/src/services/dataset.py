from sqlalchemy import select
from fastapi import HTTPException
from ..models.dataset import Dataset
def serialize(x):return {'id':x.id,'name':x.name,'description':x.description,'entries':x.entries,'operation_count':len(x.entries),'distinct_keys':len({e['key'] for e in x.entries})}
def listing(db):return [serialize(x) for x in db.scalars(select(Dataset).order_by(Dataset.id))]
def create(db,data):
    if db.scalar(select(Dataset).where(Dataset.name==data.name)):raise HTTPException(409,'写入批次名称已存在')
    x=Dataset(**data.model_dump());db.add(x);db.commit();return serialize(x)
