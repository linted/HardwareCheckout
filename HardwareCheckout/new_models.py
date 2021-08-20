from functools import partial

from .config import db_path, ctfd_db_path

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table
from sqlalchemy import or_
from sqlalchemy.orm import relationship
from tornado_sqlalchemy import SQLAlchemy, as_future
from sqlalchemy.sql import func

db = SQLAlchemy(
    url=db_path,
    # engine_options={
    #     "max_overflow": 15,
    #     "pool_pre_ping": True,
    #     "pool_recycle": 60 * 60,
    #     "pool_size": 30,
    # },
)

if ctfd_db_path:
    ctfd_db = SQLAlchemy(
        url=ctfd_db_path,
        engine_options={
            "max_overflow": 15,
            "pool_pre_ping": True,
            "pool_recycle": 60 * 60,
            "pool_size": 30,
        },
    )
else:
    ctfd_db = False

# userrole_association = Table('userroles', db.Model.metadata,
#     Column('userId', ForeignKey('user.id'), primary_key=True),
#     Column('roleId', ForeignKey('roles.id'), primary_key=True)
# )

class User(db.Model):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    password = Column(String(93))
    name = Column(String(100), unique=True)
    ctf = Column(Integer)

    roles = relationship("Roles", secondary="userroles", back_populates="users")
    deviceQueue = relationship("UserQueue", back_populates="user")


class Roles(db.Model):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)

    users = relationship("User", secondary="userroles", back_populates="roles")



class UserRoles(db.Model):
    __tablename__ = "userroles"
    roleId = Column(Integer, ForeignKey("roles.id"), primary_key=True)
    userId = Column(Integer, ForeignKey("user.id"), primary_key=True)


class UserQueue(db.Model):
    __tablename__ = "userqueue"
    userId = Column(Integer, ForeignKey("user.id"), primary_key=True)
    deviceTypeId = Column(Integer, ForeignKey("devicetype.id"), primary_key=True)
    timestamp = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="deviceQueue")
    deviceType = relationship("DeviceType", back_populates="users")


class DeviceType(db.Model):
    __tablename__ = "devicetype"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), unique=True)
    enabled = Column(Integer)
    image_path = Column(String(200))

    users = relationship("UserQueue", back_populates="deviceType")
    devices = relationship("Device", back_populates="deviceType")


class Device(db.Model):
    __tablename__ = "device"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True)
    password = Column(String(93), unique=True)
    deviceTypeId = Column(Integer, ForeignKey("devicetype.id"))

    session = relationship("DeviceSession", back_populates="device", uselist=False)
    deviceType = relationship("DeviceType", back_populates="devices")


class DeviceSession(db.Model):
    __tablename__ = "devicesession"
    id = Column(Integer, primary_key=True)
    entity_id = Column(String(200), unique=True)
    sshAddr = Column(String(200))
    webUrl = Column(String(200))
    roUrl = Column(String(200))
    state = Column(String(200))
    ctf = Column(Integer)
    device_id = Column(Integer, ForeignKey("device.id"))

    device = relationship("Device", back_populates="session")


class TwitchStream(db.Model):
    __tablename__ = "twitchstreams"
    id = Column(Integer, primary_key=True)
    name = Column(String(200))