#!/usr/bin/env python3
"""Test listing Panasonic Comfort Cloud devices.

Usage:
    pip install aio-panasonic-comfort-cloud aiohttp
    python scripts/test_devices.py

    # With 2FA/OTP:
    python scripts/test_devices.py --otp 123456

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


async def test_devices(username: str, password: str, otp_code: str | None = None):
    import aiohttp
    from aio_panasonic_comfort_cloud import ApiClient, MFARequiredError

    print(f"Listing devices for: {username}")
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
        print(f"[OK] Found {len(devices)} device(s)")
        print()

        for i, device in enumerate(devices, 1):
            print(f"  Device {i}: {device.name}")
            print(f"    ID:    {device.id}")
            print(f"    Model: {device.model}")
            print()

        if api.has_unknown_devices:
            print("  [!] Unknown devices detected (possibly Aquarea heat pumps)")
            print("      These require the aioaquarea library to access")

        if not devices and not api.has_unknown_devices:
            print("  [!] No devices found. Check your Panasonic app to verify devices are registered.")
            return False

        return True


def main():
    parser = argparse.ArgumentParser(description="Test Panasonic CC device listing")
    parser.add_argument("--username", default=os.getenv("PANASONIC_USERNAME"))
    parser.add_argument("--password", default=os.getenv("PANASONIC_PASSWORD"))
    parser.add_argument("--otp", default=os.getenv("PANASONIC_OTP"))
    args = parser.parse_args()

    if not args.username or not args.password:
        print("ERROR: Set PANASONIC_USERNAME and PANASONIC_PASSWORD")
        sys.exit(1)

    result = asyncio.run(test_devices(args.username, args.password, args.otp))
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
