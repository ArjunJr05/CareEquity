"""
api/routers/email.py
---------------------
GET  /email/status   — SMTP configuration check
POST /email/send     — send a real email to an organisation
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, field_validator

router = APIRouter(prefix="/email", tags=["Email"])


# ── Request / Response models ──────────────────────────────────────────────

class SendEmailRequest(BaseModel):
    to_addr:      str
    subject:      str
    body:         str
    sender_name:  str
    sender_email: str
    reply_to:     str | None = None

    @field_validator("to_addr", "sender_email")
    @classmethod
    def must_contain_at(cls, v: str) -> str:
        v = v.strip()
        if "@" not in v or len(v) < 5:
            raise ValueError(f"'{v}' is not a valid email address")
        return v

    @field_validator("sender_name", "subject", "body")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be empty")
        return v.strip()


class SendEmailResponse(BaseModel):
    success: bool
    message: str
    error:   str = ""


# ── GET /email/status ──────────────────────────────────────────────────────

@router.get("/status", summary="Check SMTP configuration")
def email_status():
    """
    Returns whether SMTP is configured and ready.
    Never exposes the password.
    """
    from email_sender import smtp_status
    return smtp_status()


# ── POST /email/send ───────────────────────────────────────────────────────

@router.post("/send", response_model=SendEmailResponse,
             summary="Send assistance request email to an organisation")
def send_email_endpoint(payload: SendEmailRequest):
    """
    Sends a real SMTP email from the platform to the organisation.

    - Uses Gmail App Password configured in .streamlit/secrets.toml
    - Reply-To is set to the sender's email so the org can reply directly
    - Returns 200 with success=False on delivery errors (not 5xx),
      so the frontend can display the specific error message.
    - Returns 422 on invalid email addresses (Pydantic validation).
    """
    from email_sender import send_email

    result = send_email(
        to_addr      = payload.to_addr,
        subject      = payload.subject,
        body         = payload.body,
        sender_name  = payload.sender_name,
        sender_email = payload.sender_email,
        reply_to     = payload.reply_to or payload.sender_email,
    )

    return SendEmailResponse(
        success = result.success,
        message = result.message,
        error   = result.error,
    )
