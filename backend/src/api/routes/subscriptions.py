from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from ...core.database import get_db
from ...models.user import User
from ...models.subscription import Subscription
from ...schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse
)
from ...core.security import get_password_hash


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
    # 1. Resolve user
    user = None
    if subscription_in.user_id:
        user = db.query(User).filter(User.id == subscription_in.user_id).first()

    if not user and subscription_in.user_email:
        clean_email = subscription_in.user_email.strip().lower()
        user = db.query(User).filter(func.lower(User.email) == clean_email).first()

    if not user:
        user = db.query(User).first()

    if not user:
        target_email = subscription_in.user_email or "doctor@careequity.com"
        user = User(
            name="Care Navigator",
            email=target_email,
            hashed_password=get_password_hash("CareEquity2026!"),
            status=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    plan_clean = subscription_in.plan.lower()

    # Allow Free, Basic or Pro
    if plan_clean not in ["free", "basic", "pro"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan must be free, basic or pro"
        )

    # Free plan is valid only for 15 days
    validity_clean = subscription_in.validity.lower()
    if plan_clean == "free":
        validity_clean = "15_days"
    else:
        if validity_clean not in ["monthly", "yearly"]:
            validity_clean = "monthly"

    # Create a NEW subscription row in Postgres
    subscribed_at = datetime.now(timezone.utc)

    subscription = Subscription(
        user_id=user.id,
        subscribe=subscription_in.subscribe,
        plan=plan_clean,
        validity=validity_clean,
        subscribed_at=subscribed_at
    )

    db.add(subscription)
    try:
        db.commit()
        db.refresh(subscription)
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database commit error: {str(err)}")

    return subscription


@router.get(
    "/latest",
    response_model=Optional[SubscriptionResponse]
)
def get_latest_subscription(
    email: Optional[str] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    if db is None:
        return None
    query = db.query(Subscription)
    if user_id:
        query = query.filter(Subscription.user_id == user_id)
    elif email:
        user = db.query(User).filter(func.lower(User.email) == email.strip().lower()).first()
        if user:
            query = query.filter(Subscription.user_id == user.id)
    
    sub = query.order_by(Subscription.subscribed_at.desc()).first()
    return sub


@router.get(
    "/all",
    response_model=List[SubscriptionResponse]
)
def get_all_subscriptions(
    db: Session = Depends(get_db)
):
    return db.query(Subscription).order_by(Subscription.subscribed_at.desc()).all()


@router.get("/plans")
def get_public_plans(db: Session = Depends(get_db)):
    """
    Returns live plan configurations directly from SQL database table `plan_configs`.
    """
    from ...models.plan_config import PlanConfig
    from .admin import ensure_plans_seeded
    
    plans = ensure_plans_seeded(db)
    return [
        {
            "id": p.id,
            "key": p.key,
            "title": p.title,
            "icon": p.icon,
            "monthlyPrice": p.monthly_price,
            "yearlyPrice": p.yearly_price,
            "subtitle": p.subtitle,
            "features": p.features or [],
            "buttonText": p.button_text,
            "buttonClass": p.button_class,
            "isPopular": p.is_popular,
            "updatedAt": p.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ") if p.updated_at else None
        }
        for p in plans
    ]