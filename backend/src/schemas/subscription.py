from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SubscriptionCreate(BaseModel):
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    subscribe: bool = True
    plan: str
    validity: str


class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    subscribe: bool
    plan: str
    validity: str
    tokens_allocated: int = 250000
    tokens_used: int = 0
    subscribed_at: datetime

    class Config:
        from_attributes = True
        orm_mode = True