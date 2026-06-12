# TODO — panasonic_cc auth fix

## In Progress

- [x] Clone repo
- [x] Analyze repo structure
- [x] Research auth library (aio-panasonic-comfort-cloud)
- [x] Identify root cause of 2FA failure
- [x] Create CLAUDE_STATE.md
- [x] Create TODO.md

## Implementation

- [x] Create docs/ANALYSIS.md
- [x] Create docs/AUTH_OPTIONS.md
- [x] Modify config_flow.py — add async_step_mfa
- [x] Modify config_flow.py — add async_step_reconfigure_mfa
- [x] Modify __init__.py — catch MFARequiredError → ConfigEntryAuthFailed
- [x] Update strings.json — add mfa step
- [x] Update translations/en.json — add mfa step
- [x] Create .env.example
- [x] Create scripts/test_login.py
- [x] Create scripts/test_devices.py
- [x] Create scripts/test_status.py
- [x] Create scripts/test_command.py
- [x] Git commit all changes

## Testing / Validation

- [ ] Install in Home Assistant
- [ ] Verify MFA step appears when 2FA is required
- [ ] Verify OTP code is accepted and login succeeds
- [ ] Verify devices are listed after login
- [ ] Verify token auto-refresh works (no re-auth after first login)
- [ ] Verify reconfigure flow also handles MFA

## Known remaining items

- [ ] Update other translations (cs, de, it, nb, pl, se) with mfa step
- [ ] Optional: add beautifulsoup4 explicitly to requirements if HA doesn't resolve transitive deps
