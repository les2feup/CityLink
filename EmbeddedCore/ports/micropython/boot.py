from citylink.core import EmbeddedCore, main

try:
    from app import setup

    main(setup)

except ImportError:
    print("No main module found. Proceding with initialization.")
except Exception as e:
    print(f"[Fatal] Uncaught exception in main module: {e}")
    print("Loading default main module...")

try:
    main()
except Exception as e:
    print(f"[Fatal] Uncaught runtime exception: {e}")
    print("Resetting the device...")

from machine import reset

reset()
