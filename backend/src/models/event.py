from datetime import datetime
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import String,DateTime,ForeignKey,UniqueConstraint,Index
from ..config.database import Base
class Event(Base):
    __tablename__='events'
    id:Mapped[int]=mapped_column(primary_key=True)
    revision_id:Mapped[int]=mapped_column(ForeignKey('revisions.id'))
    op_index:Mapped[int]=mapped_column()
    key:Mapped[str]=mapped_column(String(64))
    op:Mapped[str]=mapped_column(String(10))
    value:Mapped[str|None]=mapped_column(String(200),nullable=True)
    event_time:Mapped[datetime]=mapped_column(DateTime)
    __table_args__=(UniqueConstraint('revision_id','op_index'),Index('ix_events_time','event_time'),)
