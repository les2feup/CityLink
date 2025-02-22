import time
import asyncio
from ssa.core import SSA
from micropython import const

def __connect_with_retries():
    """! Connect to the broker with a retry mechanism in case of failure
         Time between retries is 2^n seconds, where n is the retry number
         Maximum number of retries is 8
    """
    ssa = SSA()
    _MAX_RETRIES: int = const(8)

    for n_reties in range(_MAX_RETRIES):
        try:
            ssa.__connect(_with_registration=True)
            break
        except Exception as e:
            print(f"[ERROR] Connection failed with {e}")
            time.sleep(abs(2 ** n_reties))

def __run_main_loop():
    """! Start the bare minimum ssa main loop without any user code and wait for incoming firmware updates """
    ssa = SSA()
    try:
        asyncio.run(ssa.__main_loop(_blocking=True))
    except Exception as e:
        print(f"[ERROR] Main loop failed with {e}")

def __registration_bootstrap():
    """! The main entry point for the application when no user code is present. (user/app.py) """
    print("[INFO] Starting registration process.")
    try:
        __connect_with_retries()
        __run_main_loop()
    except Exception as e:
        raise Exception(f"[FATAL] Registration bootstrap failed with {e}")

def __bootstrap():
    """!
    The main entry point for the application when no user code is present. (user/app.py)

    This function will create an instance of the SSA class, try to connect to the broker
    and post a registration message to the broker.

    If the registration process is successful and user code is downloaded to the device
    (to user/app.py), a soft reset will then be performed with the user code being executed
    as the main entry point.
    """
    try:
        import user.app as app
        print("[INFO] User code found. Starting application.")
        app.init()
    except ImportError as e:
        print(f"[WARNING] No user code found: {e}")
        __registration_bootstrap()
    except Exception as e:
        print(f"[ERROR] Failed to start user code: {e}")
    finally:
        print(f"[FATAL] [UNREACHABLE] Reached end of bootstrap. Exiting.")

__all__ = []
if __name__ == "__main__":
    __bootstrap()
