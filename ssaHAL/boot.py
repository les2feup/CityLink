from ssa import ssa_main

@ssa_main()
def default(ssa):
    pass

try:
    from user.app import app
    print("[INFO] User app loaded.")
    app.main()
except ImportError:
    print("[INFO] No user app found. Loading default app.")
    default()
