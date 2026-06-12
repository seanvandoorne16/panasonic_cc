#!/usr/bin/env python3
"""Test sending a command to a Panasonic Comfort Cloud device.

Usage:
    pip install aio-panasonic-comfort-cloud aiohttp
    python scripts/test_command.py --command power_on
    python scripts/test_command.py --command power_off
    python scripts/test_command.py --command set_temp --value 22

    # With 2FA/OTP:
    python scripts/test_command.py --otp 123456 --command power_on

Available commands:
    power_on       Turn device on
    power_off      Turn device off
    set_temp       Set target temperature (requires --value, e.g. --value 22)

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


async def test_command(
    username: str,
    password: str,
    command: str,
    value: str | None = None,
    otp_code: str | None = None,
    device_index: int = 0,
):
    import aiohttp
    from aio_panasonic_comfort_cloud import ApiClient, MFARequiredError
    from aio_panasonic_comfort_cloud import ChangeRequestBuilder

    print(f"Sending command '{command}' for: {username}")
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
        print(f"Getting current state of: {device_info.name}")

        try:
            device = await api.get_device(device_info)
        except Exception as e:
            print(f"[FAIL] Failed to get device: {type(e).__name__}: {e}")
            return False

        builder = ChangeRequestBuilder(device)

        if command == "power_on":
            from aio_panasonic_comfort_cloud.constants import Power
            builder.set_power_mode(Power.On)
            print(f"Turning ON: {device_info.name}")
        elif command == "power_off":
            from aio_panasonic_comfort_cloud.constants import Power
            builder.set_power_mode(Power.Off)
            print(f"Turning OFF: {device_info.name}")
        elif command == "set_temp":
            if value is None:
                print("[FAIL] --value required for set_temp command (e.g. --value 22)")
                return False
            temp = float(value)
            builder.set_target_temperature(temp)
            print(f"Setting temperature to {temp}°C on: {device_info.name}")
        else:
            print(f"[FAIL] Unknown command: {command}")
            print("       Available: power_on, power_off, set_temp")
            return False

        try:
            await api.set_device_raw(device, builder.build())
            print(f"[OK] Command '{command}' sent successfully!")
            return True
        except Exception as e:
            print(f"[FAIL] Command failed: {type(e).__name__}: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Test sending a command to Panasonic CC device")
    parser.add_argument("--username", default=os.getenv("PANASONIC_USERNAME"))
    parser.add_argument("--password", default=os.getenv("PANASONIC_PASSWORD"))
    parser.add_argument("--otp", default=os.getenv("PANASONIC_OTP"))
    parser.add_argument("--device", type=int, default=0, help="Device index (0-based, default 0)")
    parser.add_argument("--command", required=True, choices=["power_on", "power_off", "set_temp"])
    parser.add_argument("--value", help="Value for the command (e.g. temperature)")
    args = parser.parse_args()

    if not args.username or not args.password:
        print("ERROR: Set PANASONIC_USERNAME and PANASONIC_PASSWORD")
        sys.exit(1)

    result = asyncio.run(test_command(
        args.username, args.password, args.command,
        args.value, args.otp, args.device
    ))
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
