from datetime import datetime
from typing import Literal
from pydantic import BaseModel,Field,model_validator
class OpInput(BaseModel):
    op:Literal['put','delete']
    key:str=Field(min_length=1,max_length=64)
    value:str|None=Field(default=None,max_length=200)
    event_time:datetime
    @model_validator(mode='after')
    def check_value(self):
        if self.op=='put' and self.value is None:raise ValueError('put 操作必须包含字符串 value')
        return self
class RevisionInput(BaseModel):
    name:str=Field(min_length=2,max_length=120)
    note:str=Field(default='',max_length=2000)
    ops:list[OpInput]=Field(min_length=1,max_length=500)
class PublishInput(BaseModel):
    simulate_crash:bool=False
    delay_seconds:int=Field(default=0,ge=0,le=10)
