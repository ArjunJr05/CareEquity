"""
email_sender.py
---------------
Real SMTP email sender for CareEquity assistance requests.

Configuration (pick ONE method — method 1 is recommended):

METHOD 1 — Streamlit secrets  (.streamlit/secrets.toml)
    [smtp]
    host     = "smtp.gmail.com"
    port     = 587
    username = "your.gmail@gmail.com"
    password = "xxxx xxxx xxxx xxxx"   # Gmail App Password (16 chars)
    from_name = "CareEquity Platform"

METHOD 2 — Environment variables
    SMTP_HOST      (default: smtp.gmail.com)
    SMTP_PORT      (default: 587)
    SMTP_USERNAME  e.g. your.gmail@gmail.com
    SMTP_PASSWORD  Gmail App Password
    SMTP_FROM_NAME (default: CareEquity Platform)

GETTING A GMAIL APP PASSWORD
    1. Go to myaccount.google.com → Security
    2. Enable 2-Step Verification (required)
    3. Search "App passwords" → create one for "Mail / Windows Computer"
    4. Copy the 16-character password (no spaces needed in config)

SUPPORTED SMTP SERVERS
    Gmail   : smtp.gmail.com  port 587  (TLS)  ← default
    Outlook : smtp.office365.com  port 587
    Yahoo   : smtp.mail.yahoo.com  port 587
    Custom  : set SMTP_HOST / SMTP_PORT yourself
"""

import os
import smtplib
import ssl
import logging
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate
from typing import Optional

logger = logging.getLogger(__name__)


# ── Configuration dataclass ────────────────────────────────────────────────

@dataclass
class SMTPConfig:
    host:      str
    port:      int
    username:  str
    password:  str
    from_name: str = "CareEquity Platform"

    @property
    def is_configured(self) -> bool:
        return bool(self.username and self.password
                    and self.username != "your.gmail@gmail.com")


def load_smtp_config() -> SMTPConfig:
    """
    Load SMTP config from Streamlit secrets first, then env vars.
    Returns an SMTPConfig regardless — check .is_configured before sending.
    """
    # ── Try Streamlit secrets ──────────────────────────────────────────────
    try:
        import streamlit as st
        s = st.secrets.get("smtp", {})
        if s.get("username") and s.get("password"):
            return SMTPConfig(
                host      = s.get("host",      "smtp.gmail.com"),
                port      = int(s.get("port",  587)),
                username  = s.get("username",  ""),
                password  = s.get("password",  ""),
                from_name = s.get("from_name", "CareEquity Platform"),
            )
    except Exception:
        pass   # Streamlit not running or no secrets key

    # ── Fall back to environment variables ────────────────────────────────
    return SMTPConfig(
        host      = os.getenv("SMTP_HOST",      "smtp.gmail.com"),
        port      = int(os.getenv("SMTP_PORT",  "587")),
        username  = os.getenv("SMTP_USERNAME",  ""),
        password  = os.getenv("SMTP_PASSWORD",  ""),
        from_name = os.getenv("SMTP_FROM_NAME", "CareEquity Platform"),
    )


# ── Result object ──────────────────────────────────────────────────────────

@dataclass
class SendResult:
    success:  bool
    message:  str          # human-readable status
    error:    str  = ""    # raw exception string on failure


# ── Core sender ────────────────────────────────────────────────────────────

