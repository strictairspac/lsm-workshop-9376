from datetime import datetime
from pydantic import BaseModel,Field
class SettlementInput(BaseModel):
    up_to_hour:datetime
    delay_seconds:int=Field(default=0,ge=0,le=10)
