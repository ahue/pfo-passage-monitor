
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

import pfo_passage_monitor.util as util 

# pgc = util.config["postgres"]


# engine = sa.create_engine('postgresql://{pgc["user"]}:{pgc["userpassword"]}@{pgc["host"]}:{pgc["port"]}/{pgc["database"]}')
# session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()

class Passage(Base):
    __tablename__ = "passage"

    id = sa.Column(sa.Integer, primary_key=True)
    doc = sa.Column(MutableDict.as_mutable(JSONB), nullable=False)
    start = sa.Column(sa.Integer, nullable=False)
    pet = sa.Column(sa.Integer)

    @property
    def pattern(self):
        return self.doc["pattern"]

    @property
    def duration(self):
        return self.doc["duration_s"]

    @property
    def direction(self):
        return self.doc["direction"]["direction"]