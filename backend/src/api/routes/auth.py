from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import random

from ...core.database import get_db
from ...models.user import User
from ...models.audit_log import AuditLog
from ...schemas.user import UserCreate, UserLogin, UserResponse, OTPVerify, UserLogout
from ...core.security import get_password_hash, verify_password
from ...core.email import send_otp_email

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

# In-memory dictionary to hold pending signups
# Key: email string
# Value: dict containing name, email, password, otp, and expires_at
pending_registrations = {}

@router.post("/register")
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    # 1. Enforce password minimum length of 6 characters
    if len(user_in.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters."
        )

    # 2. Check if email already exists in DB
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered."
        )

    # 3. Generate 6-digit OTP code
    otp = f"{random.randint(100000, 999999)}"
    print(f"--- GENERATED OTP FOR {user_in.email}: {otp} ---")
    
    # 4. Store details in memory (valid for 10 minutes)
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    pending_registrations[user_in.email] = {
        "name": user_in.name,
        "email": user_in.email,
        "password": user_in.password,
        "otp": otp,
        "expires_at": expires_at
    }

    # 5. Send OTP mail via SMTP
    sent = send_otp_email(user_in.email, otp)
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP verification email. Please check your email settings."
        )

    return {
        "status": "otp_sent",
        "email": user_in.email,
        "otp": otp,
        "message": "OTP verification email sent successfully."
    }

@router.post("/verify-otp", response_model=UserResponse)
def verify_otp(verify_in: OTPVerify, db: Session = Depends(get_db)):
    # 1. Retrieve pending registration
    email = verify_in.email
    pending = pending_registrations.get(email)
    
    if not pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No registration request found or OTP expired. Please register again."
        )

    # 2. Validate expiration
    if datetime.utcnow() > pending["expires_at"]:
        pending_registrations.pop(email, None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please register again."
        )

    # 3. Validate OTP code
    if pending["otp"] != verify_in.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code. Please check your email."
        )

    # 4. Success! Save user to PostgreSQL database
    db_user = User(
        name=pending["name"],
        email=pending["email"],
        hashed_password=get_password_hash(pending["password"]),
        status=True,
        last_login=datetime.utcnow()
    )
    db.add(db_user)

    # Log successful registration
    db_log = AuditLog(
        event="User Registration Success",
        user=db_user.email,
        ip_address="127.0.0.1",
        category="auth",
        status="success"
    )
    db.add(db_log)

    db.commit()
    db.refresh(db_user)

    # 5. Clean up pending registry
    pending_registrations.pop(email, None)
    
    return db_user

@router.post("/login", response_model=UserResponse)
def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
    # 1. Find user by email
    db_user = db.query(User).filter(User.email == credentials.email).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No credentials found. Please register."
        )

    # 2. Verify password
    if not verify_password(credentials.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password. Please try again."
        )

    # 3. Update status and last login timestamp
    db_user.status = True
    db_user.last_login = datetime.utcnow()
    
    # Log successful login
    db_log = AuditLog(
        event="User Login Success",
        user=db_user.email,
        ip_address="127.0.0.1",
        category="auth",
        status="success"
    )
    db.add(db_log)

    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/logout")
def logout_user(payload: Optional[UserLogout] = None, db: Session = Depends(get_db)):
    from sqlalchemy import func
    if payload and payload.email:
        clean_email = payload.email.strip().lower()
        db_user = db.query(User).filter(func.lower(User.email) == clean_email).first()
        if db_user:
            db_user.status = False
            db_log = AuditLog(
                event="User Logout",
                user=db_user.email,
                ip_address="127.0.0.1",
                category="auth",
                status="success"
            )
            db.add(db_log)
            db.commit()
    return {"status": "success", "message": "Logged out successfully"}
