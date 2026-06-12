# Auth Options Analysis — panasonic_cc

## Problem Statement

Panasonic Comfort Cloud uses OAuth2 + Auth0 with optional 2FA (TOTP via authenticator app).
When 2FA is enabled, the existing integration fails during initial setup and during re-auth.

## Options Investigated

---

### Option 1: Fix the existing OAuth flow to handle 2FA (CHOSEN)

**How it works:**
- The library `aio-panasonic-comfort-cloud` already supports passing `otp_code` to `start_session(otp_code=...)`
- When `otp_code` is provided, the library handles MFA verification internally within `authenticate()`
- We add a second step to the HA config flow that asks for the OTP code

**Implementation:**
1. Try `start_session()` without OTP
2. If `MFARequiredError` → show OTP input form
3. User opens authenticator app, enters current code
4. Call fresh `start_session(otp_code=otp)` — TOTP is time-independent, works with fresh call
5. Token stored in `~/.panasonic-settings`, auto-refreshed thereafter

**Pros:**
- Clean, minimal changes
- No library modifications
- Standard HA config flow pattern
- Tokens auto-refresh → user only enters OTP once (per refresh token lifetime)
- Works with TOTP (authenticator app)

**Cons:**
- Slight timing risk: TOTP window is 30s; user must submit before expiry
- If Panasonic uses SMS OTP (not TOTP), fresh call would request new SMS → old code invalid
  (In practice, Panasonic uses TOTP via authenticator app)

**Status: IMPLEMENTED** ✅

---

### Option 2: Browser-based login (Selenium/Playwright)

**How it works:**
- Launch headless browser
- Navigate to Panasonic login page
- User completes login + 2FA in browser
- Extract cookies/tokens from browser session
- Pass tokens to the API client

**Pros:**
- Handles any 2FA type (SMS, TOTP, email)
- Future-proof against auth flow changes

**Cons:**
- Requires Selenium or Playwright (huge dependency for HA custom component)
- Complex to integrate with HA config flow
- Brittle (web scraping)
- Security concerns (browser automation)
- Not feasible for standard HA deployment

**Status: Not implemented** ❌

---

### Option 3: Local LAN API

**How it works:**
- Discover Panasonic AC devices on local network
- Communicate directly via LAN protocol (HTTP, MQTT, UDP)
- No cloud authentication needed

**Investigation results:**
- Standard Panasonic Comfort Cloud AC units do NOT expose a LAN API
- Unlike Daikin (BRP069), Mitsubishi, or Fujitsu, Panasonic CC uses cloud-only communication
- Some Panasonic models support WiMAC or other proprietary protocols, but these are not documented
- Panasonic Aquarea (heat pumps) have local Modbus RS-485, but not network-accessible on most models
- No mDNS/UDP discovery found for standard Panasonic AC units

**Status: Not viable** ❌

---

### Option 4: Mirror Home Assistant official integration approach

**Investigation:**
- HA does not have an official Panasonic Comfort Cloud integration
- This custom component IS the de-facto standard HA integration
- The upstream (sockless-coding/panasonic_cc) uses the same library approach
- No other approach exists in the HA ecosystem

**Status: Already doing the best available approach** ℹ️

---

## Token Lifecycle

```
Initial setup:
  username + password + OTP (if 2FA) → access_token + refresh_token
  → stored in ~/.panasonic-settings

Normal operation:
  access_token (valid ~1 hour)
  → auto-refreshed using refresh_token (valid weeks/months)
  → NO re-login needed during normal operation

Token expiry:
  refresh_token expires → need full re-auth
  → HA shows "Reconfigure" prompt (via ConfigEntryAuthFailed)
  → User enters credentials + OTP (if 2FA enabled)
  → New tokens stored
```

## Security Notes

- Credentials stored in HA config entry (HA-encrypted storage)
- Tokens stored in `~/.panasonic-settings` (accessible to HA process)
- No credentials hardcoded anywhere
- `.env` excluded from git via `.gitignore`
- Only your own Panasonic account is accessed — no shared credentials
