import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from database import log_alert

load_dotenv()


def _get_secret(key: str):
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(key)
    except Exception:
        return None


def send_email_alert(student: dict, subject: str, body: str):
    sender = _get_secret("SMTP_EMAIL")
    app_password = _get_secret("SMTP_APP_PASSWORD")
    recipient = student["email"]

    if not sender or not app_password:
        log_alert(student["roll_no"], student["name"], "Email", recipient, body, "Simulated (Add SMTP keys)")
        return True, f"Demo Mode: Email logged for {recipient} (Add SMTP_EMAIL & SMTP_APP_PASSWORD in .env for live send)."

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient
        msg.set_content(body)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, app_password)
            smtp.send_message(msg)

        log_alert(student["roll_no"], student["name"], "Email", recipient, body, "Sent (Live)")
        return True, f"Live Email successfully sent to {recipient}!"
    except Exception as e:
        log_alert(student["roll_no"], student["name"], "Email", recipient, body, f"Failed: {str(e)[:20]}")
        return False, f"Email failed: {e}"


def send_sms_alert(student: dict, body: str):
    sid = _get_secret("TWILIO_ACCOUNT_SID")
    token = _get_secret("TWILIO_AUTH_TOKEN")
    from_phone = _get_secret("TWILIO_PHONE_NUMBER")
    to_phone = student["phone"]

    if not sid or not token or not from_phone:
        log_alert(student["roll_no"], student["name"], "SMS", to_phone, body, "Simulated (Add Twilio keys)")
        return True, f"Demo Mode: SMS logged for {to_phone} (Add Twilio keys in .env for live SMS)."

    try:
        from twilio.rest import Client
        client = Client(sid, token)
        client.messages.create(body=body, from_=from_phone, to=to_phone)
        log_alert(student["roll_no"], student["name"], "SMS", to_phone, body, "Sent (Live)")
        return True, f"Live SMS successfully sent to {to_phone}!"
    except Exception as e:
        log_alert(student["roll_no"], student["name"], "SMS", to_phone, body, f"Failed: {str(e)[:20]}")
        return False, f"SMS failed: {e}"