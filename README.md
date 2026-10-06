# ZTE Kids Watch — Home Assistant integration

Unofficial Home Assistant integration for **ZTE / nubia "Care" kids smartwatches**
(the app is published as *ZTE Kids* / *ChildrenWatchAbroad*, backend
`care-api.nubia.com`). It logs in with **your own** account and exposes each watch
linked to it as a Home Assistant device — location on the map, battery, steps, and an
on‑demand location refresh.

> This talks to nubia's private app API by replicating the official app's request
> signing. It is **not** affiliated with or endorsed by ZTE/nubia, it uses an
> undocumented API that can change or break at any time, and it is intended only for
> accessing **your own** account and your own children's watches. Use it on accounts
> you control.

## Features

| Entity | Platform | Notes |
|---|---|---|
| Watch location | `device_tracker` | GPS lat/lon + accuracy; shows the child on the HA map. Attributes: `address`, `loc_type`, `loc_time`, `online`. |
| Battery | `sensor` | `%`, device_class `battery`. |
| Steps | `sensor` | Daily step count (`total_increasing`). |
| Last location fix | `sensor` | Timestamp of the most recent GPS fix (diagnostic). |
| Refresh location | `button` | Asks the watch to take a fresh fix, then re‑polls after a few seconds. |

One HA **device per watch**; all entities group under it.

## Requirements

- Home Assistant 2024.x or newer (uses `entry.runtime_data`).
- A working ZTE Kids / ChildrenWatch account (the same login you use in the phone app).
- No extra Python packages — `aiohttp` and `cryptography` ship with HA core.

## Installation (manual)

1. Copy the `zte_kids` folder into your HA config:
   ```
   <config>/custom_components/zte_kids/
   ```
2. Restart Home Assistant.
3. **Settings → Devices & Services → + Add Integration → "ZTE Kids Watch"**.
4. Enter the phone number / email and password for your ZTE Kids account.

Credentials are validated at setup (a real login is attempted) and stored in HA's
encrypted config entry — they are **not** written to any file in this folder.

## How it works

The watches have no public API, so the integration speaks the phone app's own
protocol. Three things were reproduced from the app so HA can authenticate as a
legitimate client **of your own account**:

- **Request signing** — every call carries `sign = SHA‑256( sorted "k=v&…" of the
  params + timestamp + nonce + appKey, with a static app salt appended )`. This is an
  app‑integrity layer, not the login secret.
- **Password encryption** — the login password is AES‑256‑GCM encrypted
  (`IV ‖ ciphertext ‖ tag`, base64) with a static app key before it's sent.
- **Endpoints** — `api/account/login` for the token, then
  `getway/accounts/{openid}/related-device` (list + battery + last location) and
  `getway/devices/{imei}/location/last` (force a fresh fix).

The real authentication is your account's `accesstoken` (valid ~30 days); the
integration caches it and silently re‑logs in before it expires. Bad credentials
trigger HA's reauth flow.

The app key / salt / AES key in `const.py` are the international
(`care-api.nubia.com`) build constants. **If nubia rotates them in a future app
version, login will start failing** — pull the three values again from the newer
APK's `eb/b.java` and update `const.py`.

## Configuration

- **Poll interval** — `DEFAULT_SCAN_INTERVAL` in `const.py` (default `180` s). These
  watches don't report much faster than ~1–2 minutes; don't set it aggressively low.

## Files

```
zte_kids/
  __init__.py          setup / unload, platform list
  manifest.json        integration manifest
  const.py             domain, poll interval, API constants
  api.py               async client: login, signing, AES‑GCM, endpoints
  coordinator.py       DataUpdateCoordinator (polls, caches token)
  config_flow.py       UI login form
  device_tracker.py    map location per watch
  sensor.py            battery / steps / last‑fix
  button.py            on‑demand location refresh
  strings.json         UI strings
  translations/en.json
```

## Troubleshooting

- **0 entities after setup** — the first poll returned no watches. Enable debug logs:
  ```yaml
  logger:
    logs:
      custom_components.zte_kids: debug
  ```
  and check **Settings → System → Logs** (or `<config>/home-assistant.log`).
- **Login fails / reauth loop** — password change on the account, or rotated app
  constants (see *How it works*).
- **Location looks stale** — press **Refresh location**; the watch only reports on its
  own schedule otherwise.

## Disclaimer

Provided as‑is, for personal use with your own account. No warranty. The API is
undocumented and may change without notice.
