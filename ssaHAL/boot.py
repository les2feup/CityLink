from ssa import ssa_main

@ssa_main()
def main(ssa):
    """
    Default entry point when no user application is found.
    
    This function serves as a fallback bootstrap for the system when a user-defined
    application module cannot be imported. The SSA parameter, provided by the framework,
    may be used to integrate additional services, though it is not utilized in this
    placeholder implementation.
    """
    pass

try:
    import user.app as app
    print("[INFO] User app loaded.")
    app.main()
except ImportError:
    print("[INFO] No user app found. Loading default app.")
    main()
