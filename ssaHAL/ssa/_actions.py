import json
import machine
import binascii

from .core import SSA

def firmware_update(_ssa: SSA, update_str):
    print(f"[INFO] Firmware update received with size {len(update_str)}")
    update = json.loads(update_str)

    binary = binascii.a2b_base64(update["base64"])
    expected_crc = int(update["crc32"], 16)
    bin_crc = binascii.crc32(binary)

    if bin_crc != expected_crc:
        print(f"[ERROR] CRC32 mismatch: expected:{hex(expected_crc)}, \
                got {hex(bin_crc)} Firmware update failed.")
        return

    if "user" not in os.listdir():
        os.mkdir("user")

    print("[INFO] Writing firmware to device")
    with open("user/app.py", "w") as f:
        f.write(binary.decode("utf-8"))

    print("[INFO] Firmware write complete. Restarting device.")
    from machine import soft_reset
    soft_reset()

def property_update(ssa: SSA, value, prop):
    try:
        _ = ssa.get_property(prop)
    except Exception as e:
        print(f"[ERROR] Property '{prop}' does not exist.")

    try:
        value = json.loads(value)
        ssa.set_property(prop, value)
    except Exception as e:
        print(f"[ERROR] Failed to set property '{prop}': {e}")
