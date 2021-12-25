from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, TINYINT, FLOAT
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Raid(Base):
    __tablename__ = "raids"

    channel_id = Column(BIGINT(20), nullable=False)
    message_id = Column(BIGINT(20), nullable=False, primary_key=True)
    init_message_id = Column(BIGINT(20), nullable=False)
    gym_id = Column(String(50, "utf8mb4_unicode_ci"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    mon_id = Column(INTEGER(11))
    mon_form = Column(INTEGER(10))
    raid_level = Column(INTEGER(10), default=0)
    raid_start = Column(DateTime(timezone=True))
    raid_end = Column(DateTime(timezone=True))
    role_id = Column(BIGINT(20))


class User(Base):
    __tablename__ = "users"

    user_id = Column(BIGINT(20), nullable=False, primary_key=True)
    level = Column(INTEGER(10))
    team_id = Column(INTEGER(10))
    friendcode = Column(BIGINT(20))
    name = Column(String(50, "utf8mb4_unicode_ci"))
    ingame_name = Column(String(50, "utf8mb4_unicode_ci"))


class Raidmember(Base):
    __tablename__ = "raidmembers"

    message_id = Column(BIGINT(20), nullable=False, primary_key=True)
    user_id = Column(BIGINT(20), nullable=False, primary_key=True)
    amount = Column(INTEGER(10))
    is_late = Column(TINYINT(1), default=0)
    is_remote = Column(TINYINT(1), default=0)


class DMapUser(Base):
    user = Column(BIGINT(20), nullable=True, primary_key=True)
    zoom = Column(FLOAT)
    lat = Column(FLOAT)
    lon = Column(FLOAT)
    style = Column(String(64, "utf8mb4_unicode_ci"))
    move_multiplier = Column(FLOAT)
    marker_multiplier = Column(FLOAT)
    levels = Column(String(16, "utf8mb4_unicode_ci"))
    iconset = Column(INTEGER(16))
