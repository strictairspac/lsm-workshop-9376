from datetime import datetime
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import DateTime
from ..config.database import Base
class Meta(Base):
    __tablename__='meta'
    id:Mapped[int]=mapped_column(primary_key=True)
    horizon:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
