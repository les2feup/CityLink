from citylink.core import EmbeddedCore, main

try:
    main()
except Exception as e:
    print(f"[BOOT] CityLink EmbeddedCore failed with error: {e}")

from machine import soft_reset

print("[BOOT] Resetting the device...")
soft_reset()
