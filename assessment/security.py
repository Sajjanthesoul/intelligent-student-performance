"""Small shared-password gate for the assessment workspace."""
import hmac
import os

def configured_password():
    value = os.getenv("ASSESSMENT_ACCESS_PASSWORD", "").strip()
    if value:
        return value
    try:
        import streamlit as st
        return str(st.secrets.get("ASSESSMENT_ACCESS_PASSWORD", "")).strip()
    except Exception:
        return ""

def password_matches(candidate, expected):
    return bool(expected) and hmac.compare_digest(str(candidate), str(expected))
