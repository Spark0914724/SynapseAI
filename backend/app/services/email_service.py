"""
Email service — sends transactional emails.
Uses SMTP directly for simplicity; swap for SendGrid/Resend in production.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


def _send(to: str, subject: str, html: str) -> None:
    """Send an email via SMTP. Silently skips if SMTP is not configured."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        # Dev mode — just print to console
        print(f"\n[EMAIL] To: {to}\nSubject: {subject}\n{html}\n")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
    msg["To"] = to
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAILS_FROM_EMAIL, to, msg.as_string())


def send_verification_email(to: str, token: str) -> None:
    verify_url = f"http://localhost:5173/verify-email/{token}"
    html = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
      <h2 style="color: #7c3aed;">Verify your SynapseAI account</h2>
      <p>Click the button below to verify your email address.</p>
      <a href="{verify_url}"
         style="display:inline-block;background:#7c3aed;color:#fff;padding:12px 24px;
                border-radius:8px;text-decoration:none;font-weight:600;margin:16px 0;">
        Verify Email
      </a>
      <p style="color:#6b7280;font-size:13px;">
        This link expires in 24 hours. If you didn't create an account, ignore this email.
      </p>
    </div>
    """
    _send(to, "Verify your SynapseAI email", html)


def send_password_reset_email(to: str, token: str) -> None:
    reset_url = f"http://localhost:5173/reset-password/{token}"
    html = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
      <h2 style="color: #7c3aed;">Reset your password</h2>
      <p>Click the button below to set a new password for your SynapseAI account.</p>
      <a href="{reset_url}"
         style="display:inline-block;background:#7c3aed;color:#fff;padding:12px 24px;
                border-radius:8px;text-decoration:none;font-weight:600;margin:16px 0;">
        Reset Password
      </a>
      <p style="color:#6b7280;font-size:13px;">
        This link expires in 1 hour. If you didn't request this, ignore this email.
      </p>
    </div>
    """
    _send(to, "Reset your SynapseAI password", html)
