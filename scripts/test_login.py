#!/usr/bin/env python3
"""Test Panasonic Comfort Cloud authentication.

Usage:
    pip install aio-panasonic-comfort-cloud aiohttp
    python scripts/test_login.py

    # With 2FA/OTP:
    python scripts/test_login.py --otp 123456

Set credentials in .env or as environment variables:
    PANASONIC_USERNAME=your@email.com
    PANASONIC_PASSWORD=yourpassword
"""
import argparse
import asyncio
import os
import sys

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not required


async def test_login(username: str, password: str, otp_code: str | None = None):
    import aiohttp
    from aio_panasonic_comfort_cloud import ApiClient, MFARequiredError

    print(f"Testing login for: {username}")
    print(f"OTP code provided: {'yes' if otp_code else 'no'}")
    print("-" * 40)

    async with aiohttp.ClientSession() as session:
        api = ApiClient(username, password, session)
        try:
            await api.start_session(otp_code=otp_code)
            print("[OK] Login successful!")
            print(f"     App version: {api.app_version}")
            return True
        except MFARequiredError:
            print("[!!] 2FA/MFA required!")
            print("     Run again with: --otp <code from your authenticator app>")
            return False
        except Exception as e:
            print(f"[FAIL] Login failed: {type(e).__name__}: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Test Panasonic CC login")
    parser.add_argument("--username", default=os.getenv("PANASONIC_USERNAME"), help="Panasonic ID (email)")
    parser.add_argument("--password", default=os.getenv("PANASONIC_PASSWORD"), help="Panasonic password")
    parser.add_argument("--otp", default=os.getenv("PANASONIC_OTP"), help="OTP code (if 2FA enabled)")
    args = parser.parse_args()

    if not args.username or not args.password:
        print("ERROR: Set PANASONIC_USERNAME and PANASONIC_PASSWORD (env or --username/--password)")
        sys.exit(1)

    result = asyncio.run(test_login(args.username, args.password, args.otp))
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
