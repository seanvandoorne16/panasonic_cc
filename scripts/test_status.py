#!/usr/bin/env python3
"""Test reading device status from Panasonic Comfort Cloud.

Usage:
    pip install aio-panasonic-comfort-cloud aiohttp
    python scripts/test_status.py

    # With 2FA/OTP:
    python scripts/test_status.py --otp 123456

    # Specific device by index (0-based):
    python scripts/test_status.py --device 0

Set credentials in .env or as environment variables:
    PANASONIC_USERNAME=your@email.com
    PANASONIC_PASSWORD=yourpassword
"""
import argparse
import asyncio
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


async def test_status(username: str, password: str, otp_code: str | None = None, device_index: int = 0):
    import aiohttp
    from aio_panasonic_comfort_cloud import ApiClient, MFARequiredError

    print(f"Reading device status for: {username}")
    print("-" * 40)

    async with aiohttp.ClientSession() as session:
        api = ApiClient(username, password, session)
        try:
            await api.start_session(otp_code=otp_code)
        except MFARequiredError:
            print("[!!] 2FA/MFA required! Run with: --otp <code from authenticator app>")
            return False
        except Exception as e:
            print(f"[FAIL] Login failed: {type(e).__name__}: {e}")
            return False

        devices = api.get_devices()
        if not devices:
            print("[FAIL] No devices found")
            return False

        if device_index >= len(devices):
            print(f"[FAIL] Device index {device_index} out of range (have {len(devices)} devices)")
            return False

        device_info = devices[device_index]
        print(f"Reading status of: {device_info.name} (index {device_index})")
        print()

        try:
            device = await api.get_device(device_info)
        except Exception as e:
            print(f"[FAIL] Failed to get device status: {type(e).__name__}: {e}")
            return False

        print(f"[OK] Status for: {device_info.name}")
        print(f"     Power:           {device.parameters.on}")
        print(f"     Operation mode:  {device.parameters.operation_mode}")
        print(f"     Target temp:     {device.parameters.target_temperature}°C")
        print(f"     Inside temp:     {device.parameters.inside_temperature}°C")
        print(f"     Outside temp:    {device.parameters.outside_temperature}°C")
        print(f"     Fan speed:       {device.parameters.fan_speed}")
        print(f"     Eco mode:        {device.parameters.eco_mode}")
        print()
        print(f"     Has Nanoe:       {device.has_nanoe}")
        print(f"     Has Eco Navi:    {device.has_eco_navi}")
        print(f"     Has Eco Func:    {device.has_eco_function}")

        return True


def main():
    parser = argparse.ArgumentParser(description="Test Panasonic CC device status")
    parser.add_argument("--username", default=os.getenv("PANASONIC_USERNAME"))
    parser.add_argument("--password", default=os.getenv("PANASONIC_PASSWORD"))
    parser.add_argument("--otp", default=os.getenv("PANASONIC_OTP"))
    parser.add_argument("--device", type=int, default=0, help="Device index (0-based, default 0)")
    args = parser.parse_args()

    if not args.username or not args.password:
        print("ERROR: Set PANASONIC_USERNAME and PANASONIC_PASSWORD")
        sys.exit(1)

    result = asyncio.run(test_status(args.username, args.password, args.otp, args.device))
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
