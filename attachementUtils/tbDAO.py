from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, Integer

Base = declarative_base()


class AttachementHeader(Base):
    # 表的名字:
    __tablename__ = 'ATTACHEMENT_HEADER'

    def __init__(self):
        pass

    # 表的结构:
    downloaded = Column(DateTime)
    title = Column(String)
    source = Column(String)  # observation,
    link = Column(String, primary_key=True)
    path = Column(String)
    pid = Column(String)
    mod_date = Column(DateTime)
    status = Column(Integer)
    comment = Column(String)
