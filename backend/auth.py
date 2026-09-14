"""
backend/auth.py
---------------
Google OAuth 2.0 + JWT session management.

Flow:
  1. Frontend redirects to GET /api/auth/google
  2. User authenticates with Google
  3. Google redirects to GET /api/auth/callback?code=...
  4. Backend exchanges code for tokens, fetches user info
  5. Creates/updates User row, issues a signed JWT
  6. Redirects frontend to /#token=<jwt>
  7. Frontend stores JWT in localStorage and sends it as
     Authorization: Bearer <jwt> on subsequent requests
"""

import os
import json
import time
import hmac
import hashlib
import base64
import urllib.parse
import urllib.request
from typing import Optional
from backend.database import get_db_connection

# ── Config (set via environment variables) ────────────────────────────────────

GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI  = os.environ.get(
    "GOOGLE_REDIRECT_URI",
    "http://127.0.0.1:8000/api/auth/callback"
)
JWT_SECRET           = os.environ.get("JWT_SECRET", "change-me-in-production-use-long-random-string")
JWT_EXPIRE_SECONDS   = int(os.environ.get("JWT_EXPIRE_SECONDS", str(60 * 60 * 24 * 7)))  # 7 days

GOOGLE_AUTH_URL      = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL     = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL  = "https://www.googleapis.com/oauth2/v2/userinfo"

FRONTEND_BASE        = os.environ.get("FRONTEND_BASE", "http://127.0.0.1:5500")

# ── Minimal JWT (no external library dependency) ───────────────────────────────

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * (padding % 4))

def create_jwt(payload: dict) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {**payload, "iat": int(time.time()), "exp": int(time.time()) + JWT_EXPIRE_SECONDS}
    h = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    p = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(JWT_SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{_b64url_encode(sig)}"

def decode_jwt(token: str) -> Optional[dict]:
    try:
        h, p, sig = token.split(".")
        expected_sig = hmac.new(JWT_SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64url_encode(expected_sig).encode(), sig.encode()):
            return None
        payload = json.loads(_b64url_decode(p))
        if payload.get("exp", 0) < time.time():
            return None  # expired
        return payload
    except Exception:
        return None

# ── Google OAuth helpers ───────────────────────────────────────────────────────

def get_google_auth_url() -> str:
    params = {
        "client_id":     GOOGLE_CLIENT_ID,
        "redirect_uri":  GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "online",
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"

def _http_post(url: str, data: dict) -> dict:
    encoded = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=encoded, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())

def _http_get(url: str, token: str) -> dict:
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())

def exchange_code_for_user(code: str) -> dict:
    """Exchange authorization code for Google user info dict."""
    tokens = _http_post(GOOGLE_TOKEN_URL, {
        "code":          code,
        "client_id":     GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri":  GOOGLE_REDIRECT_URI,
        "grant_type":    "authorization_code",
    })
    access_token = tokens.get("access_token")
    if not access_token:
        raise ValueError(f"No access_token in Google response: {tokens}")
    return _http_get(GOOGLE_USERINFO_URL, access_token)

# ── User upsert ───────────────────────────────────────────────────────────────

def upsert_google_user(google_info: dict) -> dict:
    """Insert or update user from Google profile. Returns user dict."""
    google_id  = google_info["id"]
    email      = google_info.get("email", "")
    name       = google_info.get("name", email)
    avatar_url = google_info.get("picture", None)

    conn   = get_db_connection()
    cursor = conn.cursor()

    existing = cursor.execute(
        "SELECT * FROM Users WHERE google_id = ? OR email = ?", (google_id, email)
    ).fetchone()

    if existing:
        cursor.execute("""
            UPDATE Users SET google_id=?, name=?, avatar_url=?, last_login=CURRENT_TIMESTAMP
            WHERE user_id=?
        """, (google_id, name, avatar_url, existing["user_id"]))
        user = dict(existing)
        user.update({"google_id": google_id, "name": name, "avatar_url": avatar_url})
    else:
        cursor.execute("""
            INSERT INTO Users (name, email, google_id, avatar_url, role, last_login)
            VALUES (?, ?, ?, ?, 'user', CURRENT_TIMESTAMP)
        """, (name, email, google_id, avatar_url))
        uid = cursor.lastrowid
        user = {"user_id": uid, "name": name, "email": email,
                "google_id": google_id, "avatar_url": avatar_url, "role": "user"}

    conn.commit()
    conn.close()
    return user

# ── FastAPI dependency ─────────────────────────────────────────────────────────

from fastapi import Header, HTTPException, status

def get_current_user(authorization: str = Header(default="")) -> Optional[dict]:
    """
    Dependency: returns decoded JWT payload or None.
    Returns None for anonymous requests (not logged in).
    """
    if not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    return decode_jwt(token)

def require_user(authorization: str = Header(default="")) -> dict:
    """Dependency: raises 401 if not authenticated."""
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user

def require_admin(authorization: str = Header(default="")) -> dict:
    """Dependency: raises 403 if not admin role."""
    user = require_user(authorization)
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
