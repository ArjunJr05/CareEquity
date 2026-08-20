from pydantic import BaseModel
from datetime import datetime


class SubscriptionCreate(BaseModel):
    user_id: int
    subscribe: bool
    plan: str
    validity: str


class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    subscribe: bool
    plan: str
    validity: str
    subscribed_at: datetime

    class Config:
        from_attributes = True
        orm_mode = True