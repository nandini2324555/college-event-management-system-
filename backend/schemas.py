from pydantic import BaseModel, validator
from typing import Optional


class EventCreate(BaseModel):
    title: str
    description: str
    date: str
    category: str = "Workshop"
    deadline: Optional[str] = None

    @validator("title")
    def title_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Event title cannot be empty")
        return v.strip()

    @validator("description")
    def description_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip()


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    category: Optional[str] = None
    deadline: Optional[str] = None


class TopicCreate(BaseModel):
    event_id: int
    title: str

    @validator("title")
    def title_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Topic title cannot be empty")
        return v.strip()


class RegistrationCreate(BaseModel):
    event_id: int
    name: str
    email: str

    @validator("name")
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @validator("email")
    def email_valid(cls, v):
        if not v or not v.strip():
            raise ValueError("Email cannot be empty")
        if "@" not in v or "." not in v:
            raise ValueError("Please enter a valid email address")
        return v.strip()
