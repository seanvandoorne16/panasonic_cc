# CLAUDE_STATE.md — Persistent Session Memory

## Status: COMMITTED — READY FOR HA TESTING

---

## What this project is

A Home Assistant custom component (HACS) for Panasonic Comfort Cloud (AC + Aquarea heat pump).
- Repo: https://github.com/seanvandoorne16/panasonic_cc (fork of sockless-coding/panasonic_cc)
- Language: Python
- HA integration, not a standalone app
- Depends on: `aio-panasonic-comfort-cloud==2026.6.1`, `aioaquarea==0.7.2`

---

## Root Cause of Auth Problem

Panasonic requires 2FA/MFA on login (TOTP via authenticator app).

The library `aio_panasonic_comfort_cloud` DOES support MFA:
- `ApiClient.start_session(otp_code=None)` — if otp_code provided, handles MFA inline
- `MFARequiredError` is raised when MFA is needed but no OTP given

**The bug**: `config_flow.py` and `__init__.py` never handle `MFARequiredError`:
- Config flow catches all exceptions and aborts with "device_fail"
- `__init__.py` lets it propagate uncaught
- No OTP input step exists anywhere in the HA config flow

---

## Fix Strategy

### config_flow.py — Add MFA steps

1. When `start_session()` raises `MFARequiredError`:
   - Store username + password in flow state
   - Show new `async_step_mfa()` form asking for OTP code
2. When OTP submitted:
   - Create fresh ApiClient, call `start_session(otp_code=otp)`
   - Library handles: PKCE → login → MFA challenge → verify TOTP → token stored
3. Same pattern added for reconfigure flow (`async_step_reconfigure_mfa`)

### __init__.py — Graceful runtime MFA handling

- Catch `MFARequiredError` from `start_session()` at startup
- Raise `ConfigEntryAuthFailed` → HA automatically prompts user to reconfigure

---

## Files Modified

| File | Change |
|------|--------|
| `custom_components/panasonic_cc/config_flow.py` | Add MFA step, reconfigure MFA step |
| `custom_components/panasonic_cc/__init__.py` | Catch MFARequiredError → ConfigEntryAuthFailed |
| `custom_components/panasonic_cc/strings.json` | Add mfa/reconfigure_mfa step strings |
| `custom_components/panasonic_cc/translations/en.json` | Same |

## Files Created

| File | Purpose |
|------|---------|
| `CLAUDE_STATE.md` | This file |
| `TODO.md` | Task tracking |
| `docs/ANALYSIS.md` | Full project analysis |
| `docs/AUTH_OPTIONS.md` | Auth options research |
| `.env.example` | Credentials template |
| `scripts/test_login.py` | Test auth |
| `scripts/test_devices.py` | Test device listing |
| `scripts/test_status.py` | Test device status |
| `scripts/test_command.py` | Test sending command |

---

## Key Technical Findings

- `MFARequiredError` exported from `aio_panasonic_comfort_cloud` directly
- `ApiClient.start_session(otp_code=str)` — pass OTP, library handles MFA inline
- `PanasonicAuthentication._mfa_token` stores challenge state in object
- Token stored in `~/.panasonic-settings` (JSON file, auto-refreshed)
- Library auto-refreshes access token using refresh_token
- Full re-auth only needed when refresh token expires (weeks/months)

---

## Decisions Made

- **Fresh ApiClient per MFA attempt**: Don't carry auth state across flow steps. Create fresh client in mfa step with otp_code passed directly to `start_session()`. TOTP is time-independent so this works.
- **No library modification**: Library already supports OTP in start_session(). No forking needed.
- **ConfigEntryAuthFailed for runtime**: Standard HA pattern for runtime auth failures.

---

## Open Problems / Risks

- TOTP timing: If user takes >30s between step 1 (password submit) and step 2 (OTP submit), OTP may expire. Acceptable tradeoff - this is the library's design.
- SMS-based OTP: If Panasonic uses SMS (not TOTP), fresh call triggers new SMS. Current Panasonic implementation appears TOTP-based (authenticator app).

---

## Next Actions (if session interrupted)

1. Check git status
2. Read TODO.md
3. Verify all modified files are saved
4. Run `git add` and commit if not done
5. Test by installing in HA and checking config flow shows MFA step

---

## Git State

- Commit 1 (`75e590f`): fix: add 2FA/MFA support to config flow and runtime auth handling
- Commit 2 (`c46c747`): fix: use start_session() in reconfigure flow; bump library to 2026.6.1
- Branch: master, NOT yet pushed to remote (user must authorize push)

## Last Updated

2026-06-12 — Session 2: committed both fixes, verified library attributes
