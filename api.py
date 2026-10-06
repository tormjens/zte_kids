"""Async client for the nubia 'care' (ZTE Kids) API.

Replicates the Android app's request signing + AES-GCM password encryption so the
integration can authenticate and poll the user's OWN account. Protocol details were
read from the decompiled com.nubia.care v2.7.7.A:
  - SecurityGuardRequestFilter  -> the 'sign' scheme
  - nb/f.java (nb.f.a)          -> AES/GCM password encryption
  - eb/b.java                   -> the .com key material
  - p4/a.java, l4/a.java        -> endpoints
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import time
import uuid

import aiohttp
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .const import AES_KEY, APP_KEY, APP_SALT, BASE, USER_AGENT


class ZteKidsAuthError(Exception):
    """Login rejected (bad credentials)."""


class ZteKidsApiError(Exception):
    """Any other API/transport failure."""


def _android_b64(raw: bytes) -> str:
    """Mirror android.util.Base64.encodeToString(x, 0) (DEFAULT): wrap 76 + trailing \\n.

    The encrypted password string is signed verbatim, so this must match the app byte-for-byte.
    """
    return base64.encodebytes(raw).decode("ascii")


def _encrypt_password(plain: str) -> str:
    """nb.f.a(): AES/GCM/NoPadding, random 12-byte IV, out = IV || ct || tag, then base64."""
    iv = os.urandom(12)
    ct = AESGCM(AES_KEY).encrypt(iv, plain.encode(), None)  # ct includes the 16-byte GCM tag
    return _android_b64(iv + ct)


def _sign(params: dict) -> dict:
    """SecurityGuardRequestFilter: sorted 'k=v&' of params + timestamp + nonce + appKey,
    append salt, SHA-256 hex. 'sign' is not part of the preimage."""
    p = dict(params)
    p["timestamp"] = str(int(time.time() * 1000))
    p["nonce"] = str(uuid.uuid4())
    p["appKey"] = APP_KEY
    preimage = "".join(f"{k}={p[k]}&" for k in sorted(p)) + APP_SALT
    p["sign"] = hashlib.sha256(preimage.encode("utf-8")).hexdigest()
    return p


class ZteKidsClient:
    """Minimal async client. Holds the session token and re-logs in when it expires."""

    def __init__(self, session: aiohttp.ClientSession, login_name: str, password: str) -> None:
        self._session = session
        self._login_name = login_name
        self._password = password
        self._openid: str | None = None
        self._accesstoken: str | None = None
        self._expires_at: float = 0.0

    async def async_login(self) -> None:
        body = {
            "loginName": self._login_name,
            "password": _encrypt_password(self._password),
            "dypwdFlag": "N",
            "mobileType": "HomeAssistant;integration;Android;13",
        }
        signed = _sign(dict(body))
        qs = {k: signed[k] for k in ("sign", "timestamp", "nonce", "appKey")}
        try:
            async with self._session.post(
                BASE + "api/account/login",
                params=qs,
                data=json.dumps(body),  # send the exact bytes that were signed
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": USER_AGENT,
                },
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                payload = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise ZteKidsApiError(f"login transport error: {err}") from err

        data = payload.get("data")
        if not data or not data.get("accesstoken"):
            raise ZteKidsAuthError(payload.get("msg") or "login failed (no token returned)")
        self._openid = data["openid"]
        self._accesstoken = data["accesstoken"]
        # token_expire_time is seconds-to-live; refresh a day early to be safe.
        ttl = int(data.get("token_expire_time") or 0)
        self._expires_at = time.time() + max(ttl - 86400, 0)

    async def _ensure_token(self) -> None:
        if not self._accesstoken or time.time() >= self._expires_at:
            await self.async_login()

    async def _signed_get(self, path: str, extra: dict | None = None) -> dict:
        await self._ensure_token()
        params = {
            "openid": self._openid,
            "token": self._accesstoken,
            "accesstoken": self._accesstoken,
            **(extra or {}),
        }
        signed = _sign(params)
        try:
            async with self._session.get(
                BASE + path,
                params=signed,
                headers={"Accept": "*/*", "User-Agent": USER_AGENT},
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                return await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise ZteKidsApiError(f"GET {path} failed: {err}") from err

    async def async_get_watches(self) -> list[dict]:
        """Return a flat, HA-friendly state dict per watch (battery + GPS + name)."""
        await self._ensure_token()  # must populate openid BEFORE building the path
        rd = await self._signed_get(
            f"getway/accounts/{self._openid}/related-device"
        )
        watches = (rd.get("ownedDevices") or []) + (rd.get("chatGroupDevices") or [])
        out: list[dict] = []
        for w in watches:
            loc = w.get("lastLocation") or {}
            out.append(
                {
                    "imei": w.get("imei"),
                    "name": w.get("name"),
                    "model": w.get("model"),
                    "online": bool(w.get("onlineStatus")),
                    "battery": (w.get("battery") or {}).get("percent"),
                    "lat": loc.get("lat"),
                    "lon": loc.get("lon"),
                    "address": loc.get("address") or None,
                    "accuracy": _to_float(loc.get("radius")),
                    "loc_type": loc.get("loc_type"),
                    "loc_time": loc.get("timestamp"),  # epoch seconds
                    "step_num": w.get("step_num"),
                }
            )
        return out

    async def async_request_location(self, imei: str) -> dict:
        """POST getway/devices/{imei}/location/last (form-encoded): ask the watch to take a
        fresh fix. Does NOT return a location; poll async_get_watches() a few seconds later."""
        await self._ensure_token()
        body = {
            "imei": imei,
            "openid": self._openid,
            "accesstoken": self._accesstoken,
        }
        signed = _sign(dict(body))
        qs = {k: signed[k] for k in ("sign", "timestamp", "nonce", "appKey")}
        try:
            async with self._session.post(
                BASE + f"getway/devices/{imei}/location/last",
                params=qs,
                data=body,
                headers={"Accept": "application/json", "User-Agent": USER_AGENT},
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                return await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise ZteKidsApiError(f"location refresh failed: {err}") from err

    async def async_validate(self) -> None:
        """Used by the config flow: just try to log in."""
        await self.async_login()


def _to_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
