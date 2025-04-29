from ssa_core import SSACore


@SSACore.App()
def default_main(_): ...


try:
    from main import main

    main()
except ImportError:
    print("No main module found. Proceding with initialization.")
except Exception as e:
    print(f"[Fatal] Uncaught exception in main module: {e}")
    print("Loading default main module...")

try:
    default_main()
except Exception as e:
    print(f"[Fatal] Uncaught runtime exception: {e}")
    print("Resetting the device...")

from machine import reset

reset()
