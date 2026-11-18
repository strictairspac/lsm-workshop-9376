from datetime import datetime
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import String,JSON,DateTime,func
from ..config.database import Base
from ..constants.enums import REVISION_STATUSES
class Revision(Base):
    __tablename__='revisions'
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(120),unique=True)
    note:Mapped[str]=mapped_column(String(2000))
    ops:Mapped[list]=mapped_column(JSON)
    status:Mapped[str]=mapped_column(String(20),default=REVISION_STATUSES[0])
    publish_seq:Mapped[int|None]=mapped_column(nullable=True,unique=True)
    affected_from:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
    diff:Mapped[list|None]=mapped_column(JSON,nullable=True)
    recomputed:Mapped[list|None]=mapped_column(JSON,nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,server_default=func.now())
    published_at:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
