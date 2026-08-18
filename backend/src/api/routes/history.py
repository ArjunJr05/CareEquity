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
    # Find user or fallback to first user in database
    user = db.query(User).filter(User.id == history_in.user_id).first()
    if not user:
        user = db.query(User).first()
        if not user:
            # Create a default system user if none exists
            user = User(name="Default User", email="user@careequity.com", hashed_password="defaultpassword", status=True)
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
# GET ALL HISTORY FOR ONE USER
# ---------------------------------------------------------

@router.get(
    "/user/{user_id}",
    response_model=list[AssessmentHistoryResponse]
)
def get_user_history(
    user_id: int,
    db: Session = Depends(get_db)
):
    history = (
        db.query(AssessmentHistory)
        .order_by(
            AssessmentHistory.timestamp.desc()
        )
        .all()
    )
    return history


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