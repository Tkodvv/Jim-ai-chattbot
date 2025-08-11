# roblox_alts.py
import os
import logging
import httpx

logger = logging.getLogger(__name__)

API_KEY  = os.getenv("TRIGEN_API_KEY")
API_BASE = os.getenv("TRIGEN_BASE", "https://trigen.io").rstrip("/")
ENDPOINT = os.getenv("TRIGEN_ALT_ENDPOINT", "/api/alt/generate")

SENSITIVE = {
    "password", "pass", "pwd",
    "token", "roblosecurity", ".roblosecurity", "cookie", "session",
    "otp", "2fa", "auth", "secret", "email"
}

def _sanitize(obj):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            kl = k.lower()
            if kl in SENSITIVE:
                out[k] = "[redacted]"
            else:
                out[k] = _sanitize(v)
        return out
    if isinstance(obj, list):
        return [_sanitize(x) for x in obj]
    return obj

async def generate_owned_alt_public():
    """
    Calls the provider to generate an alt, but only returns safe/public-ish
    fields for display. No credentials are returned.
    """
    if not API_KEY:
        raise RuntimeError("TRIGEN_API_KEY is missing")
    url = f"{API_BASE}{ENDPOINT}"

    headers = {
        "x-api-key": API_KEY,
        "Accept": "application/json",
        "User-Agent": "JimBot/1.0"
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        # provider doesn’t require a body per their curl example
        r = await client.post(url, headers=headers)
        r.raise_for_status()
        raw = r.json()

    data = _sanitize(raw)

    # normalize typical fields (adjust if your JSON differs)
    username     = data.get("username") or data.get("name") or data.get("user")
    display_name = data.get("displayName") or data.get("display_name") or username
    avatar_url   = data.get("avatarUrl")  or data.get("avatar_url")
    bio          = data.get("bio") or ""

    core = {"username","name","user","displayName","display_name","avatarUrl","avatar_url","bio"}
    meta = {k: v for k, v in data.items() if k not in core}

    return {
        "username": username,
        "displayName": display_name,
        "avatarUrl": avatar_url,
        "bio": bio,
        "meta": meta,  # sanitized
    }
