import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "contact.careequity@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "owfivnqalylwtaao")

def send_otp_email(to_email: str, otp: str) -> bool:
    load_dotenv()
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "contact.careequity@gmail.com")
    smtp_password = os.getenv("SMTP_PASSWORD", "owfivnqalylwtaao").replace(" ", "")

    msg = MIMEMultipart()
    msg['From'] = f"CareEquity <{smtp_user}>"
    msg['To'] = to_email
    msg['Subject'] = "CareEquity - Registration Verification Code"

    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2563eb;">Welcome to CareEquity</h2>
        <p>Please verify your email address to complete your registration.</p>
        <p>Your 6-digit verification code (OTP) is:</p>
        <div style="font-size: 28px; font-weight: bold; color: #2563eb; letter-spacing: 4px; padding: 14px 28px; background-color: #f3f4f6; display: inline-block; border-radius: 8px; margin: 15px 0;">
            {otp}
        </div>
        <p>This code is valid for 10 minutes.</p>
        <p>If you did not request this, you can safely ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;" />
        <p style="font-size: 12px; color: #9ca3af;">CareEquity Health Solutions Inc. &copy; 2026</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(body, 'html'))

    # If the password is a Brevo API Key, bypass SMTP and use the Brevo HTTP API (Port 443)
    if smtp_password.startswith("xkeysib-"):
        import urllib.request
        import json
        
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": smtp_password,
            "content-type": "application/json"
        }
        payload = {
            "sender": {
                "name": "CareEquity",
                "email": smtp_user
            },
            "to": [
                {
                    "email": to_email
                }
            ],
            "subject": "CareEquity - Registration Verification Code",
            "htmlContent": body
        }
        
        try:
            req = urllib.request.Request(
                url, 
                data=json.dumps(payload).encode('utf-8'), 
                headers=headers,
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=10.0) as response:
                res_body = response.read().decode('utf-8')
                print(f"✓ Email sent successfully via Brevo HTTP API: {res_body}")
                return True
        except Exception as e:
            print(f"Failed to send email to {to_email} via Brevo HTTP API: {e}")
            return False

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10.0)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=10.0)
            server.starttls()
            
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_user, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email} via SMTP: {e}")
        return False
