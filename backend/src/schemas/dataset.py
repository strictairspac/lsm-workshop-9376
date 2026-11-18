from typing import Literal
from pydantic import BaseModel,Field,model_validator
class Entry(BaseModel):
    op:Literal['put','delete']
    key:str=Field(min_length=1,max_length=64)
    value:str|None=Field(default=None,max_length=200)
    @model_validator(mode='after')
    def check_value(self):
        if self.op=='put' and self.value is None:raise ValueError('put 操作必须包含字符串 value')
        return self
class DatasetInput(BaseModel):
    name:str=Field(min_length=2,max_length=120)
    description:str=Field(max_length=2000)
    entries:list[Entry]=Field(min_length=1,max_length=2000)
