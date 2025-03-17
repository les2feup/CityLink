try:
    import user.app as app

    print("[INFO] User app loaded.")
    app.main()
except ImportError:
    print("[INFO] No user app found.")
except Exception as e:
    print(f"[FATAL] User app exception: {e}")
    print(f"[INFO] Falling back to default ssa runtime.")

try:
    print("[INFO] Trying to load default ssa runtime.")
    from ssa_modules import DefaultRuntime

    print("[INFO] Default ssa runtime loaded. Launching in Registration mode.")
    from ssa.core import SSA

    ssa = SSA(DefaultRuntime)
    ssa.launch()
except ImportError as e:
    print(f"[FATAL] No default ssa runtime found {e}. Exiting.")
except Exception as e:
    print(f"[FATAL] SSA core exception: {e}")
    print(f"[INFO] Rebooting...")
    from machine import soft_reset

    soft_reset()
