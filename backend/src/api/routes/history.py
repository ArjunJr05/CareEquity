from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.user import User
from ...models.assessment_history import AssessmentHistory
from ...schemas.assessment_history import (
    AssessmentHistoryCreate,
    AssessmentHistoryResponse
)


router = APIRouter(
    prefix="/history",
    tags=["History"]
)


# ---------------------------------------------------------
# SAVE A NEW ASSESSMENT HISTORY RECORD
# ---------------------------------------------------------

@router.post(
    "/save",
    response_model=AssessmentHistoryResponse,
    status_code=status.HTTP_201_CREATED
)
def save_assessment_history(
    history_in: AssessmentHistoryCreate,
    db: Session = Depends(get_db)
):
    from sqlalchemy import func
    from ...core.security import get_password_hash

    if db is None:
        from datetime import datetime, timezone
        # Return fallback unsaved history object if DB unavailable
        return AssessmentHistoryResponse(
            id=1,
            user_id=1,
            name=history_in.name,
            age=history_in.age,
            gender=history_in.gender,
            diabetes=history_in.diabetes,
            hypertension=history_in.hypertension,
            heart_disease=history_in.heart_disease,
            asthma=history_in.asthma,
            height_cm=history_in.height_cm,
            weight_kg=history_in.weight_kg,
            latitude=history_in.latitude,
            longitude=history_in.longitude,
            zipcode=history_in.zipcode,
            previous_admission=history_in.previous_admission,
            er_visits=history_in.er_visits,
            medication_adherence=history_in.medication_adherence,
            notes=history_in.notes,
            extra_data=history_in.extra_data,
            is_favorite=False,
            timestamp=datetime.now(timezone.utc)
        )

    user = None

    # 1. Try finding user by email if provided
    if history_in.user_email:
        clean_email = history_in.user_email.strip().lower()
        user = db.query(User).filter(func.lower(User.email) == clean_email).first()

    # 2. Try finding user by user_id if provided
    if not user and history_in.user_id:
        user = db.query(User).filter(User.id == history_in.user_id).first()

    # 3. If user not in DB yet but an email was provided, auto-create user record
    if not user and history_in.user_email:
        clean_email = history_in.user_email.strip().lower()
        display_name = clean_email.split("@")[0].capitalize()
        user = User(
            name=display_name,
            email=clean_email,
            hashed_password=get_password_hash("CareEquity2026!"),
            status=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 4. Fallback to first user in database or create default
    if not user:
        user = db.query(User).first()
        if not user:
            user = User(name="Care Navigator", email="doctor@careequity.com", hashed_password=get_password_hash("CareEquity2026!"), status=True)
            db.add(user)
            db.commit()
            db.refresh(user)

    history = AssessmentHistory(
        user_id=user.id,
        name=history_in.name,
        age=history_in.age,
        gender=history_in.gender,
        diabetes=history_in.diabetes,
        hypertension=history_in.hypertension,
        heart_disease=history_in.heart_disease,
        asthma=history_in.asthma,
        height_cm=history_in.height_cm,
        weight_kg=history_in.weight_kg,
        latitude=history_in.latitude,
        longitude=history_in.longitude,
        zipcode=history_in.zipcode,
        previous_admission=history_in.previous_admission,
        er_visits=history_in.er_visits,
        medication_adherence=history_in.medication_adherence,
        notes=history_in.notes,
        extra_data=history_in.extra_data
    )

    db.add(history)
    db.commit()
    db.refresh(history)
    return history


# ---------------------------------------------------------
# GET ALL HISTORY FOR ONE SPECIFIC USER
# ---------------------------------------------------------

@router.get(
    "/user/{user_id}",
    response_model=list[AssessmentHistoryResponse]
)
def get_user_history(
    user_id: int,
    db: Session = Depends(get_db)
):
    if db is None:
        return []
    history = (
        db.query(AssessmentHistory)
        .filter(AssessmentHistory.user_id == user_id)
        .order_by(
            AssessmentHistory.timestamp.desc()
        )
        .all()
    )
    return history


@router.get(
    "/email/{email:path}",
    response_model=list[AssessmentHistoryResponse]
)
def get_history_by_email(
    email: str,
    db: Session = Depends(get_db)
):
    if db is None:
        return []
    from sqlalchemy import func
    clean_email = email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if user:
        history = (
            db.query(AssessmentHistory)
            .filter(AssessmentHistory.user_id == user.id)
            .order_by(AssessmentHistory.timestamp.desc())
            .all()
        )
        return history

    return []


# ---------------------------------------------------------
# TOGGLE FAVORITE STATUS
# ---------------------------------------------------------

@router.put("/{history_id}/favorite")
def toggle_favorite(history_id: int, db: Session = Depends(get_db)):
    item = db.query(AssessmentHistory).filter(AssessmentHistory.id == history_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History record not found")
    
    current_val = getattr(item, 'is_favorite', False)
    if isinstance(current_val, bool):
        new_val = not current_val
    else:
        new_val = True
        
    setattr(item, 'is_favorite', new_val)
    db.commit()
    db.refresh(item)
    return {"id": history_id, "is_favorite": new_val}


# ---------------------------------------------------------
# GET HISTORY FOR REPORT GENERATION
# ---------------------------------------------------------

@router.get(
    "/user/{user_id}/report-data"
)
def get_report_history(
    user_id: int,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    history = (
        db.query(AssessmentHistory)
        .filter(
            AssessmentHistory.user_id == user_id
        )
        .order_by(
            AssessmentHistory.timestamp.asc()
        )
        .all()
    )

    return {
        "user_id": user_id,
        "user_name": user.name,
        "total_records": len(history),
        "history": [
            {
                "id": row.id,
                "user_id": row.user_id,

                "name": row.name,
                "age": row.age,
                "gender": row.gender,

                "diabetes": row.diabetes,
                "hypertension": row.hypertension,
                "heart_disease": row.heart_disease,
                "asthma": row.asthma,

                "height_cm": row.height_cm,
                "weight_kg": row.weight_kg,

                "latitude": row.latitude,
                "longitude": row.longitude,
                "zipcode": row.zipcode,

                "previous_admission": row.previous_admission,
                "er_visits": row.er_visits,
                "medication_adherence": row.medication_adherence,

                "notes": row.notes,
                "extra_data": row.extra_data,

                "timestamp": row.timestamp
            }
            for row in history
        ]
    }