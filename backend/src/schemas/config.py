from pydantic import BaseModel,Field
class ConfigInput(BaseModel):
    name:str=Field(min_length=2,max_length=120)
    memtable_limit:int=Field(ge=2,le=64)
    l0_trigger:int=Field(ge=2,le=8)
    max_levels:int=Field(ge=2,le=6)
    final_compaction:bool=True
