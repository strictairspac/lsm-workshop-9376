from datetime import datetime
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import String,JSON,ForeignKey,DateTime,func
from ..config.database import Base
from ..constants.enums import STATUSES
class Trial(Base):
    __tablename__='trials'
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(120),unique=True)
    dataset_id:Mapped[int]=mapped_column(ForeignKey('datasets.id'))
    config_id:Mapped[int]=mapped_column(ForeignKey('configs.id'))
    status:Mapped[str]=mapped_column(String(20),default=STATUSES[0])
    input_snapshot:Mapped[dict]=mapped_column(JSON)
    result:Mapped[dict|None]=mapped_column(JSON,nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,server_default=func.now())
