from datetime import datetime
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import String,JSON,DateTime,func
from ..config.database import Base
from ..constants.enums import SETTLEMENT_STATUSES
class Settlement(Base):
    __tablename__='settlements'
    id:Mapped[int]=mapped_column(primary_key=True)
    up_to_hour:Mapped[datetime]=mapped_column(DateTime,unique=True)
    delay_seconds:Mapped[int]=mapped_column(default=0)
    status:Mapped[str]=mapped_column(String(20),default=SETTLEMENT_STATUSES[0])
    watermark:Mapped[int|None]=mapped_column(nullable=True)
    result:Mapped[dict|None]=mapped_column(JSON,nullable=True)
    error:Mapped[str|None]=mapped_column(String(500),nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,server_default=func.now())
    finished_at:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
