from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base
from typing import Any


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    date = Column(String)
    category = Column(String, default="Workshop")
    deadline = Column(String, nullable=True)

    topics: Any = relationship(
        "Topic", back_populates="event", cascade="all, delete-orphan"
    )
    registrations: Any = relationship(
        "Registration", back_populates="event", cascade="all, delete-orphan"
    )


class Topic(Base):
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    title = Column(String)

    event: Any = relationship("Event", back_populates="topics")


class Registration(Base):
    __tablename__ = "registrations"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    name = Column(String)
    email = Column(String)
    topics = Column(String)

    event: Any = relationship("Event", back_populates="registrations")


class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    password = Column(String)
