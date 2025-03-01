from ssa import ssa_main

@ssa_main()
def main(ssa):
    pass

try:
    import user.app as app
    print("[INFO] User app loaded.")
    app.main()
except ImportError:
    print("[INFO] No user app found. Loading default app.")
    main()
