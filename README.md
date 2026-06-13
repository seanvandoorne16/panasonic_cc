# Panasonic Comfort Cloud - HomeAssistant Component

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)

> **This is a community fork of [sockless-coding/panasonic_cc](https://github.com/sockless-coding/panasonic_cc)** with fixes for broken authentication, updated library versions, and expanded Aquarea heat pump support.

## What's fixed / added in this fork

### Authentication
- **MFA/2FA fully working** — the integration now handles the two-step OTP flow correctly
- Fixed crash on wrong password (`LoginError` / `ResponseError` now show a proper error in the form instead of aborting)
- Fixed `OptionsFlow` crash on newer Home Assistant versions

### Aquarea heat pump (aioaquarea 1.0.7)
- Updated to `aioaquarea==1.0.7` which uses the new Panasonic endpoint (`accsmart.panasonic.com` — the old `aquarea-smart.panasonic.com` is dead)
- Fixed breaking API changes: `device_name`, `firmware_version`, `get_devices()`
- **Fixed zone temperature control** — the slider now works correctly regardless of device/zone power state

#### New Aquarea entities
**Sensors**
- Outside temperature
- Current action (heating / cooling / idle)
- Pump duty (%)
- Zone temperatures (one per zone, e.g. Vloer, Radiator)
- Tank temperature + tank target temperature
- Heating energy today (kWh)
- Hot water energy today (kWh)
- Total energy today (kWh)

**Diagnostic sensors**
- Operation status (ON / OFF / UNKNOWN)
- Device mode (NORMAL / DEFROST)
- Error code + error message
- Force hot water status
- Force heater status

**Climate entities** (one per zone)
- On / Off
- Temperature target (where supported by zone)
- HVAC mode (heat / cool / heat_cool)

**Buttons**
- Force Hot Water
- Force Heater
- Request Defrost

**Select**
- Quiet Mode (off / level 1 / level 2 / level 3)

---

## Installation via HACS (manual repository)

1. In HACS → go to **Integrations** → 3-dot menu → **Custom repositories**
2. Add `https://github.com/seanvandoorne16/panasonic_cc` as type **Integration**
3. Download the integration and restart Home Assistant
4. Add the integration via **Settings → Integrations → Add Integration → Panasonic Comfort Cloud**

## Configuration

Enter your Panasonic ID and password. If your account has 2FA enabled, you will be prompted for the OTP code.

Options available after setup:
- Enable/disable daily energy sensor
- Force enable Nanoe
- Use Panasonic preset names
- Device fetch interval (default: 120 seconds)
- Energy fetch interval (default: 300 seconds)

## Original features (Panasonic CC airconditioners)

* Climate control (on/off, mode, temperature, fan speed, swing)
* Horizontal and vertical swing mode selection
* Inside and outside temperature sensors
* Nanoe / ECONAVI / AI ECO switches (where available)
* Daily energy sensor (optional)
* Current power sensor
* Zone controls (where available)

## Dependencies

- [`aio-panasonic-comfort-cloud==2026.6.1`](https://github.com/sockless-coding/aio-panasonic-comfort-cloud)
- [`aioaquarea==1.0.7`](https://github.com/cjaliaga/aioaquarea)

## Known issues / limitations

- Tank water pressure is not available in the Panasonic API
- Energy sensors may show as unavailable until the first data fetch completes
- Force Heater / Force Hot Water buttons directly control hardware — use with care

[license-shield]: https://img.shields.io/github/license/seanvandoorne16/panasonic_cc.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/seanvandoorne16/panasonic_cc.svg?style=for-the-badge
[releases]: https://github.com/seanvandoorne16/panasonic_cc/releases