def send_email(
    to_addr:     str,
    subject:     str,
    body:        str,
    sender_name: str,
    sender_email: str,
    reply_to:    Optional[str] = None,
    cfg:         Optional[SMTPConfig] = None,
) -> SendResult:
    """
    Send a plain-text email via SMTP/TLS.

    Parameters
    ----------
    to_addr       : Recipient email address (the NGO)
    subject       : Email subject line
    body          : Plain-text message body
    sender_name   : Display name of the CareEquity user
    sender_email  : Reply-to address of the CareEquity user
    reply_to      : Optional explicit Reply-To header (defaults to sender_email)
    cfg           : SMTPConfig; loaded from secrets/env if not supplied

    Returns
    -------
    SendResult with success=True on delivery, success=False + error on failure
    """
    if cfg is None:
        cfg = load_smtp_config()

    # ── Validate config ────────────────────────────────────────────────────
    if not cfg.is_configured:
        return SendResult(
            success=False,
            message="SMTP not configured.",
            error="SMTP_USERNAME / SMTP_PASSWORD not set. "
                  "Add credentials to .streamlit/secrets.toml or env vars.",
        )

    # ── Validate addresses ─────────────────────────────────────────────────
    to_addr      = (to_addr or "").strip()
    sender_email = (sender_email or "").strip()
    if not to_addr or "@" not in to_addr:
        return SendResult(
            success=False,
            message="No valid recipient email address for this organisation.",
            error=f"Invalid to_addr: {to_addr!r}",
        )
    if not sender_email or "@" not in sender_email:
        return SendResult(
            success=False,
            message="Please enter a valid email address for yourself.",
            error=f"Invalid sender_email: {sender_email!r}",
        )

    # ── Build message ──────────────────────────────────────────────────────
    msg = MIMEMultipart("alternative")
    msg["Date"]    = formatdate(localtime=True)
    msg["Subject"] = subject.strip()
    msg["From"]    = formataddr((cfg.from_name, cfg.username))
    msg["To"]      = to_addr
    msg["Reply-To"] = reply_to or sender_email

    # Plain-text body — prepend sender info
    full_body = (
        f"Message submitted via CareEquity SDoH Platform\n"
        f"From: {sender_name.strip()} <{sender_email}>\n"
        f"{'─' * 50}\n\n"
        f"{body.strip()}\n\n"
        f"{'─' * 50}\n"
        f"Reply directly to: {sender_email}\n"
    )

    # HTML body — nicely formatted version
    html_body = _build_html_body(
        sender_name=sender_name.strip(),
        sender_email=sender_email,
        subject=subject.strip(),
        body=body.strip(),
    )

    msg.attach(MIMEText(full_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html",  "utf-8"))

    # ── Send via SMTP with STARTTLS ────────────────────────────────────────
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(cfg.host, cfg.port, timeout=15) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(cfg.username, cfg.password)
            server.sendmail(cfg.username, [to_addr], msg.as_string())

        logger.info("Email sent to %s via %s", to_addr, cfg.host)
        return SendResult(
            success=True,
            message=f"Email delivered to {to_addr}",
        )

    except smtplib.SMTPAuthenticationError as exc:
        err = str(exc)
        logger.error("SMTP auth failed: %s", err)
        return SendResult(
            success=False,
            message="Authentication failed. Check your App Password in secrets.toml.",
            error=err,
        )
    except smtplib.SMTPRecipientsRefused as exc:
        err = str(exc)
        logger.error("Recipient refused: %s", err)
        return SendResult(
            success=False,
            message=f"The organisation's email address was rejected by the mail server: {to_addr}",
            error=err,
        )
    except smtplib.SMTPException as exc:
        err = str(exc)
        logger.error("SMTP error: %s", err)
        return SendResult(
            success=False,
            message=f"Mail server error: {err}",
            error=err,
        )
    except OSError as exc:
        err = str(exc)
        logger.error("Network/connection error: %s", err)
        return SendResult(
            success=False,
            message="Could not reach the mail server. Check your internet connection.",
            error=err,
        )
    except Exception as exc:
        err = str(exc)
        logger.error("Unexpected send error: %s", err)
        return SendResult(
            success=False,
            message=f"Unexpected error: {err}",
            error=err,
        )


# ── HTML email template ────────────────────────────────────────────────────

def _build_html_body(sender_name: str, sender_email: str,
                     subject: str, body: str) -> str:
    """Return a clean, professional HTML email body."""
    # Convert newlines to <br> for HTML
    body_html = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    body_html = body_html.replace("\n", "<br>")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:#f4f6f9;padding:30px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:10px;
                      box-shadow:0 2px 12px rgba(0,0,0,.08);
                      overflow:hidden;max-width:600px;">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#1a1a2e,#16213e);
                        padding:28px 36px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td>
                    <span style="font-size:22px;font-weight:800;
                                 color:#ffffff;letter-spacing:1px;">
                      🏥 CareEquity
                    </span><br>
                    <span style="font-size:12px;color:#aabbcc;
                                 letter-spacing:.5px;">
                      SDoH Intervention Platform
                    </span>
                  </td>
                  <td align="right">
                    <span style="background:#e74c3c;color:white;
                                 font-size:11px;font-weight:700;
                                 padding:4px 12px;border-radius:20px;">
                      Assistance Request
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Sender info bar -->
          <tr>
            <td style="background:#eef2ff;padding:14px 36px;
                        border-bottom:1px solid #dde3f0;">
              <span style="font-size:13px;color:#555;">
                <strong>From:</strong> {sender_name}
                &nbsp;&lt;<a href="mailto:{sender_email}"
                             style="color:#3498db;text-decoration:none;">
                  {sender_email}</a>&gt;
              </span>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:32px 36px;">
              <p style="font-size:15px;color:#2c3e50;line-height:1.7;
                         margin:0 0 20px;">
                {body_html}
              </p>
            </td>
          </tr>

          <!-- Reply CTA -->
          <tr>
            <td style="padding:0 36px 28px;">
              <table cellpadding="0" cellspacing="0">
                <tr>
                  <td style="background:#3498db;border-radius:6px;">
                    <a href="mailto:{sender_email}?subject=Re: {subject}"
                       style="display:inline-block;padding:12px 24px;
                              color:#ffffff;font-weight:700;font-size:14px;
                              text-decoration:none;">
                      ↩ Reply to {sender_name}
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#f8f9fb;padding:18px 36px;
                        border-top:1px solid #e8ecf0;">
              <p style="font-size:11px;color:#999;margin:0;line-height:1.6;">
                This message was sent via the
                <strong>CareEquity SDoH Intervention Platform</strong>
                on behalf of the sender listed above.<br>
                To reply, use the button above or email
                <a href="mailto:{sender_email}" style="color:#3498db;">
                  {sender_email}
                </a> directly.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


# ── Config status helper (for UI display) ─────────────────────────────────

def smtp_status() -> dict:
    """
    Return a dict describing current SMTP configuration status.
    Safe to call from UI — never exposes the password.

    Returns keys:
        configured  : bool
        provider    : str  e.g. "Gmail (smtp.gmail.com:587)"
        username    : str  e.g. "care@gmail.com"
        message     : str  human-readable status
    """
    cfg = load_smtp_config()
    if cfg.is_configured:
        return {
            "configured": True,
            "provider":   f"{cfg.host}:{cfg.port}",
            "username":   cfg.username,
            "message":    f"SMTP ready — sending as {cfg.username}",
        }
    return {
        "configured": False,
        "provider":   "",
        "username":   "",
        "message":    (
            "SMTP not configured. Add credentials to "
            ".streamlit/secrets.toml to enable real email sending."
        ),
    }
