from datetime import datetime
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import String,JSON,DateTime
from ..config.database import Base
from ..utils.time import utcnow
class HourState(Base):
    __tablename__='hour_states'
    hour_start:Mapped[datetime]=mapped_column(DateTime,primary_key=True)
    peak:Mapped[int]=mapped_column()
    start_keys:Mapped[list]=mapped_column(JSON)
    end_keys:Mapped[list]=mapped_column(JSON)
    source:Mapped[str]=mapped_column(String(40))
    updated_at:Mapped[datetime]=mapped_column(DateTime,default=utcnow,onupdate=utcnow)
