from pydantic import BaseModel,Field
class TrialInput(BaseModel):
    name:str=Field(min_length=2,max_length=120)
    dataset_id:int=Field(gt=0)
    config_id:int=Field(gt=0)
