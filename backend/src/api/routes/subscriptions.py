from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.user import User
from ...models.subscription import Subscription
from ...schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse
)


router = APIRouter(
    prefix="/subscriptions",
    tags=["Subscriptions"]
)


@router.post(
    "/subscribe",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_subscription(
    subscription_in: SubscriptionCreate,
    db: Session = Depends(get_db)
):

    # Check that the user exists
    user = db.query(User).filter(
        User.id == subscription_in.user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Allow Free, Basic or Pro
    if subscription_in.plan not in ["free", "basic", "pro"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan must be free, basic or pro"
        )

    # Free plan is valid only for 15 days
    if subscription_in.plan == "free":
        if subscription_in.validity != "15_days":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Free plan must have 15_days validity"
            )

    # Basic and Pro remain Monthly or Yearly
    else:
        if subscription_in.validity not in ["monthly", "yearly"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Basic and Pro plans must be monthly or yearly"
            )

    # Always create a NEW subscription row
    subscribed_at = datetime.now(timezone.utc)

    if subscription_in.plan == "free":
        expires_at = subscribed_at + timedelta(days=15)

    elif subscription_in.validity == "monthly":
        expires_at = subscribed_at + relativedelta(months=1)

    else:
        expires_at = subscribed_at + relativedelta(years=1)

    subscription = Subscription(
        user_id=subscription_in.user_id,
        subscribe=subscription_in.subscribe,
        plan=subscription_in.plan,
        validity=subscription_in.validity,
        subscribed_at=subscribed_at,
        expires_at=expires_at
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return subscription