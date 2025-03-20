from ssa_core import SSACore


@SSACore.SSACoreEntry()
def default_main(_): ...


try:
    from . import main

    main.main()
except ImportError:
    print("No main module found. Running default main.")

try:
    default_main()
except Exception as e:
    print(f"[Fatal] Uncaught runtime exception: {e}")
    print("Resetting the device...")

from machine import reset

reset()
