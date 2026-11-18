from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import String,JSON
from ..config.database import Base
class Config(Base):
    __tablename__='configs'
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(120),unique=True)
    memtable_limit:Mapped[int]
    l0_trigger:Mapped[int]
    max_levels:Mapped[int]
    final_compaction:Mapped[bool]
