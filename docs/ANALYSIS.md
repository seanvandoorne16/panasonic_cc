# Project Analysis — panasonic_cc

## Overview

This is a **Home Assistant custom integration (HACS)** for Panasonic Comfort Cloud.
It allows control and monitoring of Panasonic AC units and Aquarea heat pumps through the Panasonic cloud API.

## Repository Structure

```
panasonic_cc/
├── custom_components/panasonic_cc/   # HA integration code
│   ├── __init__.py                   # Setup entry point
│   ├── config_flow.py                # HA config UI flow
│   ├── coordinator.py                # DataUpdateCoordinator wrappers
│   ├── climate.py                    # Climate entity
│   ├── sensor.py                     # Temperature/energy sensors
│   ├── switch.py                     # Switches (Nanoe, etc.)
│   ├── select.py                     # Swing mode selects
│   ├── number.py                     # Number entities
│   ├── button.py                     # Button entities
│   ├── water_heater.py               # Aquarea water heater entity
│   ├── base.py                       # Base entity class
│   ├── const.py                      # Constants
│   ├── manifest.json                 # Integration metadata + requirements
│   ├── strings.json                  # UI strings
│   └── translations/                 # Translated strings
├── docs/                             # Documentation
├── scripts/                          # Standalone test scripts
├── .env.example                      # Credentials template
└── requirements.txt                  # Python deps (for standalone use)
```

## Language & Technology

- **Language**: Python 3.11+
- **Framework**: Home Assistant (custom integration)
- **API**: Panasonic Comfort Cloud cloud API (REST/OAuth2)
- **Key dependencies**:
  - `aio-panasonic-comfort-cloud==2025.5.1` — async API client
  - `aioaquarea==0.7.2` — Aquarea (heat pump) client
  - `aiohttp` — HTTP client (provided by HA)

## Authentication Flow

### Library: aio-panasonic-comfort-cloud

The library uses **OAuth2 PKCE** flow via Auth0 (Panasonic's identity provider):

```
1. GET /authorize  (PKCE challenge)
2. GET /authorize redirect  (get CSRF token)
3. POST /usernamepassword/login  (submit credentials)
   → If 2FA enabled: response contains mfa_token → raises MFARequiredError
   → If no 2FA: response contains hidden form fields
4. POST /login/callback  (form submission)
5. GET redirect  (follow to get authorization code)
6. POST /oauth/token  (exchange code + verifier for access/refresh tokens)
7. POST /auth/v2/login  (get Panasonic clientId)
```

### Token Storage

Tokens stored in `~/.panasonic-settings` (JSON file):
- `access_token` — short-lived (typically 1 hour)
- `refresh_token` — long-lived (weeks/months)
- `expires_in` — Unix timestamp of expiry

### Token Refresh

`PanasonicSession._ensure_valid_token()` is called before every API request.
If access token expired: automatically calls `refresh_token()` using the stored refresh token.
Full re-auth only needed if refresh token also expires.

## Authentication Problems Found

### Problem 1: MFARequiredError not handled in config_flow.py

When 2FA is enabled on the Panasonic account:
- `api.start_session()` raises `MFARequiredError`
- Old `config_flow.py` catches it as a generic exception → aborts with "device_fail"
- User sees generic error, no way to enter OTP code

**Fix**: Added `async_step_mfa` to config flow (see config_flow.py changes).

### Problem 2: MFARequiredError not handled in __init__.py

At HA startup, if refresh token expires and 2FA is required for re-auth:
- `api.start_session()` raises `MFARequiredError`
- Old `__init__.py` propagates uncaught
- Integration fails to load

**Fix**: Catch `MFARequiredError` → raise `ConfigEntryAuthFailed` → HA prompts reconfigure.

## Device Communication

All communication goes through Panasonic's cloud API. There is no known LAN-direct API for standard Panasonic AC units (unlike some other brands). The cloud API is the only supported method.

### Polling intervals (configurable)
- Device status: 120 seconds (default)
- Energy data: 300 seconds (default)

## Aquarea (Heat Pump) Integration

Aquarea devices are handled separately via `aioaquarea` library.
They appear as "unknown devices" in the CC API, then looked up via the Aquarea API.
Uses same Panasonic credentials.
