from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import String,JSON
from ..config.database import Base
class Dataset(Base):
    __tablename__='datasets'
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(120),unique=True)
    description:Mapped[str]=mapped_column(String(2000))
    entries:Mapped[list]=mapped_column(JSON)
